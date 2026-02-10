"""Document assembly logic for architecture deliverables.

This module builds a structured architecture document with required sections and
exports a downloadable DOCX file without third-party dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


@dataclass(slots=True)
class ArchitectureDocumentInput:
    """Input model used to assemble the architecture document."""

    title: str
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    architecture_overview: str = ""
    high_level_solution_summary: str = ""
    capabilities_to_components: dict[str, list[str]] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssembledDocument:
    """Assembled content sections."""

    title: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    architecture_overview: str
    high_level_solution_summary: str
    capability_matrix_rows: list[tuple[str, str]]
    assumptions: list[str]


class DocumentAssembler:
    """Builds a complete architecture document from possibly incomplete input."""

    def assemble(self, payload: ArchitectureDocumentInput) -> AssembledDocument:
        capability_rows = self._capability_rows(payload.capabilities_to_components)
        assumptions = list(payload.assumptions)

        if not payload.functional_requirements:
            assumptions.append(
                "Functional requirements were not explicitly provided; draft scope validation is required."
            )
        if not payload.non_functional_requirements:
            assumptions.append(
                "Non-functional requirements were not explicitly provided; quality attributes must be confirmed."
            )
        if not payload.architecture_overview.strip():
            assumptions.append(
                "Architecture overview input was incomplete; a provisional baseline architecture is described."
            )
        if not payload.high_level_solution_summary.strip():
            assumptions.append(
                "High-level solution summary input was incomplete; implementation approach should be reviewed."
            )
        if not capability_rows:
            assumptions.append(
                "Capability-to-component mappings were missing; traceability matrix must be finalized with engineering teams."
            )

        return AssembledDocument(
            title=payload.title.strip() or "Architecture Document",
            functional_requirements=payload.functional_requirements
            or ["TBD - Functional requirement details pending stakeholder confirmation."],
            non_functional_requirements=payload.non_functional_requirements
            or ["TBD - Non-functional targets pending architecture governance input."],
            architecture_overview=payload.architecture_overview.strip()
            or "A layered cloud-native architecture is proposed with clear separation of presentation, business services, integration, and data platforms.",
            high_level_solution_summary=payload.high_level_solution_summary.strip()
            or "The solution will be delivered as modular services with API-first contracts, automated CI/CD, and centralized observability.",
            capability_matrix_rows=capability_rows
            or [("TBD Capability", "TBD Component")],
            assumptions=self._deduplicate(assumptions),
        )

    @staticmethod
    def _capability_rows(capability_map: dict[str, list[str]]) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for capability, components in capability_map.items():
            if not components:
                rows.append((capability, "TBD Component"))
                continue
            for component in components:
                rows.append((capability, component))
        return rows

    @staticmethod
    def _deduplicate(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result


class DocxExporter:
    """Exports an assembled architecture document into DOCX (Open XML)."""

    CONTENT_TYPES = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
  <Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>
  <Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>
</Types>"""

    RELS = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
  <Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/>
  <Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties\" Target=\"docProps/app.xml\"/>
</Relationships>"""

    @staticmethod
    def _core_xml(title: str) -> str:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:dcmitype=\"http://purl.org/dc/dcmitype/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
  <dc:title>{escape(title)}</dc:title>
  <dc:creator>AzureArchAssistant</dc:creator>
  <cp:lastModifiedBy>AzureArchAssistant</cp:lastModifiedBy>
  <dcterms:created xsi:type=\"dcterms:W3CDTF\">{now}</dcterms:created>
  <dcterms:modified xsi:type=\"dcterms:W3CDTF\">{now}</dcterms:modified>
</cp:coreProperties>"""

    APP_XML = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">
  <Application>AzureArchAssistant</Application>
</Properties>"""

    @staticmethod
    def _paragraph(text: str, bold: bool = False) -> str:
        text_xml = escape(text)
        if bold:
            return f"<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{text_xml}</w:t></w:r></w:p>"
        return f"<w:p><w:r><w:t>{text_xml}</w:t></w:r></w:p>"

    def _document_xml(self, doc: AssembledDocument) -> str:
        parts: list[str] = [
            self._paragraph(doc.title, bold=True),
            self._paragraph("Functional Requirements", bold=True),
        ]
        parts.extend(self._paragraph(f"• {item}") for item in doc.functional_requirements)

        parts.append(self._paragraph("Non-Functional Requirements", bold=True))
        parts.extend(self._paragraph(f"• {item}") for item in doc.non_functional_requirements)

        parts.extend(
            [
                self._paragraph("Architecture Overview", bold=True),
                self._paragraph(doc.architecture_overview),
                self._paragraph("High-Level Solution Summary", bold=True),
                self._paragraph(doc.high_level_solution_summary),
                self._paragraph("Capability Matrix", bold=True),
                self._paragraph("Capability | Software Component", bold=True),
            ]
        )
        parts.extend(self._paragraph(f"{cap} | {comp}") for cap, comp in doc.capability_matrix_rows)

        parts.append(self._paragraph("Assumptions", bold=True))
        parts.extend(self._paragraph(f"• {item}") for item in doc.assumptions)

        body = "".join(parts)
        return f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" xmlns:o=\"urn:schemas-microsoft-com:office:office\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" xmlns:v=\"urn:schemas-microsoft-com:vml\" xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" xmlns:w10=\"urn:schemas-microsoft-com:office:word\" xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" xmlns:wne=\"http://schemas.microsoft.com/office/2006/wordml\" xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" mc:Ignorable=\"w14 wp14\">
  <w:body>{body}<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/><w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/></w:sectPr></w:body>
</w:document>"""

    def export(self, doc: AssembledDocument, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", self.CONTENT_TYPES)
            archive.writestr("_rels/.rels", self.RELS)
            archive.writestr("word/document.xml", self._document_xml(doc))
            archive.writestr("docProps/core.xml", self._core_xml(doc.title))
            archive.writestr("docProps/app.xml", self.APP_XML)

        return output


def assemble_and_export(payload: ArchitectureDocumentInput, output_path: str | Path) -> Path:
    assembled = DocumentAssembler().assemble(payload)
    return DocxExporter().export(assembled, output_path)
