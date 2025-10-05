from bmad_python_sdk.workflow import Workflow
from bmad_python_sdk.prompts import generate_prompt_from_template

def run_workflow_example():
    """
    Demonstrates running a BMAD workflow using the Python SDK.
    """
    print("Starting BMAD Python SDK Example...")

    # 1. Initialize and run a workflow
    print("\n--- Running Greenfield Full-Stack Workflow Simulation ---")
    try:
        # Path to the workflow definition
        workflow_path = "bmad-core/workflows/greenfield-fullstack.yaml"

        # Initialize the workflow
        bmad_workflow = Workflow(workflow_definition_path=workflow_path)

        # Run the workflow and get the execution log
        execution_log = bmad_workflow.run()

        # Print the log
        for log_entry in execution_log:
            print(log_entry)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error running workflow: {e}")

def generate_prompt_example():
    """
    Demonstrates generating a prompt from a template.
    """
    print("\n--- Generating a PRD Prompt from a Template ---")
    try:
        # Path to the PRD template
        template_path = "bmad-core/templates/prd-tmpl.yaml"

        # Example context to inject into the template
        context = {
            "project_name": "My Awesome App",
            "user_type": "Admin",
            "action": "manage user accounts",
            "benefit": "I can efficiently control access to the system"
        }

        # Generate the prompt
        prompt = generate_prompt_from_template(template_path, context)

        print("Generated Prompt:")
        print(prompt)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error generating prompt: {e}")

if __name__ == "__main__":
    run_workflow_example()
    generate_prompt_example()