from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


@dataclass
class CapabilityMapping:
    capability: str
    components: list[str]


@dataclass
class ArchitectureInput:
    title: str = "Architecture Design Document"
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    architecture_overview: str = ""
    high_level_solution_summary: str = ""
    capability_matrix: list[CapabilityMapping] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ArchitectureInput":
        matrix = [
            CapabilityMapping(
                capability=str(row.get("capability", "")).strip(),
                components=[str(component).strip() for component in row.get("components", []) if str(component).strip()],
            )
            for row in payload.get("capability_matrix", [])
            if isinstance(row, dict)
        ]
        return cls(
            title=str(payload.get("title") or cls.title),
            functional_requirements=[
                str(item).strip() for item in payload.get("functional_requirements", []) if str(item).strip()
            ],
            non_functional_requirements=[
                str(item).strip() for item in payload.get("non_functional_requirements", []) if str(item).strip()
            ],
            architecture_overview=str(payload.get("architecture_overview", "")).strip(),
            high_level_solution_summary=str(payload.get("high_level_solution_summary", "")).strip(),
            capability_matrix=[row for row in matrix if row.capability],
            assumptions=[str(item).strip() for item in payload.get("assumptions", []) if str(item).strip()],
        )


def _paragraph(text: str) -> str:
    safe = escape(text)
    return (
        "<w:p><w:r><w:rPr><w:sz w:val=\"22\"/></w:rPr>"
        f"<w:t xml:space=\"preserve\">{safe}</w:t></w:r></w:p>"
    )


def _heading(text: str, level: int = 1) -> str:
    style = "Heading1" if level == 1 else "Heading2"
    safe = escape(text)
    return (
        f"<w:p><w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>"
        f"<w:r><w:t>{safe}</w:t></w:r></w:p>"
    )


def _bullet(text: str) -> str:
    safe = escape(text)
    return (
        "<w:p><w:pPr><w:numPr><w:ilvl w:val=\"0\"/><w:numId w:val=\"1\"/>"
        "</w:numPr></w:pPr><w:r><w:t xml:space=\"preserve\">"
        f"{safe}</w:t></w:r></w:p>"
    )


def _table(rows: list[tuple[str, str]]) -> str:
    header = (
        "<w:tr>"
        "<w:tc><w:p><w:r><w:t>Capability</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>Software Components</w:t></w:r></w:p></w:tc>"
        "</w:tr>"
    )
    body = ""
    for capability, components in rows:
        body += (
            "<w:tr>"
            f"<w:tc><w:p><w:r><w:t>{escape(capability)}</w:t></w:r></w:p></w:tc>"
            f"<w:tc><w:p><w:r><w:t>{escape(components)}</w:t></w:r></w:p></w:tc>"
            "</w:tr>"
        )
    return f"<w:tbl>{header}{body}</w:tbl>"


def _derived_assumptions(arch_input: ArchitectureInput) -> list[str]:
    assumptions = list(arch_input.assumptions)
    if not arch_input.functional_requirements:
        assumptions.append("Functional requirements were not provided; placeholder requirements should be validated with stakeholders.")
    if not arch_input.non_functional_requirements:
        assumptions.append("Non-functional requirements were not provided; performance, reliability, and security targets are assumed to be standard enterprise defaults.")
    if not arch_input.architecture_overview:
        assumptions.append("Architecture overview details were not provided; the target architecture is assumed to be cloud-native and modular.")
    if not arch_input.high_level_solution_summary:
        assumptions.append("High-level solution summary was not provided; the solution is assumed to prioritize maintainability and scalability.")
    if not arch_input.capability_matrix:
        assumptions.append("Capability matrix was not provided; mapping to components should be finalized during solution design workshops.")
    return assumptions


def build_document_xml(arch_input: ArchitectureInput) -> str:
    assumptions = _derived_assumptions(arch_input)

    parts = [
        _heading(arch_input.title, level=1),
        _heading("Functional requirements", level=2),
    ]
    parts.extend(_bullet(item) for item in arch_input.functional_requirements or ["To be confirmed"])

    parts.append(_heading("Non-functional requirements", level=2))
    parts.extend(_bullet(item) for item in arch_input.non_functional_requirements or ["To be confirmed"])

    parts.append(_heading("Architecture overview and high-level solution summary", level=2))
    parts.append(
        _paragraph(
            arch_input.architecture_overview
            or "Architecture overview details are pending and should be supplied by the architecture team."
        )
    )
    parts.append(
        _paragraph(
            arch_input.high_level_solution_summary
            or "High-level solution summary is pending and should be supplied by the solution owner."
        )
    )

    parts.append(_heading("Capability matrix", level=2))
    table_rows = [
        (entry.capability, ", ".join(entry.components) if entry.components else "To be confirmed")
        for entry in arch_input.capability_matrix
    ]
    if not table_rows:
        table_rows = [("To be confirmed", "To be confirmed")]
    parts.append(_table(table_rows))

    parts.append(_heading("Assumptions", level=2))
    parts.extend(_bullet(item) for item in assumptions)

    body = "".join(parts)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" "
        "mc:Ignorable=\"w14 wp14\">"
        f"<w:body>{body}<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\"/>"
        "</w:sectPr></w:body></w:document>"
    )


def write_docx(arch_input: ArchitectureInput, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document_xml = build_document_xml(arch_input)
    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
    <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
    <Default Extension=\"xml\" ContentType=\"application/xml\"/>
    <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
    <Override PartName=\"/word/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml\"/>
    <Override PartName=\"/word/numbering.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml\"/>
</Types>"""
    rels = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
    <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>"""
    document_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"></Relationships>"""
    styles_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:styles xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">
  <w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\"><w:name w:val=\"Normal\"/></w:style>
  <w:style w:type=\"paragraph\" w:styleId=\"Heading1\"><w:name w:val=\"heading 1\"/><w:b/><w:sz w:val=\"32\"/></w:style>
  <w:style w:type=\"paragraph\" w:styleId=\"Heading2\"><w:name w:val=\"heading 2\"/><w:b/><w:sz w:val=\"28\"/></w:style>
</w:styles>"""
    numbering_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:numbering xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">
  <w:abstractNum w:abstractNumId=\"0\"><w:lvl w:ilvl=\"0\"><w:numFmt w:val=\"bullet\"/><w:lvlText w:val=\"•\"/></w:lvl></w:abstractNum>
  <w:num w:numId=\"1\"><w:abstractNumId w:val=\"0\"/></w:num>
</w:numbering>"""

    with ZipFile(output_path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/styles.xml", styles_xml)
        docx.writestr("word/numbering.xml", numbering_xml)
        docx.writestr("word/_rels/document.xml.rels", document_rels)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an architecture design document as DOCX.")
    parser.add_argument("input", type=Path, help="Path to input JSON file.")
    parser.add_argument("--output", type=Path, default=Path("output/architecture_design.docx"), help="Output DOCX path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    arch_input = ArchitectureInput.from_dict(payload)
    output = write_docx(arch_input, args.output)
    print(f"Generated document: {output}")


if __name__ == "__main__":
    main()
