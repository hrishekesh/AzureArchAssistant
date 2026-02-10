# Azure Architecture Assistant

This project assembles architecture design documents into a downloadable `.docx` file.

## Features

The generated document always includes:

- Functional requirements section.
- Non-functional requirements section.
- Architecture overview and high-level solution summary.
- Capability matrix mapping functionality to software components.
- Explicit Assumptions section when any required inputs are missing or unclear.

## Input format

Provide a JSON file:

```json
{
  "title": "Architecture Design Document",
  "functional_requirements": [
    "Users can submit architecture requests",
    "The system validates request schema"
  ],
  "non_functional_requirements": [
    "99.9% availability",
    "Response time under 2 seconds"
  ],
  "architecture_overview": "Event-driven services on Azure.",
  "high_level_solution_summary": "An API captures requirements and routes orchestration jobs.",
  "capability_matrix": [
    {"capability": "Request intake", "components": ["API Gateway", "Request Service"]},
    {"capability": "Workflow orchestration", "components": ["Orchestrator", "Queue"]}
  ],
  "assumptions": [
    "Authentication will use Azure AD."
  ]
}
```

## Generate a document

```bash
python -m azure_arch_assistant.document_assembler example_input.json --output output/architecture_design.docx
```

The output `.docx` can be downloaded and opened in Word, LibreOffice, or Google Docs.
