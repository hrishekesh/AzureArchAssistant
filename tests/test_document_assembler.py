from pathlib import Path
from zipfile import ZipFile

from document_assembler import build_document_content, write_docx


def test_build_document_content_includes_required_sections():
    payload = {
        "project_name": "Sample Project",
        "functional_requirements": ["Users can submit requests"],
        "non_functional_requirements": ["99.9% availability"],
        "architecture_overview": "Microservice-based deployment.",
        "high_level_solution_summary": "Use API and worker services.",
        "capability_matrix": [
            {
                "functionality": "Submit requests",
                "components": ["API Gateway", "Request Service"],
            }
        ],
    }

    content = build_document_content(payload)

    assert "Functional Requirements" in content
    assert "Non-Functional Requirements" in content
    assert "Architecture Overview" in content
    assert "High-Level Solution Summary" in content
    assert "Capability Matrix" in content


def test_unclear_input_triggers_assumptions_section():
    payload = {
        "project_name": "Missing Data Project",
        "unclear_inputs": ["Authentication flow unspecified"],
    }

    content = build_document_content(payload)

    assert "Assumptions" in content
    assert "Authentication flow unspecified" in content


def test_write_docx_creates_downloadable_file(tmp_path: Path):
    payload = {
        "project_name": "Downloadable Document",
        "functional_requirements": ["Generate output"],
        "non_functional_requirements": ["Export as DOCX"],
        "architecture_overview": "Simple architecture overview.",
        "high_level_solution_summary": "Simple high-level summary.",
        "capability_matrix": [
            {"functionality": "Generate output", "components": ["Assembler"]}
        ],
    }

    output_path = tmp_path / "architecture.docx"
    write_docx(payload, output_path)

    assert output_path.exists()

    with ZipFile(output_path, "r") as archive:
        names = set(archive.namelist())
        assert "word/document.xml" in names
        assert "[Content_Types].xml" in names

        document_xml = archive.read("word/document.xml").decode("utf-8")
        assert "Downloadable Document" in document_xml
