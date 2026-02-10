from pathlib import Path
from zipfile import ZipFile

from azure_arch_assistant.document_assembler import ArchitectureInput, build_document_xml, write_docx


def test_xml_contains_all_required_sections() -> None:
    arch_input = ArchitectureInput(
        functional_requirements=["Users can submit architecture requests."],
        non_functional_requirements=["System should respond within 2 seconds."],
        architecture_overview="Event-driven microservices architecture.",
        high_level_solution_summary="Requests are captured via API and routed to orchestrator.",
    )

    xml = build_document_xml(arch_input)

    assert "Functional requirements" in xml
    assert "Non-functional requirements" in xml
    assert "Architecture overview and high-level solution summary" in xml
    assert "Capability matrix" in xml
    assert "Assumptions" in xml


def test_assumptions_added_when_input_missing() -> None:
    xml = build_document_xml(ArchitectureInput())

    assert "Functional requirements were not provided" in xml
    assert "Non-functional requirements were not provided" in xml
    assert "Architecture overview details were not provided" in xml


def test_write_docx_creates_downloadable_file(tmp_path: Path) -> None:
    output_path = tmp_path / "design.docx"
    arch_input = ArchitectureInput(
        functional_requirements=["FR1"],
        non_functional_requirements=["NFR1"],
        architecture_overview="Overview",
        high_level_solution_summary="Summary",
    )

    write_docx(arch_input, output_path)

    assert output_path.exists()
    with ZipFile(output_path) as archive:
        assert "word/document.xml" in archive.namelist()
        content = archive.read("word/document.xml").decode("utf-8")
        assert "Functional requirements" in content
