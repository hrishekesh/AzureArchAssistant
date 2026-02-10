from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


@dataclass
class CapabilityRow:
    functionality: str
    components: list[str]


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Sequence):
        return len(value) == 0
    return False


def _paragraph(text: str) -> str:
    return (
        "<w:p>"
        "<w:r><w:t xml:space=\"preserve\">"
        f"{escape(text)}"
        "</w:t></w:r>"
        "</w:p>"
    )


def _heading(text: str, level: int = 1) -> str:
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"Heading{level}\"/></w:pPr>"
        "<w:r><w:t>"
        f"{escape(text)}"
        "</w:t></w:r>"
        "</w:p>"
    )


def _bullet(text: str) -> str:
    return _paragraph(f"• {text}")


def _table(rows: Iterable[CapabilityRow]) -> str:
    tbl_rows: list[str] = []

    def cell(content: str) -> str:
        return (
            "<w:tc><w:p><w:r><w:t xml:space=\"preserve\">"
            f"{escape(content)}"
            "</w:t></w:r></w:p></w:tc>"
        )

    # header
    tbl_rows.append(
        "<w:tr>"
        f"{cell('Functionality')}"
        f"{cell('Software Components')}"
        "</w:tr>"
    )

    for row in rows:
        tbl_rows.append(
            "<w:tr>"
            f"{cell(row.functionality)}"
            f"{cell(', '.join(row.components))}"
            "</w:tr>"
        )

    return "<w:tbl>" + "".join(tbl_rows) + "</w:tbl>"


def _normalize_capability_matrix(value: object) -> list[CapabilityRow]:
    if not isinstance(value, list):
        return []

    normalized: list[CapabilityRow] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        functionality = str(item.get("functionality", "")).strip()
        components = item.get("components", [])
        if isinstance(components, str):
            components = [components]
        components = [str(component).strip() for component in components if str(component).strip()]
        if functionality and components:
            normalized.append(CapabilityRow(functionality=functionality, components=components))
    return normalized


def build_document_content(payload: dict) -> str:
    assumptions: list[str] = [str(x) for x in payload.get("assumptions", []) if str(x).strip()]

    if _is_blank(payload.get("functional_requirements")):
        assumptions.append(
            "Functional requirements were incomplete or missing; placeholders were used pending stakeholder confirmation."
        )
    if _is_blank(payload.get("non_functional_requirements")):
        assumptions.append(
            "Non-functional requirements were incomplete or missing; baseline quality attributes were assumed."
        )
    if _is_blank(payload.get("architecture_overview")):
        assumptions.append(
            "Architecture overview was not supplied; a high-level architecture narrative was inferred."
        )
    if _is_blank(payload.get("high_level_solution_summary")):
        assumptions.append(
            "High-level solution summary was not supplied; solution intent was inferred from available inputs."
        )

    unclear_inputs = payload.get("unclear_inputs", [])
    if isinstance(unclear_inputs, list):
        for unclear in unclear_inputs:
            unclear_text = str(unclear).strip()
            if unclear_text:
                assumptions.append(f"Input was unclear and interpreted conservatively: {unclear_text}.")

    functional_requirements = payload.get("functional_requirements") or [
        "TBD – Capture and validate required business workflows."
    ]
    non_functional_requirements = payload.get("non_functional_requirements") or [
        "TBD – Confirm performance, security, availability, and compliance targets."
    ]
    architecture_overview = payload.get("architecture_overview") or (
        "The solution follows a modular architecture with separation between presentation, "
        "application, and integration responsibilities to support maintainability and scalability."
    )
    high_level_solution_summary = payload.get("high_level_solution_summary") or (
        "Deliver an incremental implementation that prioritizes core business capabilities first, "
        "then extends with operational hardening and observability."
    )

    matrix = _normalize_capability_matrix(payload.get("capability_matrix"))
    if not matrix:
        assumptions.append(
            "Capability matrix details were incomplete; representative capability-to-component mappings were assumed."
        )
        matrix = [
            CapabilityRow("Capture requirements", ["Requirements API", "Document Service"]),
            CapabilityRow("Generate architecture document", ["Document Assembler", "Template Engine"]),
            CapabilityRow("Distribute deliverable", ["Storage Adapter", "Download Endpoint"]),
        ]

    parts: list[str] = []
    title = payload.get("project_name", "Architecture Requirements Document")
    parts.append(_heading(str(title), level=1))

    parts.append(_heading("Functional Requirements", level=2))
    for item in functional_requirements:
        parts.append(_bullet(str(item)))

    parts.append(_heading("Non-Functional Requirements", level=2))
    for item in non_functional_requirements:
        parts.append(_bullet(str(item)))

    parts.append(_heading("Architecture Overview", level=2))
    parts.append(_paragraph(str(architecture_overview)))

    parts.append(_heading("High-Level Solution Summary", level=2))
    parts.append(_paragraph(str(high_level_solution_summary)))

    parts.append(_heading("Capability Matrix", level=2))
    parts.append(_table(matrix))

    if assumptions:
        parts.append(_heading("Assumptions", level=2))
        for assumption in assumptions:
            parts.append(_bullet(assumption))

    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        f"<w:document xmlns:w=\"{W_NS}\">"
        "<w:body>"
        + "".join(parts)
        + "<w:sectPr/></w:body></w:document>"
    )


def write_docx(payload: dict, output_path: str | os.PathLike[str]) -> Path:
    document_xml = build_document_content(payload)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    content_types = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
    <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
    <Default Extension=\"xml\" ContentType=\"application/xml\"/>
    <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
</Types>
"""

    rels = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
    <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>
"""

    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)

    return output


def _load_payload(input_file: str | os.PathLike[str]) -> dict:
    with open(input_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble an architecture requirements DOCX document.")
    parser.add_argument("--input", required=True, help="Path to JSON input payload.")
    parser.add_argument("--output", default="dist/architecture-document.docx", help="Output DOCX path.")
    args = parser.parse_args()

    payload = _load_payload(args.input)
    output = write_docx(payload, args.output)
    print(f"Generated document: {output}")


if __name__ == "__main__":
    main()
