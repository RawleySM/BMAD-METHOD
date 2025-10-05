"""Agent abstractions powered by the OpenAI Agents SDK."""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

from bmad_python_sdk.agents import Agent as BaseAgent

try:  # pragma: no cover - optional dependency for runtime use
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore


class OpenAIAgent(BaseAgent):
    """Concrete BMAD agent that talks to the OpenAI Agents SDK."""

    def __init__(
        self,
        agent_id: str,
        agent_definition_path: str,
        *,
        client: Optional["OpenAI"] = None,
        model: str = "gpt-4.1-mini",
        response_kwargs: Optional[Dict[str, Any]] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(agent_id, agent_definition_path)
        self.client: Optional["OpenAI"] = client
        self.model = model
        self.response_kwargs = response_kwargs or {}
        self._client_options = client_options or {}

    # ---------------------------------------------------------------------
    # Prompt helpers
    # ---------------------------------------------------------------------
    def _format_persona(self) -> str:
        if not self.persona:
            return ""

        lines: List[str] = []
        for key, value in self.persona.items():
            human_key = key.replace("_", " ").strip().capitalize()
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
                lines.append(f"{human_key}:")
                for item in value:
                    lines.append(f"- {item}")
            elif isinstance(value, dict):
                lines.append(f"{human_key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  - {sub_key}: {sub_value}")
            else:
                lines.append(f"{human_key}: {value}")
        return "\n".join(lines)

    def _format_commands(self) -> str:
        if not self.commands:
            return "No explicit command shortcuts are defined for this agent."

        lines = ["Available Commands:"]
        for entry in self.commands:
            if isinstance(entry, dict):
                for command, description in entry.items():
                    lines.append(f"- {command}: {description}")
            else:
                lines.append(f"- {entry}")
        return "\n".join(lines)

    def _format_dependencies(self) -> str:
        if not self.dependencies:
            return "No external dependencies declared."

        lines = ["Referenced Dependencies:"]
        for dep_type, items in self.dependencies.items():
            lines.append(f"- {dep_type}:")
            for item in items:
                lines.append(f"  - {item}")
        return "\n".join(lines)

    def _format_context(self, context: Dict[str, Any]) -> str:
        if not context:
            return "None provided."

        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Assemble the system instructions sent to the OpenAI model."""

        context = context or {}
        agent_title = self.agent_info.get("title") or self.agent_id
        agent_name = self.agent_info.get("name", "")
        base = [
            f"You are {agent_title} ({self.agent_id}).",
            "Adopt the persona and operating constraints defined for the BMAD workflow.",
        ]
        if agent_name:
            base.insert(0, f"Agent name: {agent_name}")

        persona_block = self._format_persona()
        if persona_block:
            base.append("\nPersona:")
            base.append(persona_block)

        dependencies_block = self._format_dependencies()
        if dependencies_block:
            base.append("\nReference Materials:")
            base.append(dependencies_block)

        if context:
            base.append("\nPreviously created artifacts and context:")
            base.append(self._format_context(context))

        return "\n".join(base)

    def get_prompt(self, task: str, context: Dict[str, Any]) -> str:  # type: ignore[override]
        """Generate the user prompt passed to the OpenAI model."""

        parts = [
            f"Primary task: {task}",
            "Follow the BMAD workflow guidance precisely and produce actionable output.",
            "If required artifacts are missing, note the gap and propose next steps before proceeding.",
            "\n" + self._format_commands(),
        ]

        if context:
            parts.append("\nLeverage the available context when generating your response.")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # OpenAI execution
    # ------------------------------------------------------------------
    def _ensure_client(self, client: Optional["OpenAI"]) -> "OpenAI":
        if client is not None:
            return client

        if self.client is not None:
            return self.client

        if OpenAI is None:  # pragma: no cover - requires optional dependency
            raise ImportError(
                "The 'openai' package is required to execute agents. Install it with 'pip install openai'."
            )

        # Allow the caller to override API key / organization via client_options
        options = {**self._client_options}
        api_key = options.pop("api_key", os.getenv("OPENAI_API_KEY"))
        if api_key:
            options.setdefault("api_key", api_key)

        self.client = OpenAI(**options)
        return self.client

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Best-effort extraction of textual content from a Responses API payload."""

        # Newer SDK versions expose a convenience accessor.
        text = getattr(response, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        output = getattr(response, "output", None)
        if output:
            chunks: List[str] = []
            for item in output:
                content = getattr(item, "content", None)
                if content is None and isinstance(item, dict):
                    content = item.get("content")
                if not content:
                    continue
                for block in content:
                    text_obj = getattr(block, "text", None)
                    if text_obj is None and isinstance(block, dict):
                        text_obj = block.get("text")
                    if text_obj is None:
                        continue
                    value = getattr(text_obj, "value", None)
                    if value is None and isinstance(text_obj, dict):
                        value = text_obj.get("value")
                    if isinstance(value, str):
                        chunks.append(value)
            if chunks:
                return "\n".join(chunks).strip()

        # Fall back to string representation so the caller gets something useful.
        return str(response)

    def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        *,
        model: Optional[str] = None,
        client: Optional["OpenAI"] = None,
        response_kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute the agent through the OpenAI Responses API."""

        context = context or {}
        active_client = self._ensure_client(client)

        payload_kwargs = {**self.response_kwargs}
        if response_kwargs:
            payload_kwargs.update(response_kwargs)

        response = active_client.responses.create(
            model=model or self.model,
            input=[
                {"role": "system", "content": self.build_system_prompt(context)},
                {"role": "user", "content": self.get_prompt(task, context)},
            ],
            **payload_kwargs,
        )
        return self._extract_text(response)
