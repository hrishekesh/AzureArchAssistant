from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED


@dataclass(frozen=True)
class CapabilityMapping:
    functionality: str
    component: str


@dataclass(frozen=True)
class ProjectInput:
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    architecture_overview: str = ""
    high_level_solution_summary: str = ""
    capability_matrix: list[CapabilityMapping] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AssembledDocument:
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    architecture_overview: str
    high_level_solution_summary: str
    capability_matrix: list[CapabilityMapping]
    assumptions: list[str]


def assemble_document(project_input: ProjectInput) -> AssembledDocument:
    """Build a complete document payload, inferring assumptions where input is incomplete."""

    inferred_assumptions: list[str] = []

    functional = _normalize_list(
        project_input.functional_requirements,
        fallback="Functional requirements were not provided; detailed requirements will be validated during discovery.",
        assumption="Functional requirements input was incomplete.",
        inferred_assumptions=inferred_assumptions,
    )

    non_functional = _normalize_list(
        project_input.non_functional_requirements,
        fallback="Non-functional requirements were not provided; quality attributes will be confirmed with stakeholders.",
        assumption="Non-functional requirements input was incomplete.",
        inferred_assumptions=inferred_assumptions,
    )

    architecture_overview = _normalize_text(
        project_input.architecture_overview,
        fallback=(
            "A target-state architecture was not supplied. A layered cloud-native architecture "
            "on Azure is assumed, with presentation, application, data, and integration concerns separated."
        ),
        assumption="Architecture overview input was unclear.",
        inferred_assumptions=inferred_assumptions,
    )

    solution_summary = _normalize_text(
        project_input.high_level_solution_summary,
        fallback=(
            "The high-level solution summary was not supplied. It is assumed the solution should align with "
            "Azure Well-Architected Framework principles and deliver incremental business value."
        ),
        assumption="High-level solution summary input was unclear.",
        inferred_assumptions=inferred_assumptions,
    )

    capability_matrix = _normalize_capability_matrix(
        project_input.capability_matrix,
        functional,
        inferred_assumptions,
    )

    assumptions = [*project_input.assumptions, *inferred_assumptions]

    return AssembledDocument(
        functional_requirements=functional,
        non_functional_requirements=non_functional,
        architecture_overview=architecture_overview,
        high_level_solution_summary=solution_summary,
        capability_matrix=capability_matrix,
        assumptions=assumptions,
    )


def write_docx(document: AssembledDocument, destination: str | Path) -> Path:
    """Write assembled document content to a DOCX file."""

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    body = []
    body.append(_heading("Architecture Document", level=1))

    body.append(_heading("Functional Requirements", level=2))
    body.extend(_bullet(item) for item in document.functional_requirements)

    body.append(_heading("Non-Functional Requirements", level=2))
    body.extend(_bullet(item) for item in document.non_functional_requirements)

    body.append(_heading("Architecture Overview", level=2))
    body.append(_paragraph(document.architecture_overview))

    body.append(_heading("High-Level Solution Summary", level=2))
    body.append(_paragraph(document.high_level_solution_summary))

    body.append(_heading("Capability Matrix", level=2))
    body.append(
        _table(
            headers=["Functionality", "Software Component"],
            rows=[(mapping.functionality, mapping.component) for mapping in document.capability_matrix],
        )
    )

    if document.assumptions:
        body.append(_heading("Assumptions", level=2))
        body.extend(_bullet(item) for item in document.assumptions)

    document_xml = _build_document_xml("".join(body))

    with ZipFile(destination_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", _document_rels_xml())

    return destination_path


def _normalize_list(
    values: Iterable[str],
    fallback: str,
    assumption: str,
    inferred_assumptions: list[str],
) -> list[str]:
    cleaned = [item.strip() for item in values if item and item.strip()]
    if cleaned:
        return cleaned

    inferred_assumptions.append(assumption)
    return [fallback]


def _normalize_text(
    value: str,
    fallback: str,
    assumption: str,
    inferred_assumptions: list[str],
) -> str:
    if value and value.strip():
        return value.strip()

    inferred_assumptions.append(assumption)
    return fallback


def _normalize_capability_matrix(
    mappings: list[CapabilityMapping],
    functional_requirements: list[str],
    inferred_assumptions: list[str],
) -> list[CapabilityMapping]:
    cleaned: list[CapabilityMapping] = []
    for mapping in mappings:
        if mapping.functionality.strip() and mapping.component.strip():
            cleaned.append(
                CapabilityMapping(
                    functionality=mapping.functionality.strip(),
                    component=mapping.component.strip(),
                )
            )

    if cleaned:
        return cleaned

    inferred_assumptions.append("Capability-to-component mappings were missing and were inferred from functional requirements.")
    return [CapabilityMapping(functionality=req, component="TBD Component") for req in functional_requirements]


def _build_document_xml(content: str) -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">'
        f"<w:body>{content}<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/>"
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        '<w:cols w:space="708"/><w:docGrid w:linePitch="360"/></w:sectPr></w:body></w:document>'
    )


def _heading(text: str, level: int) -> str:
    escaped = escape(text)
    style = "Heading1" if level == 1 else "Heading2"
    return (
        "<w:p><w:pPr>"
        f"<w:pStyle w:val=\"{style}\"/>"
        "</w:pPr><w:r><w:t>"
        f"{escaped}"
        "</w:t></w:r></w:p>"
    )


def _paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"


def _bullet(text: str) -> str:
    return f"<w:p><w:r><w:t>• {escape(text)}</w:t></w:r></w:p>"


def _table(headers: list[str], rows: list[tuple[str, str]]) -> str:
    cells = "".join(_table_cell(header, bold=True) for header in headers)
    header_row = f"<w:tr>{cells}</w:tr>"

    body_rows = []
    for left, right in rows:
        body_rows.append(f"<w:tr>{_table_cell(left)}{_table_cell(right)}</w:tr>")

    return (
        "<w:tbl>"
        "<w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr>"
        "<w:tblGrid><w:gridCol w:w=\"5000\"/><w:gridCol w:w=\"5000\"/></w:tblGrid>"
        f"{header_row}{''.join(body_rows)}"
        "</w:tbl>"
    )


def _table_cell(text: str, bold: bool = False) -> str:
    escaped = escape(text)
    run_pr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return (
        "<w:tc><w:tcPr><w:tcW w:w=\"5000\" w:type=\"dxa\"/></w:tcPr>"
        f"<w:p><w:r>{run_pr}<w:t>{escaped}</w:t></w:r></w:p>"
        "</w:tc>"
    )


def _content_types_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )


def _root_rels_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )


def _document_rels_xml() -> str:
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )
