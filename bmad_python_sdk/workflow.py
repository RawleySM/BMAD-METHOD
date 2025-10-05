import yaml
from typing import Any, Dict, List
from .agents import Agent

class Workflow:
    """
    Orchestrates a sequence of agent interactions based on a workflow definition.
    """
    def __init__(self, workflow_definition_path: str, agent_definitions_base_path: str = "bmad-core/agents"):
        """
        Initializes a Workflow.

        Args:
            workflow_definition_path: The file path to the workflow's YAML definition.
            agent_definitions_base_path: The base directory where agent markdown files are stored.
        """
        self.workflow_definition_path = workflow_definition_path
        self.agent_definitions_base_path = agent_definitions_base_path
        self.sequence = None
        self._load_workflow_definition()

    def _load_workflow_definition(self):
        """
        Loads the workflow definition from the provided YAML file.
        """
        with open(self.workflow_definition_path, 'r') as f:
            try:
                definition = yaml.safe_load(f)
                self.sequence = definition.get('workflow', {}).get('sequence', [])
            except yaml.YAMLError as e:
                raise ValueError(f"Could not parse YAML definition from {self.workflow_definition_path}: {e}")

    def run(self, initial_context: Dict[str, Any] = None):
        """
        Executes the workflow sequence.

        This is a simulation of the workflow execution. In a real implementation
        with the Google Agents ADK, this would involve invoking language models.

        Args:
            initial_context: An optional dictionary representing the initial state.

        Returns:
            A list of strings describing the workflow execution steps.
        """
        if not self.sequence:
            return ["Workflow sequence is not defined."]

        execution_log = []
        current_context = initial_context or {}

        for step in self.sequence:
            agent_id = step.get('agent')
            if not agent_id or agent_id == "various":
                # Handle non-agent steps or complex steps
                log_message = f"Executing step: {step.get('step', 'Unnamed Step')} - {step.get('notes', '')}"
                execution_log.append(log_message)
                continue

            actual_agent_id = agent_id
            if '/' in agent_id:
                # Handle complex specifiers like 'analyst/pm' by picking the first agent for simulation
                actual_agent_id = agent_id.split('/')[0]
                log_message = f"Complex agent specifier '{agent_id}' found. Choosing '{actual_agent_id}' for this step."
                execution_log.append(log_message)

            agent_definition_path = f"{self.agent_definitions_base_path}/{actual_agent_id}.md"

            try:
                agent = Agent(actual_agent_id, agent_definition_path)

                creates_artifact = step.get('creates', 'an artifact')
                requires_artifacts = step.get('requires', 'initial context')

                log_message = (
                    f"Running Agent: {agent.agent_info.get('title', actual_agent_id)} "
                    f"to create '{creates_artifact}'. "
                    f"Requires: {requires_artifacts}."
                )
                execution_log.append(log_message)

                # In a real ADK implementation, this is where you would:
                # 1. Generate a detailed prompt using agent.get_prompt()
                # 2. Invoke the language model with the prompt
                # 3. Process the model's output to update the context

                # For this simulation, we'll just update the context with the new artifact
                current_context[creates_artifact] = f"Content of {creates_artifact}"

            except FileNotFoundError:
                log_message = f"Could not find agent definition for '{actual_agent_id}' at '{agent_definition_path}'."
                execution_log.append(log_message)
            except ValueError as e:
                execution_log.append(str(e))

        execution_log.append("Workflow finished.")
        return execution_log

    def __repr__(self) -> str:
        return f"Workflow(definition='{self.workflow_definition_path}')"