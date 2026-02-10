from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
import zipfile


@dataclass
class DocumentInputs:
    """Input model for architecture document assembly."""

    title: str
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    architecture_overview: str | None = None
    high_level_solution_summary: str | None = None
    capabilities: dict[str, list[str]] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)


class ArchitectureDocumentAssembler:
    """Assembles architecture documents and exports in downloadable formats."""

    def assemble_markdown(self, data: DocumentInputs) -> str:
        assumptions = list(data.assumptions)

        if not data.functional_requirements:
            assumptions.append(
                "Functional requirements were not fully provided; placeholders were used."
            )
        if not data.non_functional_requirements:
            assumptions.append(
                "Non-functional requirements were not fully provided; placeholders were used."
            )
        if not data.architecture_overview:
            assumptions.append(
                "Architecture overview was not provided; summary placeholder was used."
            )
        if not data.high_level_solution_summary:
            assumptions.append(
                "High-level solution summary was not provided; summary placeholder was used."
            )
        if not data.capabilities:
            assumptions.append(
                "Capability/component mapping was not provided; template matrix was inserted."
            )

        lines: list[str] = [f"# {data.title}", ""]

        lines.extend(self._section("Functional Requirements", data.functional_requirements))
        lines.extend(
            self._section(
                "Non-Functional Requirements", data.non_functional_requirements
            )
        )

        lines.append("## Architecture Overview")
        lines.append(
            data.architecture_overview
            or "Architecture overview pending. Provide system context, boundaries, and major design patterns."
        )
        lines.append("")

        lines.append("## High-Level Solution Summary")
        lines.append(
            data.high_level_solution_summary
            or "High-level solution summary pending. Describe major components, integrations, and delivery scope."
        )
        lines.append("")

        lines.extend(self._capability_matrix(data.capabilities))

        if assumptions:
            lines.append("## Assumptions")
            lines.extend([f"- {item}" for item in assumptions])
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _section(title: str, items: Iterable[str]) -> list[str]:
        lines: list[str] = [f"## {title}"]
        collected = list(items)
        if collected:
            lines.extend(f"- {item}" for item in collected)
        else:
            lines.append("- _To be defined_")
        lines.append("")
        return lines

    @staticmethod
    def _capability_matrix(capabilities: dict[str, list[str]]) -> list[str]:
        lines = ["## Capability Matrix", "| Functionality | Software Components |", "| --- | --- |"]
        if capabilities:
            for functionality, components in capabilities.items():
                component_cell = ", ".join(components) if components else "_To be defined_"
                lines.append(f"| {functionality} | {component_cell} |")
        else:
            lines.append("| _To be defined_ | _To be defined_ |")
        lines.append("")
        return lines

    def export_docx(self, markdown_content: str, output_path: str | Path) -> Path:
        """Export markdown text into a minimal DOCX package."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        paragraphs = [line for line in markdown_content.splitlines() if line.strip()]
        body = "".join(
            f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(line)}</w:t></w:r></w:p>"
            for line in paragraphs
        )

        content_types = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>
  <Override PartName='/docProps/core.xml' ContentType='application/vnd.openxmlformats-package.core-properties+xml'/>
  <Override PartName='/docProps/app.xml' ContentType='application/vnd.openxmlformats-officedocument.extended-properties+xml'/>
</Types>
""".strip()

        rels = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/>
  <Relationship Id='rId2' Type='http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties' Target='docProps/core.xml'/>
  <Relationship Id='rId3' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties' Target='docProps/app.xml'/>
</Relationships>
""".strip()

        document_xml = f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:document xmlns:wpc='http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas'
    xmlns:mc='http://schemas.openxmlformats.org/markup-compatibility/2006'
    xmlns:o='urn:schemas-microsoft-com:office:office'
    xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    xmlns:m='http://schemas.openxmlformats.org/officeDocument/2006/math'
    xmlns:v='urn:schemas-microsoft-com:vml'
    xmlns:wp14='http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing'
    xmlns:wp='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
    xmlns:w10='urn:schemas-microsoft-com:office:word'
    xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    xmlns:w14='http://schemas.microsoft.com/office/word/2010/wordml'
    xmlns:wpg='http://schemas.microsoft.com/office/word/2010/wordprocessingGroup'
    xmlns:wpi='http://schemas.microsoft.com/office/word/2010/wordprocessingInk'
    xmlns:wne='http://schemas.microsoft.com/office/word/2006/wordml'
    xmlns:wps='http://schemas.microsoft.com/office/word/2010/wordprocessingShape'
    mc:Ignorable='w14 wp14'>
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w='12240' w:h='15840'/>
      <w:pgMar w:top='1440' w:right='1440' w:bottom='1440' w:left='1440' w:header='708' w:footer='708' w:gutter='0'/>
    </w:sectPr>
  </w:body>
</w:document>
""".strip()

        timestamp = datetime.now(timezone.utc).isoformat()
        core_xml = f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<cp:coreProperties xmlns:cp='http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
    xmlns:dc='http://purl.org/dc/elements/1.1/'
    xmlns:dcterms='http://purl.org/dc/terms/'
    xmlns:dcmitype='http://purl.org/dc/dcmitype/'
    xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>
  <dc:title>Architecture Document</dc:title>
  <dc:creator>ArchitectureDocumentAssembler</dc:creator>
  <cp:lastModifiedBy>ArchitectureDocumentAssembler</cp:lastModifiedBy>
  <dcterms:created xsi:type='dcterms:W3CDTF'>{timestamp}</dcterms:created>
  <dcterms:modified xsi:type='dcterms:W3CDTF'>{timestamp}</dcterms:modified>
</cp:coreProperties>
""".strip()

        app_xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Properties xmlns='http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
    xmlns:vt='http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'>
  <Application>ArchitectureDocumentAssembler</Application>
</Properties>
""".strip()

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as docx:
            docx.writestr("[Content_Types].xml", content_types)
            docx.writestr("_rels/.rels", rels)
            docx.writestr("word/document.xml", document_xml)
            docx.writestr("docProps/core.xml", core_xml)
            docx.writestr("docProps/app.xml", app_xml)

        return output


if __name__ == "__main__":
    assembler = ArchitectureDocumentAssembler()
    inputs = DocumentInputs(
        title="Architecture Definition",
        functional_requirements=[
            "User authentication and authorization",
            "Document generation with required sections",
        ],
        non_functional_requirements=[
            "Response time under 2 seconds for generation",
            "Auditability of generated artifacts",
        ],
        architecture_overview="The solution uses a modular document assembly service with template-driven output.",
        high_level_solution_summary="Input metadata is normalized, rendered into markdown, and exported as DOCX for download.",
        capabilities={
            "User management": ["Identity Service", "API Gateway"],
            "Document generation": ["Assembly Engine", "DOCX Exporter"],
        },
    )
    markdown = assembler.assemble_markdown(inputs)
    out_file = assembler.export_docx(markdown, "output/architecture_document.docx")
    print(f"Generated {out_file}")
