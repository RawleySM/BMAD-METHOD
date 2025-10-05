import unittest
import os
from bmad_python_sdk.prompts import generate_prompt_from_template

class TestPrompts(unittest.TestCase):

    def setUp(self):
        # This setup assumes the test is run from the root of the project
        self.template_path = "bmad-core/templates/prd-tmpl.yaml"
        self.context = {
            "project_name": "Test Project",
            "epic_number": "1",
            "epic_title": "Test Epic"
        }

    def test_prompt_generation_from_template(self):
        """
        Tests that a prompt is generated correctly from a template.
        """
        self.assertTrue(os.path.exists(self.template_path), f"Template file not found at {self.template_path}")

        prompt = generate_prompt_from_template(self.template_path, self.context)

        self.assertIn("Subject: Product Requirements Document", prompt)
        self.assertIn("## Epic 1 Test Epic", prompt)
        self.assertIn("CRITICAL STORY SEQUENCING REQUIREMENTS:", prompt)
        self.assertIn("Examples:", prompt)

    def test_prompt_generation_with_invalid_template(self):
        """
        Tests that prompt generation raises an error for a non-existent template.
        """
        with self.assertRaises(ValueError):
            generate_prompt_from_template("non_existent_template.yaml", self.context)

if __name__ == '__main__':
    unittest.main()