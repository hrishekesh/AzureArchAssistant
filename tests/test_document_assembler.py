from pathlib import Path
from zipfile import ZipFile

from document_assembler import ArchitectureDocumentInput, DocumentAssembler, assemble_and_export


def test_assemble_populates_required_sections_and_assumptions():
    payload = ArchitectureDocumentInput(
        title="Target Platform Architecture",
        functional_requirements=["Users can submit claims"],
        capabilities_to_components={"Claims Intake": ["Claims API", "Workflow Engine"]},
    )

    assembled = DocumentAssembler().assemble(payload)

    assert assembled.functional_requirements
    assert assembled.non_functional_requirements
    assert assembled.architecture_overview
    assert assembled.high_level_solution_summary
    assert assembled.capability_matrix_rows == [
        ("Claims Intake", "Claims API"),
        ("Claims Intake", "Workflow Engine"),
    ]
    assert any("Non-functional requirements" in entry for entry in assembled.assumptions)


def test_docx_export_contains_expected_sections(tmp_path: Path):
    payload = ArchitectureDocumentInput(
        title="Architecture Baseline",
        functional_requirements=["Capture order"],
        non_functional_requirements=["99.9% availability"],
        architecture_overview="Event-driven microservice architecture.",
        high_level_solution_summary="Deploy to managed Kubernetes with CI/CD.",
        capabilities_to_components={"Order Processing": ["Order API"]},
    )

    out_file = tmp_path / "architecture.docx"
    generated = assemble_and_export(payload, out_file)

    assert generated.exists()
    with ZipFile(generated) as docx:
        document_xml = docx.read("word/document.xml").decode("utf-8")

    for expected in [
        "Functional Requirements",
        "Non-Functional Requirements",
        "Architecture Overview",
        "High-Level Solution Summary",
        "Capability Matrix",
        "Assumptions",
        "Order Processing | Order API",
    ]:
        assert expected in document_xml
