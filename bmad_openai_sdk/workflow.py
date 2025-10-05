"""Workflow orchestration backed by the OpenAI Agents SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from .agents import OpenAIAgent


@dataclass
class WorkflowRunResult:
    """Structured result returned from :meth:`OpenAIWorkflow.run`."""

    log: List[str]
    context: Dict[str, Any]


class OpenAIWorkflow:
    """Execute BMAD workflows using OpenAI-powered agents."""

    def __init__(
        self,
        workflow_definition_path: str,
        agent_definitions_base_path: str = "bmad-core/agents",
        *,
        client: Optional[Any] = None,
        default_model: str = "gpt-4.1-mini",
        agent_factory_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.workflow_definition_path = workflow_definition_path
        self.agent_definitions_base_path = agent_definitions_base_path
        self.sequence: List[Dict[str, Any]] = []
        self.client = client
        self.default_model = default_model
        self.agent_factory_kwargs = agent_factory_kwargs or {}

        self._load_workflow_definition()

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------
    def _load_workflow_definition(self) -> None:
        with open(self.workflow_definition_path, "r", encoding="utf-8") as handle:
            try:
                definition = yaml.safe_load(handle)
            except yaml.YAMLError as exc:  # pragma: no cover - simple pass through
                raise ValueError(
                    f"Could not parse YAML definition from {self.workflow_definition_path}: {exc}"
                ) from exc

        self.sequence = definition.get("workflow", {}).get("sequence", [])

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _artifact_key(step: Dict[str, Any]) -> Optional[str]:
        for key in ("creates", "updates", "action", "step"):
            value = step.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    @staticmethod
    def _describe_step(step: Dict[str, Any]) -> str:
        if "creates" in step:
            return f"create {step['creates']}"
        if "updates" in step:
            return f"update {step['updates']}"
        if "action" in step:
            return step["action"]
        return step.get("step", "Unnamed step")

    @staticmethod
    def _build_task_description(step: Dict[str, Any]) -> str:
        parts: List[str] = []
        if step.get("creates"):
            parts.append(f"Create the artifact named '{step['creates']}'.")
        if step.get("updates"):
            parts.append(f"Update the artifact named '{step['updates']}'.")
        if step.get("requires"):
            required = step["requires"]
            if isinstance(required, list):
                required_str = ", ".join(required)
            else:
                required_str = str(required)
            parts.append(f"Required context: {required_str}.")
        if step.get("notes"):
            parts.append(step["notes"])
        if step.get("optional_steps"):
            optional = ", ".join(step["optional_steps"])
            parts.append(f"Optional subtasks to consider: {optional}.")
        if step.get("condition"):
            parts.append(f"Execute only if condition '{step['condition']}' is satisfied.")
        return " ".join(parts) if parts else "Follow the BMAD workflow guidance for this step."

    @staticmethod
    def _should_skip(step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        condition = step.get("condition")
        if not condition:
            return False
        return not bool(context.get(condition))

    def _instantiate_agent(
        self,
        agent_id: str,
        *,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> OpenAIAgent:
        definition_path = f"{self.agent_definitions_base_path}/{agent_id}.md"
        combined_kwargs = {**self.agent_factory_kwargs}
        overrides = overrides or {}
        init_overrides = overrides.get("init", {})
        combined_kwargs.update(init_overrides)

        if "client" not in combined_kwargs:
            combined_kwargs["client"] = self.client
        if "model" not in combined_kwargs:
            combined_kwargs["model"] = overrides.get("model", self.default_model)

        return OpenAIAgent(agent_id, definition_path, **combined_kwargs)

    def run(
        self,
        initial_context: Optional[Dict[str, Any]] = None,
        *,
        agent_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        dry_run: bool = False,
    ) -> WorkflowRunResult:
        """Execute the workflow and optionally call out to OpenAI."""

        if not self.sequence:
            return WorkflowRunResult(log=["Workflow sequence is not defined."], context=initial_context or {})

        execution_log: List[str] = []
        current_context = dict(initial_context or {})
        agent_overrides = agent_overrides or {}

        for raw_step in self.sequence:
            if self._should_skip(raw_step, current_context):
                execution_log.append(
                    f"Skipping step '{self._describe_step(raw_step)}' because condition "
                    f"'{raw_step.get('condition')}' is not satisfied."
                )
                continue

            agent_spec = raw_step.get("agent")
            if not agent_spec or agent_spec == "various":
                notes_value = raw_step.get("notes", "")
                notes_text = notes_value.strip() if isinstance(notes_value, str) else ""
                execution_log.append(
                    f"Non-agent step '{self._describe_step(raw_step)}': {notes_text}"
                )
                continue

            actual_agent_id = agent_spec.split("/")[0].strip()
            if actual_agent_id != agent_spec:
                execution_log.append(
                    f"Complex agent specifier '{agent_spec}' resolved to '{actual_agent_id}' for execution."
                )

            overrides = agent_overrides.get(actual_agent_id)
            try:
                agent = self._instantiate_agent(actual_agent_id, overrides=overrides)
            except FileNotFoundError:
                execution_log.append(
                    f"Could not find agent definition for '{actual_agent_id}' in {self.agent_definitions_base_path}."
                )
                continue

            task_description = self._build_task_description(raw_step)
            log_prefix = agent.agent_info.get("title", actual_agent_id)

            if dry_run:
                execution_log.append(
                    f"[Dry Run] {log_prefix} would {self._describe_step(raw_step)}. Task detail: {task_description}"
                )
                continue

            run_kwargs = {}
            if overrides:
                run_kwargs = {**overrides.get("run", {})}
                if "model" in overrides and "model" not in run_kwargs:
                    run_kwargs["model"] = overrides["model"]

            try:
                result_text = agent.run(task_description, current_context, **run_kwargs)
            except Exception as exc:  # pragma: no cover - defensive catch
                execution_log.append(f"Agent '{actual_agent_id}' failed: {exc}")
                continue

            artifact_key = self._artifact_key(raw_step)
            if artifact_key:
                current_context[artifact_key] = result_text

            if artifact_key:
                execution_log.append(
                    f"{log_prefix} completed step '{self._describe_step(raw_step)}' and produced artifact '{artifact_key}'."
                )
            else:
                execution_log.append(
                    f"{log_prefix} completed step '{self._describe_step(raw_step)}'."
                )

        execution_log.append("Workflow finished.")
        return WorkflowRunResult(log=execution_log, context=current_context)
