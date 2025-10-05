"""Example usage of the OpenAI-backed BMAD Python SDK."""

from bmad_openai_sdk import OpenAIWorkflow, generate_prompt_from_template


def run_workflow_example() -> None:
    print("Starting BMAD OpenAI SDK Example...")

    workflow_path = "bmad-core/workflows/greenfield-fullstack.yaml"
    workflow = OpenAIWorkflow(workflow_definition_path=workflow_path)

    # Dry run keeps the example runnable without an API key; set dry_run=False to call OpenAI.
    result = workflow.run(
        initial_context={"project_name": "Example App"},
        dry_run=True,
    )

    print("\n--- Workflow Log ---")
    for line in result.log:
        print(line)


def generate_prompt_example() -> None:
    print("\n--- Generating Prompt ---")
    template_path = "bmad-core/templates/prd-tmpl.yaml"
    prompt = generate_prompt_from_template(
        template_path,
        {
            "project_name": "Example App",
            "user_type": "Administrator",
            "action": "manage user access",
            "benefit": "maintain security effortlessly",
        },
    )
    print(prompt)


if __name__ == "__main__":
    run_workflow_example()
    generate_prompt_example()
