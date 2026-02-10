# AzureArchAssistant

This repository contains document assembly logic for producing architecture deliverables in downloadable DOCX format.

## What it assembles

The generated document always contains:

- Functional requirements section.
- Non-functional requirements section.
- Architecture overview.
- High-level solution summary.
- Capability matrix mapping functionality to software components.
- Explicit **Assumptions** section whenever inputs are incomplete.

## Quick usage

```python
from document_assembler import ArchitectureDocumentInput, assemble_and_export

payload = ArchitectureDocumentInput(
    title="Retail Platform Architecture",
    functional_requirements=["Customers can place orders"],
    non_functional_requirements=["99.95% availability"],
    architecture_overview="Layered services with API gateway and event backbone.",
    high_level_solution_summary="Deploy microservices with CI/CD and observability.",
    capabilities_to_components={
        "Order Management": ["Order API", "Order Service"],
        "Inventory Sync": ["Inventory Worker"],
    },
)

output = assemble_and_export(payload, "artifacts/architecture.docx")
print(output)
```

The resulting `.docx` can be downloaded and opened in Microsoft Word, LibreOffice, or Google Docs.

## Run tests

```bash
pytest -q
```
