# AzureArchAssistant

Generates architecture requirement documents in **downloadable DOCX format**.

## Features

The assembler always includes:
- Functional requirements section
- Non-functional requirements section
- Architecture overview
- High-level solution summary
- Capability matrix mapping functionality to software components
- Explicit assumptions section when inputs are missing/unclear

## Usage

Create an input payload, e.g. `input.json`:

```json
{
  "project_name": "Contoso Platform Modernization",
  "functional_requirements": [
    "Users can submit architecture requests",
    "System can generate requirement documents"
  ],
  "non_functional_requirements": [
    "99.9% availability",
    "Encryption at rest and in transit"
  ],
  "architecture_overview": "Event-driven microservice architecture on Azure.",
  "high_level_solution_summary": "Use API Management, App Services, and Storage for generated deliverables.",
  "capability_matrix": [
    {
      "functionality": "Submit architecture requests",
      "components": ["API Gateway", "Request Service"]
    },
    {
      "functionality": "Generate deliverables",
      "components": ["Document Assembler", "Template Repository"]
    }
  ],
  "unclear_inputs": [
    "Retention policy for generated documents not provided"
  ]
}
```

Generate a DOCX:

```bash
python document_assembler.py --input input.json --output dist/architecture-document.docx
```

The output file can be downloaded/shared as a standard `.docx` document.

## Test

```bash
python -m pytest -q
```
