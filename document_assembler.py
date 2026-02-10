#!/usr/bin/env python3
"""Build architecture documents from structured inputs and export as DOCX.

This module provides a reusable document assembly pipeline that always renders:
- Functional requirements
- Non-functional requirements
- Architecture overview and high-level solution summary
- Capability matrix mapping functionality to software components
- Assumptions (automatically added when inputs are incomplete)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable
import zipfile
from xml.sax.saxutils import escape


@dataclass
class ArchitectureInput:
    """Structured input payload for document assembly."""

    title: str = "Architecture & Requirements Document"
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    architecture_overview: str = ""
    high_level_solution_summary: str = ""
    capability_matrix: list[dict[str, str]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "ArchitectureInput":
        return cls(
            title=payload.get("title") or cls.title,
            functional_requirements=_normalize_list(payload.get("functional_requirements")),
            non_functional_requirements=_normalize_list(payload.get("non_functional_requirements")),
            architecture_overview=(payload.get("architecture_overview") or "").strip(),
            high_level_solution_summary=(payload.get("high_level_solution_summary") or "").strip(),
            capability_matrix=_normalize_matrix(payload.get("capability_matrix")),
            assumptions=_normalize_list(payload.get("assumptions")),
        )


def _normalize_list(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, Iterable):
        return []
    values: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def _normalize_matrix(raw: object) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    normalized: list[dict[str, str]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        capability = str(row.get("capability") or "").strip()
        component = str(row.get("component") or "").strip()
        notes = str(row.get("notes") or "").strip()
        if capability or component or notes:
            normalized.append(
                {"capability": capability, "component": component, "notes": notes}
            )
    return normalized


def build_assumptions(data: ArchitectureInput) -> list[str]:
    assumptions = list(data.assumptions)
    if not data.functional_requirements:
        assumptions.append(
            "Functional requirements were not explicitly provided and should be validated with business stakeholders."
        )
    if not data.non_functional_requirements:
        assumptions.append(
            "Non-functional requirements were not explicitly provided and should be validated for reliability, scalability, and security targets."
        )
    if not data.architecture_overview:
        assumptions.append(
            "Architecture overview details were not provided; the solution summary is treated as the baseline architecture direction."
        )
    if not data.high_level_solution_summary:
        assumptions.append(
            "High-level solution summary was not provided and should be confirmed before implementation planning."
        )
    if not data.capability_matrix:
        assumptions.append(
            "Capability-to-component mappings were not supplied; a draft matrix has been generated and requires review."
        )
    return assumptions


def build_default_matrix(data: ArchitectureInput) -> list[dict[str, str]]:
    if data.capability_matrix:
        return data.capability_matrix

    matrix: list[dict[str, str]] = []
    if data.functional_requirements:
        for req in data.functional_requirements:
            matrix.append(
                {
                    "capability": req,
                    "component": "TBD Component",
                    "notes": "Component mapping pending architecture review.",
                }
            )
    else:
        matrix.append(
            {
                "capability": "TBD Capability",
                "component": "TBD Component",
                "notes": "Populate after requirements clarification.",
            }
        )
    return matrix


def assemble_document(data: ArchitectureInput) -> list[tuple[str, list[str]]]:
    assumptions = build_assumptions(data)
    capability_matrix = build_default_matrix(data)

    sections: list[tuple[str, list[str]]] = [
        (
            "Functional Requirements",
            data.functional_requirements
            or ["No functional requirements provided in the input payload."],
        ),
        (
            "Non-Functional Requirements",
            data.non_functional_requirements
            or ["No non-functional requirements provided in the input payload."],
        ),
        (
            "Architecture Overview & High-Level Solution Summary",
            [
                data.architecture_overview
                or "No architecture overview provided.",
                data.high_level_solution_summary
                or "No high-level solution summary provided.",
            ],
        ),
    ]

    matrix_lines = [
        f"Capability: {row['capability'] or 'N/A'} | Component: {row['component'] or 'N/A'} | Notes: {row['notes'] or 'N/A'}"
        for row in capability_matrix
    ]
    sections.append(("Capability Matrix", matrix_lines))

    if assumptions:
        sections.append(("Assumptions", assumptions))

    return sections


def _xml_paragraph(text: str) -> str:
    safe = escape(text)
    return (
        "<w:p><w:r><w:t xml:space=\"preserve\">"
        f"{safe}"
        "</w:t></w:r></w:p>"
    )


def write_docx(data: ArchitectureInput, output_path: Path) -> None:
    sections = assemble_document(data)
    body_parts = [_xml_paragraph(data.title), _xml_paragraph(f"Generated: {date.today().isoformat()}")]

    for heading, lines in sections:
        body_parts.append(_xml_paragraph(""))
        body_parts.append(_xml_paragraph(heading))
        for line in lines:
            body_parts.append(_xml_paragraph(f"• {line}"))

    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
  <w:body>
    {''.join(body_parts)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
      <w:cols w:space="708"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble architecture document and export DOCX.")
    parser.add_argument("input", type=Path, help="Path to input JSON")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/architecture_document.docx"),
        help="Output DOCX path",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    data = ArchitectureInput.from_dict(payload)
    write_docx(data, args.output)
    print(f"Generated document: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
