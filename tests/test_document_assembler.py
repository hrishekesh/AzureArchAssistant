from pathlib import Path
import zipfile

from document_assembler import ArchitectureDocumentAssembler, DocumentInputs


def test_assemble_includes_required_sections_and_matrix():
    assembler = ArchitectureDocumentAssembler()
    inputs = DocumentInputs(
        title="Target Architecture",
        functional_requirements=["F1", "F2"],
        non_functional_requirements=["N1"],
        architecture_overview="Overview text",
        high_level_solution_summary="Summary text",
        capabilities={"Capability A": ["Component 1", "Component 2"]},
    )

    output = assembler.assemble_markdown(inputs)

    assert "## Functional Requirements" in output
    assert "## Non-Functional Requirements" in output
    assert "## Architecture Overview" in output
    assert "## High-Level Solution Summary" in output
    assert "## Capability Matrix" in output
    assert "| Capability A | Component 1, Component 2 |" in output
    assert "## Assumptions" not in output


def test_assemble_adds_assumptions_for_missing_inputs():
    assembler = ArchitectureDocumentAssembler()
    inputs = DocumentInputs(title="Target Architecture")

    output = assembler.assemble_markdown(inputs)

    assert "## Assumptions" in output
    assert "Functional requirements were not fully provided" in output
    assert "Capability/component mapping was not provided" in output


def test_export_docx_creates_downloadable_docx(tmp_path: Path):
    assembler = ArchitectureDocumentAssembler()
    content = "# Title\n\n## Functional Requirements\n- F1\n"

    output_path = assembler.export_docx(content, tmp_path / "architecture.docx")

    assert output_path.exists()
    with zipfile.ZipFile(output_path) as archive:
        names = set(archive.namelist())
        assert "[Content_Types].xml" in names
        assert "word/document.xml" in names
        document_xml = archive.read("word/document.xml").decode("utf-8")
        assert "Functional Requirements" in document_xml
