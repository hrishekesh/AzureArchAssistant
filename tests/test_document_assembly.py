from pathlib import Path

from azure_arch_assistant.document_assembly import assemble_document, export_document


def test_assemble_document_includes_required_sections() -> None:
    payload = {
        "project_name": "Sample Project",
        "functional_requirements": ["Users can submit orders"],
        "non_functional_requirements": ["99.9% availability"],
        "architecture_overview": "Event-driven architecture.",
        "high_level_solution_summary": "Web app + API + queue.",
        "capabilities": [
            {"capability": "Order Submission", "components": ["Frontend", "Orders API"]}
        ],
    }

    document = assemble_document(payload)

    assert "## Functional Requirements" in document.content
    assert "## Non-Functional Requirements" in document.content
    assert "## Architecture Overview" in document.content
    assert "## High-Level Solution Summary" in document.content
    assert "## Capability Matrix" in document.content
    assert "## Assumptions" in document.content
    assert "| Order Submission | Frontend, Orders API |" in document.content


def test_assumptions_added_when_input_unclear() -> None:
    payload = {
        "project_name": "Unclear",
        "functional_requirements": [],
        "non_functional_requirements": "TBD",
        "architecture_overview": "",
        "high_level_solution_summary": "not provided",
    }

    document = assemble_document(payload)

    assert len(document.assumptions) >= 4
    assert "- Not provided." in document.content


def test_markdown_export(tmp_path: Path) -> None:
    document = assemble_document({"project_name": "Export Test"})
    output_file = tmp_path / "out.md"

    result = export_document(document, output_file)

    assert result.exists()
    assert result.read_text(encoding="utf-8").startswith("# Export Test")
