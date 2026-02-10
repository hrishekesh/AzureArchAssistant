"""Azure MCP integration layer."""

from __future__ import annotations

from .client import AzureMcpClient, BestPracticeBundle, format_architecture_with_citations


def retrieve_azure_guidance(endpoint: str) -> BestPracticeBundle:
    """Retrieve Azure best practices and production checklist guidance.

    Args:
        endpoint: Base URL for the Azure MCP server JSON-RPC endpoint.

    Returns:
        BestPracticeBundle containing best practices and production checklists.
    """
    client = AzureMcpClient(endpoint)
    return client.fetch_best_practices()


__all__ = [
    "AzureMcpClient",
    "BestPracticeBundle",
    "format_architecture_with_citations",
    "retrieve_azure_guidance",
]
