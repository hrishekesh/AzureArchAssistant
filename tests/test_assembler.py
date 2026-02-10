import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from azure_arch_assistant.assembler import (
    CapabilityMapping,
    ProjectInput,
    assemble_document,
    write_docx,
)


class AssembleDocumentTests(unittest.TestCase):
    def test_infers_assumptions_when_inputs_missing(self) -> None:
        doc = assemble_document(ProjectInput())

        self.assertTrue(doc.assumptions)
        self.assertIn("Functional requirements input was incomplete.", doc.assumptions)
        self.assertEqual(doc.capability_matrix[0].component, "TBD Component")

    def test_uses_provided_sections(self) -> None:
        doc = assemble_document(
            ProjectInput(
                functional_requirements=["Order capture"],
                non_functional_requirements=["99.9% availability"],
                architecture_overview="Event-driven architecture on Azure.",
                high_level_solution_summary="Incremental delivery with CI/CD.",
                capability_matrix=[
                    CapabilityMapping("Order capture", "Order API")
                ],
            )
        )

        self.assertEqual(doc.assumptions, [])
        self.assertEqual(doc.capability_matrix[0].component, "Order API")


class WriteDocxTests(unittest.TestCase):
    def test_writes_docx_with_expected_sections(self) -> None:
        doc = assemble_document(
            ProjectInput(
                functional_requirements=["Customer onboarding"],
                non_functional_requirements=["Encryption at rest"],
                architecture_overview="Hub-spoke network and microservices.",
                high_level_solution_summary="Use managed Azure services.",
                capability_matrix=[
                    CapabilityMapping("Customer onboarding", "Onboarding Service")
                ],
                assumptions=["Identity provider is Entra ID."],
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "architecture.docx"
            write_docx(doc, output)

            self.assertTrue(output.exists())
            with ZipFile(output) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")

            self.assertIn("Functional Requirements", document_xml)
            self.assertIn("Non-Functional Requirements", document_xml)
            self.assertIn("Capability Matrix", document_xml)
            self.assertIn("Assumptions", document_xml)


if __name__ == "__main__":
    unittest.main()
