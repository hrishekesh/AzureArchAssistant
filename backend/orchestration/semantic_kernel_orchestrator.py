"""Semantic Kernel orchestration for multi-agent architecture generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.chat_message_content import AuthorRole
from semantic_kernel.kernel import Kernel


@dataclass(frozen=True)
class AgentDefinition:
    """Defines an agent's role prompt and responsibilities."""

    name: str
    role_prompt: str
    responsibilities: Sequence[str]

    def system_prompt(self) -> str:
        responsibilities = "\n".join(f"- {item}" for item in self.responsibilities)
        return f"""You are the {self.name} agent.

Role:
{self.role_prompt}

Responsibilities:
{responsibilities}
"""


@dataclass
class ArchitectureContext:
    """Input context for the architecture request."""

    goal: str
    domain: str | None = None
    compliance: str | None = None
    scale: str | None = None
    constraints: Sequence[str] = field(default_factory=list)
    notes: Sequence[str] = field(default_factory=list)


@dataclass
class ArchitectureDocument:
    """Unified architecture document output."""

    content: str
    assumptions: Sequence[str]
    agent_summaries: dict[str, str]


class SemanticKernelOrchestrator:
    """Coordinates multi-agent collaboration using Semantic Kernel."""

    def __init__(
        self,
        kernel: Kernel,
        agent_definitions: Iterable[AgentDefinition],
        chat_service_id: str,
        max_rounds: int = 2,
    ) -> None:
        self.kernel = kernel
        self.agent_definitions = list(agent_definitions)
        self.chat_service_id = chat_service_id
        self.max_rounds = max_rounds

    async def run(self, context: ArchitectureContext) -> ArchitectureDocument:
        assumptions = self._collect_assumptions(context)
        history = ChatHistory()
        history.add_message(
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content="You are coordinating an architecture review group chat.",
            )
        )
        history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=self._format_context(context, assumptions),
            )
        )
        agent_summaries: dict[str, str] = {}
        for _ in range(self.max_rounds):
            for agent_definition in self.agent_definitions:
                agent_summary = await self._invoke_agent(agent_definition, history)
                agent_summaries[agent_definition.name] = agent_summary
                history.add_message(
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content=f"[{agent_definition.name}] {agent_summary}",
                    )
                )
        unified_document = self._assemble_document(context, agent_summaries, assumptions)
        return ArchitectureDocument(
            content=unified_document,
            assumptions=assumptions,
            agent_summaries=agent_summaries,
        )

    async def _invoke_agent(
        self, agent_definition: AgentDefinition, history: ChatHistory
    ) -> str:
        chat_history = ChatHistory(messages=list(history))
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.SYSTEM,
                content=agent_definition.system_prompt(),
            )
        )
        chat_completion = self.kernel.get_service(self.chat_service_id)
        responses = await chat_completion.get_chat_message_contents(
            chat_history, kernel=self.kernel
        )
        if not responses:
            return "No response generated."
        return responses[0].content or "No response generated."

    def _collect_assumptions(self, context: ArchitectureContext) -> list[str]:
        assumptions: list[str] = []
        if not context.domain:
            assumptions.append("Assumed a general-purpose business web application domain.")
        if not context.compliance:
            assumptions.append("Assumed standard Azure compliance (SOC 2, ISO 27001).")
        if not context.scale:
            assumptions.append("Assumed moderate scale with room for growth (tens of thousands of users).")
        if not context.constraints:
            assumptions.append("Assumed no special constraints beyond typical cloud governance policies.")
        return assumptions

    def _format_context(self, context: ArchitectureContext, assumptions: Sequence[str]) -> str:
        constraint_lines = "\n".join(f"- {item}" for item in context.constraints) or "- None"
        note_lines = "\n".join(f"- {item}" for item in context.notes) or "- None"
        assumption_lines = "\n".join(f"- {item}" for item in assumptions) or "- None"
        return f"""Architecture Goal: {context.goal}
Domain: {context.domain or 'Unknown'}
Compliance: {context.compliance or 'Unknown'}
Scale: {context.scale or 'Unknown'}

Constraints:
{constraint_lines}

Additional Notes:
{note_lines}

Assumptions (include these in the final output):
{assumption_lines}
"""

    def _assemble_document(
        self,
        context: ArchitectureContext,
        agent_summaries: dict[str, str],
        assumptions: Sequence[str],
    ) -> str:
        assumption_lines = "\n".join(f"- {item}" for item in assumptions) or "- None"
        summary_lines = "\n".join(
            f"### {agent}\n{summary}" for agent, summary in agent_summaries.items()
        )
        return f"""# Unified Architecture Document

## Goal
{context.goal}

## Architecture Guidance by Agent
{summary_lines}

## Consolidated Recommendations
Synthesize the agent feedback into a cohesive architecture that balances security,
scalability, performance, and user experience. Highlight trade-offs explicitly.

## Assumptions
{assumption_lines}
"""


def default_agent_definitions() -> list[AgentDefinition]:
    """Return the standard architecture review agents."""

    return [
        AgentDefinition(
            name="Security",
            role_prompt="Focus on identity, network protection, data security, and governance.",
            responsibilities=[
                "Recommend identity and access controls",
                "Identify data protection and encryption needs",
                "Highlight threat modeling and monitoring requirements",
            ],
        ),
        AgentDefinition(
            name="Infrastructure",
            role_prompt="Design resilient Azure infrastructure and deployment topology.",
            responsibilities=[
                "Define core Azure services and network layout",
                "Ensure high availability and disaster recovery",
                "Recommend IaC and operational tooling",
            ],
        ),
        AgentDefinition(
            name="Performance",
            role_prompt="Optimize for scalability, latency, and cost efficiency.",
            responsibilities=[
                "Evaluate scalability and caching strategies",
                "Recommend performance monitoring and tuning",
                "Identify cost optimization opportunities",
            ],
        ),
        AgentDefinition(
            name="Web Designer",
            role_prompt="Ensure web experience, accessibility, and UX alignment.",
            responsibilities=[
                "Advise on UX, accessibility, and responsiveness",
                "Recommend front-end architecture patterns",
                "Highlight branding and design system needs",
            ],
        ),
        AgentDefinition(
            name="Solution Architect",
            role_prompt="Integrate agent input into a cohesive architecture plan.",
            responsibilities=[
                "Balance trade-offs across security, infra, performance, and UX",
                "Provide overall architecture narrative",
                "Ensure alignment with business goals",
            ],
        ),
    ]
