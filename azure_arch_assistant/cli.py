from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import CapabilityMapping, ProjectInput, assemble_document, write_docx


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an architecture document in DOCX format.")
    parser.add_argument("input", type=Path, help="Path to input JSON.")
    parser.add_argument("output", type=Path, help="Path to output DOCX file.")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))

    capability_matrix = [
        CapabilityMapping(
            functionality=item.get("functionality", ""),
            component=item.get("component", ""),
        )
        for item in payload.get("capability_matrix", [])
    ]

    project_input = ProjectInput(
        functional_requirements=payload.get("functional_requirements", []),
        non_functional_requirements=payload.get("non_functional_requirements", []),
        architecture_overview=payload.get("architecture_overview", ""),
        high_level_solution_summary=payload.get("high_level_solution_summary", ""),
        capability_matrix=capability_matrix,
        assumptions=payload.get("assumptions", []),
    )

    document = assemble_document(project_input)
    output_path = write_docx(document, args.output)
    print(output_path)


if __name__ == "__main__":
    main()
