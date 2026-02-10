# Azure Architecture Assistant

This repository provides document assembly logic for producing architecture deliverables in downloadable DOCX format.

## Features

- Functional requirements section.
- Non-functional requirements section.
- Architecture overview section.
- High-level solution summary section.
- Capability matrix mapping functionality to software components.
- Explicit assumptions section when inputs are unclear.

## Usage

```bash
python -m azure_arch_assistant.cli input.json output.docx
```

### Input JSON shape

```json
{
  "functional_requirements": ["Order capture", "Order tracking"],
  "non_functional_requirements": ["99.9% availability"],
  "architecture_overview": "Event-driven microservices architecture.",
  "high_level_solution_summary": "Use managed Azure services and CI/CD pipelines.",
  "capability_matrix": [
    {"functionality": "Order capture", "component": "Order API"}
  ],
  "assumptions": ["Client will provide SSO integration details."]
}
```
