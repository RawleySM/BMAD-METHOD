#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "claude-code-sdk",
#     "pydantic",
#     "watchdog",
#     "pyyaml",
#     "python-dotenv",
#     "rich",
# ]
# ///

"""Enhanced Agentic Drop Zone - File monitoring and processing system with BMAD integration."""

import asyncio
import logging
import os
import shutil
import subprocess
import yaml
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MOVED,
)
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# Load environment variables
load_dotenv()

# Constants
FILE_PATH_PLACEHOLDER = "[[FILE_PATH]]"
PROJECT_NAME_PLACEHOLDER = "[[PROJECT_NAME]]"

# Environment variable checks
def check_environment_variables():
    """Check for required environment variables at startup."""
    required_vars = {
        "ANTHROPIC_API_KEY": "Required for Claude Code SDK authentication",
        "CLAUDE_CODE_PATH": "Required path to Claude CLI executable",
    }

    optional_vars = {
        "REPLICATE_API_TOKEN": "Optional - needed for image generation/editing (won't be able to generate images without it)"
    }

    missing_required = []

    # Check required variables
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"  - {var}: {description}")

    # Display missing required variables
    if missing_required:
        console.print("[bold red]❌ Missing required environment variables:[/bold red]")
        for item in missing_required:
            console.print(f"[red]{item}[/red]")
        console.print(
            "\n[yellow]Please set these in your .env file or environment[/yellow]"
        )
        raise EnvironmentError("Missing required environment variables")

    # Check optional variables and display warnings
    missing_optional = []
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  - {var}: {description}")

    if missing_optional:
        console.print("[yellow]⚠️  Optional environment variables not set:[/yellow]")
        for item in missing_optional:
            console.print(f"[dim]{item}[/dim]")
        console.print()

    console.print("[green]✅ All required environment variables are set[/green]")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class EventType(str, Enum):
    """Supported file system event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"

class AgentType(str, Enum):
    """Supported agent types."""
    CLAUDE_CODE = "claude_code"
    GEMINI_CLI = "gemini_cli"
    CODEX_CLI = "codex_cli"
    BMAD_AUTOMATOR = "bmad_automator"  # New agent type for BMAD integration

class PromptArgs(BaseModel):
    """Arguments for prompt processing."""
    reusable_prompt: str = Field(description="Path to the reusable prompt file")
    file_path: str = Field(description="Path to the file being processed")
    model: Optional[str] = Field(default=None, description="Model to use for processing")
    mcp_server_file: Optional[str] = Field(default=None, description="Path to MCP server configuration file (JSON or YAML)")
    zone_name: Optional[str] = Field(default=None, description="Name of the drop zone")
    zone_color: Optional[str] = Field(default="cyan", description="Color for the drop zone")
    project_name: Optional[str] = Field(default=None, description="Project name extracted from file")

class DropZone(BaseModel):
    """Configuration for a single drop zone."""
    name: str = Field(description="Name of the drop zone")
    file_patterns: list[str] = Field(description="File patterns to watch (e.g., *.txt)")
    reusable_prompt: str = Field(description="Path to the reusable prompt file (e.g., .claude/commands/echo.md)")
    zone_dirs: list[str] = Field(description="List of directories to monitor (supports * wildcard)")
    events: list[EventType] = Field(default=[EventType.CREATED], description="Event types to respond to")
    agent: AgentType = Field(default=AgentType.CLAUDE_CODE, description="Agent type to use for processing")
    model: Optional[str] = Field(default="sonnet", description="Model to use for Claude Code (e.g., 'sonnet', 'opus', 'haiku')")
    mcp_server_file: Optional[str] = Field(default=None, description="Path to MCP server configuration file (JSON or YAML)")
    color: Optional[str] = Field(default="cyan", description="Color for console output (e.g., 'red', 'blue', 'green', 'cyan', 'yellow', 'magenta')")
    create_zone_dir_if_not_exists: bool = Field(default=False, description="Create zone directory if it doesn't exist (non-glob patterns only)")
    new_project_variant: bool = Field(default=False, description="Enable new project creation workflow for initProject.md files")
    bmad_automator_path: Optional[str] = Field(default=None, description="Path to BMAD automator script")

    @field_validator("zone_dirs")
    @classmethod
    def validate_zone_dirs(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("zone_dirs must contain at least one directory")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[EventType]) -> list[EventType]:
        if not v:
            raise ValueError("events must contain at least one event type")
        return v

class DropsConfig(BaseModel):
    """Root configuration for all drop zones."""
    drop_zones: list[DropZone] = Field(description="List of configured drop zones")

class ProjectCreator:
    """Handles new project creation from initProject.md files."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def extract_project_name(self, md_file_path: Path) -> str:
        """Extract project name from initProject.md file."""
        try:
            content = md_file_path.read_text(encoding='utf-8')
            
            # Look for project name in title (first # heading)
            import re
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                project_name = title_match.group(1).strip()
                # Clean up project name for directory use
                project_name = re.sub(r'[^\w\s-]', '', project_name)
                project_name = re.sub(r'[-\s]+', '-', project_name).lower()
                return project_name
            
            # Fallback to filename without extension
            return md_file_path.stem
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error extracting project name: {e}[/yellow]")
            return md_file_path.stem
    
    def create_project_directory(self, project_name: str, source_file: Path) -> Optional[Path]:
        """Create a new project directory and copy the initProject.md file."""
        try:
            # Create project directory
            project_dir = self.base_dir / project_name
            
            # Handle existing directory
            if project_dir.exists():
                console.print(f"[yellow]⚠️  Project directory already exists: {project_dir}[/yellow]")
                # Create a unique name
                counter = 1
                while (self.base_dir / f"{project_name}-{counter}").exists():
                    counter += 1
                project_dir = self.base_dir / f"{project_name}-{counter}"
                console.print(f"[cyan]📁 Using unique directory: {project_dir}[/cyan]")
            
            # Create the directory
            project_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Created project directory: {project_dir}[/green]")
            
            # Copy the initProject.md file to the new directory
            dest_file = project_dir / "initProject.md"
            shutil.copy2(source_file, dest_file)
            console.print(f"[cyan]📄 Copied initProject.md to: {dest_file}[/cyan]")
            
            return project_dir
            
        except Exception as e:
            console.print(f"[bold red]❌ Error creating project directory: {e}[/bold red]")
            return None

