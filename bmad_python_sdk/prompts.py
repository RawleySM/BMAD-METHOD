import yaml
from typing import Any, Dict, List

def generate_prompt_from_template(template_path: str, context: Dict[str, Any]) -> str:
    """
    Generates a prompt string from a YAML template and context.

    This is a simplified implementation that demonstrates how to construct
    a prompt from a structured template. It iterates through the sections
of a template and combines instructions with context data.

    Args:
        template_path: The file path to the YAML template.
        context: A dictionary containing data to be injected into the prompt.

    Returns:
        A string representing the generated prompt.
    """
    try:
        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        raise ValueError(f"Could not load or parse template from {template_path}: {e}")

    prompt_parts = []
    template_metadata = template.get('template', {})

    prompt_parts.append(f"Subject: {template_metadata.get('name', 'Untitled Document')}")
    prompt_parts.append(f"Version: {template_metadata.get('version', '1.0')}")
    prompt_parts.append("\nInstructions:")

    for section in template.get('sections', []):
        title = section.get('title', 'Unnamed Section')
        instruction = section.get('instruction', '')

        # Replace placeholders in the title, like {{project_name}}
        for key, value in context.items():
            title = title.replace(f"{{{{{key}}}}}", str(value))

        prompt_parts.append(f"\n## {title}")
        prompt_parts.append(instruction)

        # Add examples if they exist in the template
        examples = section.get('examples')
        if examples:
            prompt_parts.append("\nExamples:")
            if isinstance(examples, list):
                for example in examples:
                    prompt_parts.append(f"- {example}")
            elif isinstance(examples, dict):
                 for key, value in examples.items():
                    prompt_parts.append(f"- {key}: {value}")

    return "\n".join(prompt_parts)