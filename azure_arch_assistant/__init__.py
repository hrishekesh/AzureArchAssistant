"""Azure architecture document assembly utilities."""

from .assembler import (
    CapabilityMapping,
    ProjectInput,
    assemble_document,
    write_docx,
)

__all__ = [
    "CapabilityMapping",
    "ProjectInput",
    "assemble_document",
    "write_docx",
]
