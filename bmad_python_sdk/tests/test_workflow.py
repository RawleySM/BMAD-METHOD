import unittest
import os
from bmad_python_sdk.workflow import Workflow

class TestWorkflow(unittest.TestCase):

    def setUp(self):
        # This setup assumes the test is run from the root of the project
        self.workflow_path = "bmad-core/workflows/greenfield-fullstack.yaml"
        self.agent_base_path = "bmad-core/agents"

    def test_workflow_loading(self):
        """
        Tests that a workflow definition is loaded correctly.
        """
        self.assertTrue(os.path.exists(self.workflow_path), f"Workflow file not found at {self.workflow_path}")

        workflow = Workflow(self.workflow_path, self.agent_base_path)
        self.assertIsNotNone(workflow.sequence, "Workflow sequence should not be None after loading.")
        self.assertIsInstance(workflow.sequence, list, "Workflow sequence should be a list.")
        self.assertGreater(len(workflow.sequence), 0, "Workflow sequence should not be empty.")

    def test_workflow_run_simulation(self):
        """
        Tests the simulation of a workflow run.
        """
        workflow = Workflow(self.workflow_path, self.agent_base_path)
        execution_log = workflow.run()

        self.assertIsInstance(execution_log, list, "Execution log should be a list.")
        self.assertGreater(len(execution_log), 1, "Execution log should have more than one entry.")
        self.assertEqual(execution_log[-1], "Workflow finished.", "The last log entry should indicate the workflow finished.")

if __name__ == '__main__':
    unittest.main()