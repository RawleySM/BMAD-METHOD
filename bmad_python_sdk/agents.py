import yaml
from typing import Any, Dict, List, Optional

class Agent:
    """
    Represents a generic agent in the BMAD workflow.
    This class is designed to be subclassed by specific agent types.
    """
    def __init__(self, agent_id: str, agent_definition_path: str):
        """
        Initializes an Agent.

        Args:
            agent_id: The unique identifier for the agent (e.g., 'analyst', 'pm').
            agent_definition_path: The file path to the agent's markdown definition.
        """
        self.agent_id = agent_id
        self.agent_definition_path = agent_definition_path
        self.persona = None
        self.commands = None
        self.dependencies = None
        self._load_agent_definition()

    def _load_agent_definition(self):
        """
        Loads the agent's definition from the provided markdown file.
        The definition is expected to be in a YAML block within the file.
        """
        with open(self.agent_definition_path, 'r') as f:
            content = f.read()

        # Extract the YAML block from the markdown file
        try:
            yaml_content = content.split('```yaml')[1].split('```')[0]
            definition = yaml.safe_load(yaml_content)

            self.persona = definition.get('persona', {})
            self.commands = definition.get('commands', [])
            self.dependencies = definition.get('dependencies', {})
            self.agent_info = definition.get('agent', {})

        except (IndexError, yaml.YAMLError) as e:
            raise ValueError(f"Could not parse YAML definition from {self.agent_definition_path}: {e}")

    def get_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generates a prompt for the agent to perform a specific task.
        This method will be customized by subclasses.

        Args:
            task: The task to be performed.
            context: The context for the task.

        Returns:
            A string representing the prompt for the language model.
        """
        # Base implementation to be overridden
        return f"As {self.agent_info.get('title', self.agent_id)}, perform the following task: {task}"

    def __repr__(self) -> str:
        return f"Agent(id='{self.agent_id}', title='{self.agent_info.get('title', 'N/A')}')"