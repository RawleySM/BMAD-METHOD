# BMAD Python SDK

This directory contains a Python SDK for the BMAD (Breakthrough Method of Agile AI-Driven Development) workflow. It is designed to work with the Google Agents ADK and provides a framework for orchestrating a multi-agent system based on the principles of BMAD.

## Overview

The SDK is composed of three main components:

- `agents.py`: Defines the base `Agent` class, which is responsible for loading agent definitions from the markdown files in `bmad-core/agents`. Each agent's persona, commands, and dependencies are parsed from these files.
- `workflow.py`: Contains the `Workflow` class, which loads workflow definitions (e.g., `greenfield-fullstack.yaml`) and orchestrates the sequence of agent hand-offs. It simulates the execution of a BMAD workflow.
- `prompts.py`: Provides utilities for generating prompts from the structured YAML templates found in `bmad-core/templates`. This allows for the dynamic creation of instructions for the agents.

## How to Use

The `example.py` script in the root directory demonstrates how to use the SDK. To run it, you will first need to install the necessary dependencies:

```bash
pip install pyyaml
```

Then, you can run the example from the root of the project:

```bash
python3 example.py
```

The script will:

1.  Run a simulation of the "Greenfield Full-Stack" workflow, printing out each step of the agent hand-off process.
2.  Generate a sample prompt from the `prd-tmpl.yaml` template to demonstrate the prompt generation capabilities.

This SDK provides a foundation for building a fully-fledged implementation of the BMAD workflow using Python and the Google Agents ADK.

## Additional Documentation

For an in-depth review, architecture diagrams, PRD, technical specifications, and roadmap guidance, see [`docs/bmad-python-sdk.md`](../docs/bmad-python-sdk.md).