class Agents:
    """Agent implementations for processing drop zone files."""

    @staticmethod
    def build_prompt(reusable_prompt_path: str, file_path: str, project_name: Optional[str] = None) -> str:
        """Build the full prompt by loading from file and replacing variables."""
        prompt_path = Path(reusable_prompt_path)

        # Ensure prompt file exists
        if not prompt_path.exists():
            error_msg = f"Reusable prompt file not found: {reusable_prompt_path}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise FileNotFoundError(error_msg)

        if not prompt_path.is_file():
            error_msg = f"Reusable prompt path is not a file: {reusable_prompt_path}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise ValueError(error_msg)

        # Load prompt from file
        console.print(f"[dim]   Loading prompt: {reusable_prompt_path}[/dim]")
        try:
            prompt_content = prompt_path.read_text()
        except Exception as e:
            error_msg = f"Failed to read prompt file {reusable_prompt_path}: {e}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise Exception(error_msg) from e

        # Replace placeholders
        if FILE_PATH_PLACEHOLDER in prompt_content:
            prompt_content = prompt_content.replace(FILE_PATH_PLACEHOLDER, file_path)
        
        if project_name and PROJECT_NAME_PLACEHOLDER in prompt_content:
            prompt_content = prompt_content.replace(PROJECT_NAME_PLACEHOLDER, project_name)

        return prompt_content

    @staticmethod
    async def prompt_bmad_automator(args: PromptArgs) -> None:
        """Process a file using BMAD Automator."""
        console.print(f"[magenta]🤖 Processing with BMAD Automator...[/magenta]")
        
        # Determine BMAD automator script path
        bmad_script_path = "bmad_automator_enhanced_md.py"  # Default
        
        # Check if custom path is provided in the drop zone config
        # This would need to be passed through the args somehow
        
        try:
            # Run BMAD automator with the file
            cmd = ["python", bmad_script_path]
            
            # Read the file content and pass it as stdin
            file_path = Path(args.file_path)
            if file_path.exists():
                with open(file_path, 'r') as f:
                    file_content = f.read()
                
                # Create a mock CLI output for BMAD processing
                mock_cli_output = f"""BMAD Project Initialization:

The following initProject.md file has been created and needs to be processed:

File: {args.file_path}
Project: {args.project_name or 'Unknown Project'}

Content:
---
{file_content}
---

Please analyze this project specification and provide guidance on the next steps for BMAD methodology implementation.

What should be the first priority?

1. Create Project Requirements Document (PRD)
2. Design System Architecture
3. Set up Development Environment
4. Initialize BMAD Core System
5. Configure Expansion Packs

Choose the best option (1-5):"""
                
                # Run the BMAD automator
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=file_path.parent if file_path.parent.exists() else Path.cwd()
                )
                
                stdout, stderr = process.communicate(input=mock_cli_output, timeout=60)
                
                if process.returncode == 0:
                    # Display the result
                    zone_workflow = f"{args.zone_name} BMAD Workflow" if args.zone_name else "BMAD Workflow"
                    panel_color = args.zone_color or "magenta"
                    
                    console.print(
                        Panel(
                            Text(f"BMAD Decision: {stdout.strip()}\n\nProject initialized successfully!"),
                            title=f"[bold {panel_color}]🤖 BMAD Automator • {zone_workflow}[/bold {panel_color}]",
                            subtitle=f"[dim]{file_path.name}[/dim]",
                            border_style=panel_color,
                            expand=False,
                            padding=(1, 2),
                        )
                    )
                else:
                    console.print(f"[bold red]❌ BMAD Automator failed with return code {process.returncode}[/bold red]")
                    if stderr:
                        console.print(f"[red]Error: {stderr}[/red]")
            
        except subprocess.TimeoutExpired:
            console.print("[bold red]❌ BMAD Automator timed out[/bold red]")
        except FileNotFoundError:
            console.print(f"[bold red]❌ BMAD Automator script not found: {bmad_script_path}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Error running BMAD Automator: {e}[/bold red]")

    @staticmethod
    async def prompt_claude_code(args: PromptArgs) -> None:
        """Process a file using Claude Code SDK."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path, args.project_name)

        console.print(f"[cyan]ℹ️  Processing prompt with Claude Code...[/cyan]")
        if args.model:
            console.print(f"[dim]   Model: {args.model}[/dim]")

        # Get CLI path from environment or use default
        cli_path = os.getenv("CLAUDE_CODE_PATH", "claude")

        # If a custom path is set, update PATH environment variable
        if cli_path != "claude":
            # Extract directory from the CLI path
            cli_dir = os.path.dirname(cli_path) if os.path.dirname(cli_path) else "."
            current_path = os.environ.get("PATH", "")
            if cli_dir not in current_path:
                os.environ["PATH"] = f"{cli_dir}:{current_path}"

        # Create options with bypassPermissions mode and optional model
        options_dict = {
            "permission_mode": "bypassPermissions"  # Bypass all permission prompts
        }

        # Add model if specified
        if args.model:
            options_dict["model"] = args.model

        # Add MCP server file if specified
        if args.mcp_server_file:
            options_dict["mcp_servers"] = args.mcp_server_file
            console.print(f"[dim]   MCP config: {args.mcp_server_file}[/dim]")

        options = ClaudeCodeOptions(**options_dict)

        # Minimal Claude Code setup - let errors propagate
        async with ClaudeSDKClient(options=options) as client:
            await client.query(full_prompt)

            # Stream response - output panels as content arrives
            file_name = Path(args.file_path).name
            has_response = False
            zone_workflow = f"{args.zone_name} Workflow" if args.zone_name else "Workflow"
            panel_color = args.zone_color or "cyan"

            async for message in client.receive_response():
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text") and block.text.strip():
                            has_response = True
                            # Output each text block in its own panel
                            console.print(
                                Panel(
                                    Text(block.text),
                                    title=f"[bold {panel_color}]🤖 Claude Code • {zone_workflow}[/bold {panel_color}]",
                                    subtitle=f"[dim]{file_name}[/dim]",
                                    border_style=panel_color,
                                    expand=False,
                                    padding=(1, 2),
                                )
                            )

            # If no response was received
            if not has_response:
                console.print(
                    Panel(
                        Text("[yellow]No response received[/yellow]"),
                        title=f"[bold yellow]🤖 Claude Code • {zone_workflow}[/bold yellow]",
                        subtitle=f"[dim]{file_name}[/dim]",
                        border_style="yellow",
                        expand=False,
                        padding=(1, 2),
                    )
                )

            console.print()

    @staticmethod
    async def prompt_gemini_cli(args: PromptArgs) -> None:
        """Process a file using Gemini CLI."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path, args.project_name)

        console.print(f"[green]ℹ️  Processing prompt with Gemini CLI...[/green]")
        if args.model:
            console.print(f"[dim]   Model: {args.model}[/dim]")

        # Get CLI path from environment or use default
        gemini_path = os.getenv("GEMINI_CLI_PATH", "gemini")

        # Build command with flags
        cmd = [
            gemini_path,
            "--yolo",      # Auto-approve all tool calls
            "--sandbox",   # Enable sandboxing by default
            "-m", args.model or "gemini-2.5-pro",  # Model
            "-p", full_prompt  # Non-interactive prompt
        ]

        console.print(f"[dim]   Command: {' '.join(cmd[:4])}...[/dim]")

        try:
            # Create subprocess with asyncio
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()  # Pass environment variables
            )

            # Prepare for streaming display
            file_name = Path(args.file_path).name
            zone_workflow = f"{args.zone_name} Workflow" if args.zone_name else "Workflow"
            panel_color = args.zone_color or "green"
            has_output = False

            async def read_stream(stream, is_stderr=False):
                """Read and display stream output line by line."""
                nonlocal has_output
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    if decoded:  # Only process non-empty lines
                        has_output = True
                        # Print each line in its own panel
                        console.print(
                            Panel(
                                Text(decoded),
                                title=f"[bold {panel_color}]🤖 Gemini CLI • {zone_workflow}[/bold {panel_color}]",
                                subtitle=f"[dim]{file_name}[/dim]",
                                border_style=panel_color,
                                expand=False,
                                padding=(1, 2),
                            )
                        )

            # Handle both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, is_stderr=False),
                read_stream(process.stderr, is_stderr=True)
            )

            # Wait for process to complete
            return_code = await process.wait()
            
            # Print completion status if needed
            if return_code != 0:
                console.print(f"\n[yellow]⚠️ Process exited with code {return_code}[/yellow]")
            
            # If no output was received, show a message
            if not has_output:
                console.print(
                    Panel(
                        "[yellow]No output received[/yellow]",
                        title=f"[bold yellow]🤖 Gemini CLI • {zone_workflow}[/bold yellow]",
                        subtitle=f"[dim]{file_name}[/dim]",
                        border_style="yellow",
                        expand=False,
                        padding=(1, 2),
                    )
                )

        except FileNotFoundError:
            console.print(f"[bold red]❌ Gemini CLI not found at '{gemini_path}'[/bold red]")
            console.print("[yellow]Please install Gemini CLI: npm install -g @google/gemini-cli[/yellow]")
            console.print("[dim]Or set GEMINI_CLI_PATH environment variable to the correct path[/dim]")
        except Exception as e:
            console.print(f"[bold red]❌ Error running Gemini CLI: {e}[/bold red]")

        console.print()

    @staticmethod
    async def prompt_codex_cli(args: PromptArgs) -> None:
        """Process a file using Codex CLI."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path, args.project_name)

        # TODO: Implement Codex CLI integration
        raise NotImplementedError("Codex CLI agent not yet implemented")

    @staticmethod
    async def process_with_agent(agent: AgentType, args: PromptArgs) -> None:
        """Route to appropriate agent based on type."""
        try:
            if agent == AgentType.CLAUDE_CODE:
                await Agents.prompt_claude_code(args)
            elif agent == AgentType.GEMINI_CLI:
                await Agents.prompt_gemini_cli(args)
            elif agent == AgentType.CODEX_CLI:
                await Agents.prompt_codex_cli(args)
            elif agent == AgentType.BMAD_AUTOMATOR:
                await Agents.prompt_bmad_automator(args)
            else:
                raise ValueError(f"Unknown agent type: {agent}")
        except Exception as e:
            console.print(f"[bold red]❌ Agent processing failed: {e}[/bold red]")
            raise

class DropZoneHandler(FileSystemEventHandler):
    """Enhanced file system event handler for drop zones with new project support."""

    def __init__(self, drop_zone: DropZone, base_dir: Path):
        self.drop_zone = drop_zone
        self.base_dir = base_dir
        self.project_creator = ProjectCreator(base_dir) if drop_zone.new_project_variant else None

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and EventType.CREATED in self.drop_zone.events:
            asyncio.run(self._handle_file_event(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and EventType.MODIFIED in self.drop_zone.events:
            asyncio.run(self._handle_file_event(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and EventType.DELETED in self.drop_zone.events:
            asyncio.run(self._handle_file_event(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory and EventType.MOVED in self.drop_zone.events:
            asyncio.run(self._handle_file_event(event.dest_path))

    async def _handle_file_event(self, file_path: str) -> None:
        """Handle file system events with enhanced new project support."""
        path = Path(file_path)

        # Check if file matches patterns
        if not any(path.match(pattern) for pattern in self.drop_zone.file_patterns):
            return

        zone_color = self.drop_zone.color or "green"
        console.print(f"\n[bold {zone_color}]📁 Drop Zone: {self.drop_zone.name}[/bold {zone_color}]")
        console.print(f"[yellow]   File: {file_path}[/yellow]")
        console.print(f"[dim]   Agent: {self.drop_zone.agent}[/dim]")
        console.print(f"[dim]   Prompt: {self.drop_zone.reusable_prompt}[/dim]")

        project_name = None
        working_directory = path.parent

        # Handle new project variant for initProject.md files
        if self.drop_zone.new_project_variant and self.project_creator:
            if path.name == "initProject.md" or "initProject" in path.name.lower():
                console.print(f"[bold cyan]🚀 New Project Detected![/bold cyan]")
                
                # Extract project name
                project_name = self.project_creator.extract_project_name(path)
                console.print(f"[cyan]   Project Name: {project_name}[/cyan]")
                
                # Create project directory
                project_dir = self.project_creator.create_project_directory(project_name, path)
                if project_dir:
                    working_directory = project_dir
                    # Update file path to the copied file
                    file_path = str(project_dir / "initProject.md")
                    console.print(f"[green]✅ Project directory created: {project_dir}[/green]")
                else:
                    console.print("[bold red]❌ Failed to create project directory[/bold red]")
                    return

        if self.drop_zone.model:
            console.print(f"[dim]   Model: {self.drop_zone.model}[/dim]")
        if self.drop_zone.mcp_server_file:
            console.print(f"[dim]   MCP: {self.drop_zone.mcp_server_file}[/dim]")

        # Create PromptArgs
        prompt_args = PromptArgs(
            reusable_prompt=self.drop_zone.reusable_prompt,
            file_path=file_path,
            model=self.drop_zone.model,
            mcp_server_file=self.drop_zone.mcp_server_file,
            zone_name=self.drop_zone.name,
            zone_color=self.drop_zone.color,
            project_name=project_name,
        )

        # Change to working directory for agent execution
        original_cwd = Path.cwd()
        try:
            os.chdir(working_directory)
            console.print(f"[dim]   Working Directory: {working_directory}[/dim]")
            
            # Run the agent
            await Agents.process_with_agent(self.drop_zone.agent, prompt_args)
            
        finally:
            os.chdir(original_cwd)

class AgenticDropZone:
    """Enhanced main application class for the Agentic Drop Zone with BMAD support."""

    def __init__(self, config_file: Path = Path("drops.yaml")):
        self.config_file = config_file
        self.config: Optional[DropsConfig] = None
        self.observers: list[Observer] = []
        self.base_path = Path.cwd()

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if not self.config_file.exists():
                error_msg = f"Configuration file not found: {self.config_file}"
                console.print(f"[bold red]❌ {error_msg}[/bold red]")
                raise FileNotFoundError(error_msg)

            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f)

            self.config = DropsConfig(**data)
            console.print(f"[green]✅ Loaded configuration from {self.config_file}[/green]")
            console.print(f"[cyan]   Found {len(self.config.drop_zones)} drop zone(s)[/cyan]")
        except FileNotFoundError:
            raise
        except Exception as e:
            console.print(f"[bold red]❌ Error loading configuration: {e}[/bold red]")
            raise

    def _expand_zone_dirs(self, drop_zone: DropZone) -> list[Path]:
        """Expand zone_dirs patterns to actual directories."""
        expanded_dirs = []

        for zone_dir in drop_zone.zone_dirs:
            if "*" in zone_dir:
                # Simple wildcard support - just use the pattern as-is
                matching_dirs = list(self.base_path.glob(zone_dir))
                # Filter to only directories
                matching_dirs = [d for d in matching_dirs if d.is_dir()]
                if matching_dirs:
                    expanded_dirs.extend(matching_dirs)
                    console.print(
                        f"[dim]   Pattern '{zone_dir}' matched {len(matching_dirs)} directories: {[d.name for d in matching_dirs]}[/dim]"
                    )
                else:
                    console.print(
                        f"[yellow]⚠️  Pattern '{zone_dir}' matched no directories[/yellow]"
                    )
            else:
                # Direct directory path (non-glob)
                dir_path = self.base_path / zone_dir
                if dir_path.exists() and dir_path.is_dir():
                    expanded_dirs.append(dir_path)
                elif not dir_path.exists():
                    # Directory doesn't exist
                    if drop_zone.create_zone_dir_if_not_exists:
                        # Create the directory
                        try:
                            dir_path.mkdir(parents=True, exist_ok=True)
                            console.print(f"[green]✅ Created zone directory: {dir_path}[/green]")
                            expanded_dirs.append(dir_path)
                        except Exception as e:
                            console.print(f"[bold red]❌ Failed to create directory {dir_path}: {e}[/bold red]")
                    else:
                        # Log error and ask user to create it
                        console.print(f"[bold red]❌ Zone directory does not exist: {dir_path}[/bold red]")
                        console.print(f"[yellow]   Please create the directory manually: mkdir -p {dir_path}[/yellow]")
                        console.print(f"[dim]   Or set 'create_zone_dir_if_not_exists: true' in drops.yaml for zone '{drop_zone.name}'[/dim]")
                else:
                    console.print(f"[yellow]⚠️  Path exists but is not a directory: {dir_path}[/yellow]")

        return expanded_dirs

    def start(self) -> None:
        """Start monitoring all configured drop zones."""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        for drop_zone in self.config.drop_zones:
            # Expand zone_dirs patterns
            zone_paths = self._expand_zone_dirs(drop_zone)

            if not zone_paths:
                console.print(f"[yellow]⚠️  No valid directories found for drop zone '{drop_zone.name}'[/yellow]")
                continue

            # Create observer for each directory
            for zone_path in zone_paths:
                observer = Observer()
                handler = DropZoneHandler(drop_zone, self.base_path)

                # Schedule non-recursive watching
                observer.schedule(handler, str(zone_path), recursive=False)
                observer.start()
                self.observers.append(observer)

                zone_color = drop_zone.color or "green"
                console.print(f"\n[bold {zone_color}]✅ Started monitoring drop zone: {drop_zone.name}[/bold {zone_color}]")
                console.print(f"[cyan]   📂 Path: {zone_path}[/cyan]")
                console.print(f"[dim]   - Patterns: {drop_zone.file_patterns}[/dim]")
                console.print(f"[dim]   - Events: {[e.value for e in drop_zone.events]}[/dim]")
                console.print(f"[dim]   - Agent: {drop_zone.agent}[/dim]")
                console.print(f"[dim]   - Prompt: {drop_zone.reusable_prompt}[/dim]")
                if drop_zone.new_project_variant:
                    console.print(f"[dim]   - New Project Mode: Enabled[/dim]")
                if drop_zone.model:
                    console.print(f"[dim]   - Model: {drop_zone.model}[/dim]")
                if drop_zone.mcp_server_file:
                    console.print(f"[dim]   - MCP: {drop_zone.mcp_server_file}[/dim]")

        if self.observers:
            console.print(f"\n[bold cyan]🎯 Total observers started: {len(self.observers)}[/bold cyan]")
            console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
        else:
            console.print("[bold red]⚠️ No observers started. Check your configuration.[/bold red]")

    def stop(self) -> None:
        """Stop monitoring all drop zones."""
        for observer in self.observers:
            observer.stop()

        for observer in self.observers:
            observer.join()

        console.print(f"[yellow]🛑 Stopped {len(self.observers)} observer(s)[/yellow]")
        self.observers.clear()

    async def run(self) -> None:
        """Run the drop zone monitor."""
        self.load_config()
        self.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚡ Received interrupt signal[/yellow]")
        finally:
            self.stop()

async def main():
    """Main entry point."""
    # Display startup banner
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   🚀 Enhanced Agentic Drop Zone 🚀[/bold cyan]")
    console.print("[bold cyan]      with BMAD Integration[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # Check environment variables
    check_environment_variables()

    drop_zone = AgenticDropZone(config_file=Path("drops.yaml"))
    await drop_zone.run()

if __name__ == "__main__":
    asyncio.run(main())
