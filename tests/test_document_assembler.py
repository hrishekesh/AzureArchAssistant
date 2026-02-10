from pathlib import Path
import zipfile

from document_assembler import ArchitectureInput, assemble_document, write_docx


def test_assumptions_added_when_input_missing():
    payload = ArchitectureInput()
    sections = assemble_document(payload)
    names = [name for name, _ in sections]
    assert "Assumptions" in names


def test_docx_is_created_and_contains_required_sections(tmp_path: Path):
    data = ArchitectureInput(
        functional_requirements=["FR1"],
        non_functional_requirements=["NFR1"],
        architecture_overview="Overview",
        high_level_solution_summary="Summary",
        capability_matrix=[{"capability": "Cap", "component": "Comp", "notes": "Notes"}],
    )
    out = tmp_path / "doc.docx"
    write_docx(data, out)

    assert out.exists()
    with zipfile.ZipFile(out, "r") as docx:
        xml = docx.read("word/document.xml").decode("utf-8")
        assert "Functional Requirements" in xml
        assert "Non-Functional Requirements" in xml
        assert "Architecture Overview &amp; High-Level Solution Summary" in xml
        assert "Capability Matrix" in xml
