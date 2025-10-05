"""Prompt generation helpers for the OpenAI-powered SDK."""

from __future__ import annotations

import yaml
from typing import Any, Dict


def generate_prompt_from_template(template_path: str, context: Dict[str, Any]) -> str:
    """Build a prompt string from a BMAD template file."""

    try:
        with open(template_path, "r", encoding="utf-8") as handle:
            template = yaml.safe_load(handle)
    except (FileNotFoundError, yaml.YAMLError) as exc:  # pragma: no cover - simple pass through
        raise ValueError(f"Could not load or parse template from {template_path}: {exc}") from exc

    prompt_parts = []
    template_metadata = template.get("template", {})

    prompt_parts.append(f"Subject: {template_metadata.get('name', 'Untitled Document')}")
    prompt_parts.append(f"Version: {template_metadata.get('version', '1.0')}")
    prompt_parts.append("\nInstructions:")

    for section in template.get("sections", []):
        title = section.get("title", "Unnamed Section")
        instruction = section.get("instruction", "")

        for key, value in context.items():
            title = title.replace(f"{{{{{key}}}}}", str(value))
            instruction = instruction.replace(f"{{{{{key}}}}}", str(value))

        prompt_parts.append(f"\n## {title}")
        if instruction:
            prompt_parts.append(instruction)

        examples = section.get("examples")
        if examples:
            prompt_parts.append("\nExamples:")
            if isinstance(examples, list):
                for example in examples:
                    prompt_parts.append(f"- {example}")
            elif isinstance(examples, dict):
                for example_key, example_value in examples.items():
                    prompt_parts.append(f"- {example_key}: {example_value}")

    return "\n".join(prompt_parts)
