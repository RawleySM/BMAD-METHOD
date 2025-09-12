#!/usr/bin/env python3
"""
Integrated Drop Zone System with PrompEnhancer and BMAD Automator

This system provides end-to-end automation from prompt.txt to complete BMAD project setup.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Import the enhanced drop zone system
sys.path.append(str(Path(__file__).parent))
from sfs_agentic_drop_zone_enhanced import AgenticDropZone, DropZoneHandler, Agents, PromptArgs

class IntegratedDropZoneHandler(DropZoneHandler):
    """Enhanced drop zone handler with PrompEnhancer integration"""
    
    async def _handle_file_event(self, file_path: str) -> None:
        """Handle file system events with PrompEnhancer integration"""
        path = Path(file_path)
        
        # Check if file matches patterns
        if not any(path.match(pattern) for pattern in self.drop_zone.file_patterns):
            return
        
        zone_color = self.drop_zone.color or "green"
        console = __import__('rich.console', fromlist=['Console']).Console()
        
        console.print(f"\n[bold {zone_color}]📁 Drop Zone: {self.drop_zone.name}[/bold {zone_color}]")
        console.print(f"[yellow]   File: {file_path}[/yellow]")
        
        # Special handling for prompt.txt files
        if path.name == "prompt.txt" or "prompt" in path.name.lower():
            await self._handle_prompt_file(path, console, zone_color)
        else:
            # Use the original handler for other files
            await super()._handle_file_event(file_path)
    
    async def _handle_prompt_file(self, prompt_path: Path, console, zone_color: str):
        """Handle prompt.txt files with PrompEnhancer"""
        console.print(f"[bold cyan]🚀 PrompEnhancer Detected![/bold cyan]")
        console.print(f"[cyan]   Processing: {prompt_path.name}[/cyan]")
        
        try:
            # Check for API key
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                console.print("[bold red]❌ ANTHROPIC_API_KEY not set. Please configure your API key.[/bold red]")
                return
            
            # Run PrompEnhancer
            enhancer_script = Path(__file__).parent / "prompt_enhancer.py"
            if not enhancer_script.exists():
                console.print(f"[bold red]❌ PrompEnhancer script not found: {enhancer_script}[/bold red]")
                return
            
            console.print("[cyan]   Running PrompEnhancer...[/cyan]")
            
            # Execute PrompEnhancer
            process = subprocess.Popen(
                [sys.executable, str(enhancer_script), str(prompt_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )
            
            stdout, stderr = process.communicate(timeout=120)  # 2 minute timeout
            
            if process.returncode == 0:
                console.print("[green]✅ PrompEnhancer completed successfully![/green]")
                console.print(f"[dim]{stdout.strip()}[/dim]")
                
                # Check if initProject.md was created
                init_project_file = prompt_path.parent / "initProject.md"
                if init_project_file.exists():
                    console.print(f"[green]📄 Generated: {init_project_file}[/green]")
                    console.print("[cyan]   initProject.md will be processed by BMAD automator...[/cyan]")
                else:
                    console.print("[yellow]⚠️  initProject.md not found after enhancement[/yellow]")
            else:
                console.print(f"[bold red]❌ PrompEnhancer failed with return code {process.returncode}[/bold red]")
                if stderr:
                    console.print(f"[red]Error: {stderr}[/red]")
                    
        except subprocess.TimeoutExpired:
            console.print("[bold red]❌ PrompEnhancer timed out after 2 minutes[/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Error running PrompEnhancer: {e}[/bold red]")

class IntegratedAgenticDropZone(AgenticDropZone):
    """Enhanced drop zone system with PrompEnhancer integration"""
    
    def _expand_zone_dirs(self, drop_zone):
        """Override to use integrated handler"""
        expanded_dirs = super()._expand_zone_dirs(drop_zone)
        return expanded_dirs
    
    def start(self) -> None:
        """Start monitoring with integrated handlers"""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        console = __import__('rich.console', fromlist=['Console']).Console()
        
        for drop_zone in self.config.drop_zones:
            # Expand zone_dirs patterns
            zone_paths = self._expand_zone_dirs(drop_zone)

            if not zone_paths:
                console.print(f"[yellow]⚠️  No valid directories found for drop zone '{drop_zone.name}'[/yellow]")
                continue

            # Create observer for each directory
            from watchdog.observers import Observer
            for zone_path in zone_paths:
                observer = Observer()
                
                # Use integrated handler for prompt files, regular handler for others
                if any("prompt" in pattern for pattern in drop_zone.file_patterns):
                    handler = IntegratedDropZoneHandler(drop_zone, self.base_path)
                else:
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
                if "prompt" in str(drop_zone.file_patterns):
                    console.print(f"[dim]   - PrompEnhancer: Enabled[/dim]")

        if self.observers:
            console.print(f"\n[bold cyan]🎯 Total observers started: {len(self.observers)}[/bold cyan]")
            console.print("[bold green]🚀 End-to-End BMAD Automation System Ready![/bold green]")
            console.print("[dim]Drop a prompt.txt file in zone-dir/ to start the workflow...[/dim]")
            console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
        else:
            console.print("[bold red]⚠️ No observers started. Check your configuration.[/bold red]")

async def main():
    """Main entry point for integrated system"""
    console = __import__('rich.console', fromlist=['Console']).Console()
    
    # Display startup banner
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   🚀 Integrated BMAD Automation 🚀[/bold cyan]")
    console.print("[bold cyan]     PrompEnhancer + Drop Zone[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # Check environment variables
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]❌ ANTHROPIC_API_KEY environment variable not set[/bold red]")
        console.print("[yellow]Please set your Anthropic API key to continue.[/yellow]")
        return

    console.print("[green]✅ Environment configured[/green]")

    # Initialize integrated drop zone system
    drop_zone = IntegratedAgenticDropZone(config_file=Path("drops.yaml"))
    await drop_zone.run()

if __name__ == "__main__":
    asyncio.run(main())
