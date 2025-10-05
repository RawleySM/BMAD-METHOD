# BMAD OpenAI Python SDK

This directory contains an alternative Python SDK for BMAD (Breakthrough Method of Agile AI-Driven Development) that targets the **OpenAI Agents SDK**. It mirrors the structure of the original Google Agents ADK prototype while providing real integration points for the OpenAI Responses/Agents runtime.

## Components

- `agents.py` – Implements `OpenAIAgent`, a concrete agent that reads persona definitions from `bmad-core/agents` and executes work through the OpenAI Responses API.
- `workflow.py` – Contains `OpenAIWorkflow`, a runner that orchestrates a workflow definition (for example `bmad-core/workflows/greenfield-fullstack.yaml`) by invoking `OpenAIAgent` instances. It returns both a log of execution events and the generated artifacts/context.
- `prompts.py` – Utility helpers for rendering BMAD YAML templates into rich prompts that can be fed to the OpenAI APIs.
- `__init__.py` – Convenience exports so the SDK can be imported as a module.

## Installation

The SDK depends on the official `openai` Python package. Install the library and export an API key before running workflows:

```bash
pip install openai pyyaml
export OPENAI_API_KEY="sk-..."
```

Alternatively, pass a configured `OpenAI` client object when instantiating `OpenAIAgent` or `OpenAIWorkflow`.

## Usage

```python
from bmad_openai_sdk import OpenAIWorkflow

workflow = OpenAIWorkflow(
    workflow_definition_path="bmad-core/workflows/greenfield-fullstack.yaml",
    default_model="gpt-4.1-mini",
)

result = workflow.run(initial_context={"project_name": "Lunar CRM"}, dry_run=True)

print("\n".join(result.log))
```

Switch `dry_run` to `False` (the default) to stream the tasks to the OpenAI APIs. Use the `agent_overrides` argument to tailor models or runtime parameters for specific agents.

For prompt-centric workflows you can reuse the shared template helper:

```python
from bmad_openai_sdk import generate_prompt_from_template

prompt = generate_prompt_from_template(
    "bmad-core/templates/prd-tmpl.yaml",
    {"project_name": "Lunar CRM", "user_type": "Admin"}
)
print(prompt)
```

This SDK serves as a starting point for executing BMAD playbooks with OpenAI-hosted agents while keeping compatibility with the BMAD Core assets.
