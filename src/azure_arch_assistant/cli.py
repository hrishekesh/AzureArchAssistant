from __future__ import annotations

import argparse
import json
from pathlib import Path

from azure_arch_assistant.document_assembly import assemble_document, export_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assemble architecture requirement documents.")
    parser.add_argument("--input", required=True, help="Path to JSON input payload.")
    parser.add_argument(
        "--output",
        required=True,
        help="Output path (.docx or .md).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    document = assemble_document(payload)
    destination = export_document(document, args.output)
    print(f"Document generated: {destination}")


if __name__ == "__main__":
    main()
