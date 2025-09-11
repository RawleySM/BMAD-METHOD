# BMAD Automator Tools

This directory contains enhanced automation tools for the BMAD methodology, specifically designed to integrate with Claude Code CLI and agentic drop zone systems.

## Files

### `bmad_automator_enhanced_md.py`
Enhanced BMAD automator that supports Markdown configuration files (`initProject.md`). Key features:
- **Markdown Config Parser**: Extracts project details, constraints, tech stack, and BMAD settings
- **Automatic BMAD Installation**: Installs and configures BMAD-METHOD with expansion packs
- **Claude Code Integration**: Sets up Claude Code as the primary BMAD administrator
- **Intelligent Decision Making**: Makes constraint-aware decisions using Claude SDK
- **Comprehensive Logging**: Complete audit trail with structured logging

### `example_initProject.md`
Complete example of a project specification file that demonstrates the expected Markdown structure for the automator. Includes:
- Project overview and goals
- Budget and timeline constraints
- Technical requirements and tech stack
- BMAD configuration settings
- Success metrics

### `bmad_project_init.md`
Claude Code command prompt for BMAD project initialization. Provides structured guidance for:
- Project specification analysis
- BMAD methodology assessment
- Initialization recommendations
- Next steps planning

## Usage

### With Agentic Drop Zone System
1. Configure drop zone to monitor for `initProject.md` files
2. Drop zone automatically creates project directories
3. BMAD automator processes the Markdown configuration
4. System installs and configures BMAD automatically

### Manual Usage
```bash
# Set required environment variable
export ANTHROPIC_API_KEY="your-api-key-here"

# Ensure initProject.md exists in current directory
echo "CLI output..." | python bmad_automator_enhanced_md.py
```

### Integration with Claude Code Hooks
The automator is designed to work with Claude Code CLI hooks for seamless automation during development workflows.

## Requirements

- Python 3.11+
- Node.js (for BMAD-METHOD installation)
- Claude Code SDK
- Anthropic API key (set as environment variable)

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for Claude SDK authentication

## Features

- ✅ Markdown configuration parsing
- ✅ Automatic BMAD installation and setup
- ✅ Claude Code integration
- ✅ Expansion pack configuration
- ✅ Intelligent decision making
- ✅ Comprehensive audit logging
- ✅ Error handling and fallbacks
- ✅ Secure API key handling

## Integration

This automator is designed to work with:
- **PrompEnhancer Agent**: Generates structured `initProject.md` files
- **Agentic Drop Zone System**: Monitors and processes project files
- **Claude Code CLI**: Provides intelligent development assistance
- **BMAD Methodology**: Ensures proper agile AI-driven development practices
