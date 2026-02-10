"""Client helpers for talking to the Azure MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
import json
import urllib.request
import urllib.error


class McpError(RuntimeError):
    """Raised when the MCP server returns an error response."""


def _json_rpc_request(
    endpoint: str,
    method: str,
    params: Optional[dict[str, Any]] = None,
    request_id: int = 1,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            response_data = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise McpError(f"Failed to reach MCP server at {endpoint}: {exc}") from exc

    try:
        decoded = json.loads(response_data)
    except json.JSONDecodeError as exc:
        raise McpError("MCP server returned non-JSON response") from exc

    if "error" in decoded:
        raise McpError(decoded["error"])

    return decoded


@dataclass(frozen=True)
class McpResource:
    uri: str
    name: str
    description: str | None = None


@dataclass(frozen=True)
class BestPractice:
    title: str
    content: str
    source_uri: str


@dataclass(frozen=True)
class BestPracticeBundle:
    best_practices: tuple[BestPractice, ...]
    production_checklist: tuple[BestPractice, ...]


class AzureMcpClient:
    """Thin MCP client for Azure guidance resources."""

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint.rstrip("/")

    def list_resources(self) -> tuple[McpResource, ...]:
        response = _json_rpc_request(self._endpoint, "resources/list")
        resources = response.get("result", {}).get("resources", [])
        return tuple(
            McpResource(
                uri=resource.get("uri", ""),
                name=resource.get("name", ""),
                description=resource.get("description"),
            )
            for resource in resources
        )

    def read_resource(self, uri: str) -> dict[str, Any]:
        response = _json_rpc_request(
            self._endpoint,
            "resources/read",
            params={"uri": uri},
        )
        return response.get("result", {})

    def find_guidance_resources(self) -> tuple[McpResource, ...]:
        resources = self.list_resources()
        guidance_keywords = ("best", "practice", "checklist", "production")
        return tuple(
            resource
            for resource in resources
            if any(keyword in resource.name.lower() for keyword in guidance_keywords)
        )

    def fetch_best_practices(self) -> BestPracticeBundle:
        guidance = self.find_guidance_resources()
        best_practices: list[BestPractice] = []
        checklists: list[BestPractice] = []
        for resource in guidance:
            payload = self.read_resource(resource.uri)
            contents = payload.get("contents", [])
            for entry in contents:
                text = entry.get("text") or entry.get("content") or ""
                title = resource.name
                item = BestPractice(title=title, content=text, source_uri=resource.uri)
                if "checklist" in resource.name.lower():
                    checklists.append(item)
                else:
                    best_practices.append(item)
        return BestPracticeBundle(
            best_practices=tuple(best_practices),
            production_checklist=tuple(checklists),
        )


def format_architecture_with_citations(
    architecture_text: str,
    guidance: BestPracticeBundle,
) -> str:
    """Combine architecture output with Azure guidance citations."""

    def _format_section(title: str, items: Iterable[BestPractice]) -> str:
        lines = [f"\n{title}:"]
        for item in items:
            citation = f"[source: {item.source_uri}]"
            lines.append(f"- {item.content.strip()} {citation}")
        return "\n".join(lines)

    sections = [architecture_text.rstrip()]
    if guidance.best_practices:
        sections.append(_format_section("Azure Best Practices", guidance.best_practices))
    if guidance.production_checklist:
        sections.append(
            _format_section("Azure Production Checklist", guidance.production_checklist)
        )
    return "\n".join(sections).strip() + "\n"
