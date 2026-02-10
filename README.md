# Azure Architecture Assistant

This repository contains a document assembly utility that builds architecture output in **DOCX** format.

## Features

The assembler always includes:

- Functional requirements section
- Non-functional requirements section
- Architecture overview and high-level solution summary
- Capability matrix mapping functionality to software components
- Explicit assumptions section when inputs are incomplete or unclear

## Usage

```bash
python3 document_assembler.py examples/sample_input.json -o output/architecture_document.docx
```

## Input JSON shape

```json
{
  "title": "Architecture & Requirements Document",
  "functional_requirements": ["..."],
  "non_functional_requirements": ["..."],
  "architecture_overview": "...",
  "high_level_solution_summary": "...",
  "capability_matrix": [
    {"capability": "...", "component": "...", "notes": "..."}
  ],
  "assumptions": ["Optional explicit assumptions"]
}
```
