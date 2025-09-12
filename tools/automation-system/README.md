# BMAD Automation System

Complete end-to-end automation system that transforms rough project ideas into detailed BMAD specifications with PRD, architecture, and development roadmap.

## 🔄 **Complete Workflow**

```
prompt.txt → PrompEnhancer → initProject.md → BMAD Automator → Complete Project Setup
```

1. **User drops `prompt.txt`** with rough project idea in `zone-dir/`
2. **PrompEnhancer Agent** converts it to structured `initProject.md`
3. **BMAD Automator** processes the specification and creates project directory
4. **BMAD-METHOD** installs and generates complete project documentation
5. **Result**: Full project with PRD, architecture docs, and development roadmap

## 🚀 **Quick Start**

### 1. Setup
```bash
# Run setup script
python setup.py

# Create .env file and add your API key
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

### 2. Start the System
```bash
python integrated_drop_zone.py
```

### 3. Test the Workflow
```bash
# Copy sample prompt to trigger workflow
cp sample_prompt.txt zone-dir/prompt.txt
```

## 📁 **System Components**

### Core Files
- **`integrated_drop_zone.py`** - Main system orchestrator
- **`prompt_enhancer.py`** - Converts rough prompts to structured specs
- **`bmad_automator_enhanced_md.py`** - BMAD project initialization
- **`sfs_agentic_drop_zone_enhanced.py`** - File monitoring system

### Configuration
- **`drops.yaml`** - Drop zone configuration
- **`.env`** - Environment variables (API keys)
- **`.claude/commands/`** - Claude Code prompts

### Directories
- **`zone-dir/`** - Drop prompt.txt files here
- **`project-drops/`** - Alternative drop location
- **Generated projects** - Created automatically with unique names

## 🔧 **Configuration**

### Environment Variables (.env)
```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional
CLAUDE_CODE_PATH=claude
BMAD_AUTOMATOR_PATH=bmad_automator_enhanced_md.py
```

### Drop Zone Configuration (drops.yaml)
The system monitors multiple file patterns:
- **`prompt.txt`** → PrompEnhancer → `initProject.md`
- **`initProject.md`** → BMAD Automator → Complete project setup

## 📋 **Requirements**

- **Python 3.11+**
- **Node.js** (for BMAD-METHOD installation)
- **Anthropic API Key**
- **Internet connection** (for package installation)

## 🎯 **Features**

### PrompEnhancer Agent
- ✅ Converts unstructured prompts to structured specifications
- ✅ Intelligent project name extraction
- ✅ Realistic budget and timeline estimation
- ✅ Technology stack recommendations
- ✅ BMAD expansion pack selection

### BMAD Automator
- ✅ Automatic BMAD-METHOD installation
- ✅ Project directory creation with conflict resolution
- ✅ Claude Code integration setup
- ✅ Expansion pack configuration
- ✅ Comprehensive logging and audit trails

### Integrated Drop Zone
- ✅ Real-time file monitoring
- ✅ Multi-stage workflow orchestration
- ✅ Error handling and recovery
- ✅ Rich console output with progress tracking

## 📖 **Usage Examples**

### Example 1: Simple Web App
```
# zone-dir/prompt.txt
Build a todo app with user authentication and real-time sync
```

### Example 2: AI-Powered Application
```
# zone-dir/prompt.txt
Create a smart recipe recommendation system that uses AI to suggest 
personalized recipes based on dietary preferences and available ingredients
```

### Example 3: E-commerce Platform
```
# zone-dir/prompt.txt
Build an online marketplace for handmade crafts with payment processing,
seller dashboards, and customer reviews
```

## 🔍 **Monitoring & Logs**

The system provides comprehensive logging:
- **Console Output**: Real-time progress and status
- **Decision Logs**: `bmad_decisions.jsonl` - All AI decisions with reasoning
- **Installation Logs**: BMAD installation and configuration details
- **Error Handling**: Detailed error messages and recovery suggestions

## 🛠 **Troubleshooting**

### Common Issues

**API Key Not Set**
```bash
# Check .env file
cat .env
# Ensure ANTHROPIC_API_KEY is set correctly
```

**Node.js Not Found**
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Permission Errors**
```bash
# Ensure proper permissions
chmod +x *.py
```

**BMAD Installation Fails**
```bash
# Check Node.js version (requires 20.10.0+)
node --version
# Check npm connectivity
npm ping
```

## 🔗 **Integration**

### With Claude Code CLI
The system integrates seamlessly with Claude Code CLI:
- Automatic hook configuration
- IDE-specific settings
- Development workflow optimization

### With BMAD-METHOD
- Automatic installation and setup
- Expansion pack configuration
- Project structure generation
- Documentation templates

## 📊 **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   prompt.txt    │───▶│  PrompEnhancer   │───▶│ initProject.md  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Complete Project│◀───│  BMAD Automator  │◀───│ Drop Zone System│
│   - PRD         │    │  - Installation  │    │  - Monitoring   │
│   - Architecture│    │  - Configuration │    │  - Orchestration│
│   - Roadmap     │    │  - Setup         │    │  - Error Handle │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎉 **Success Criteria**

The system is working correctly when:
1. ✅ Dropping `prompt.txt` triggers PrompEnhancer
2. ✅ `initProject.md` is generated with structured content
3. ✅ BMAD Automator creates project directory
4. ✅ BMAD-METHOD installs successfully
5. ✅ Complete project documentation is generated
6. ✅ All steps are logged and auditable

## 📞 **Support**

For issues or questions:
1. Check the console output for error messages
2. Review log files for detailed information
3. Verify environment configuration
4. Ensure all requirements are met

## 🔒 **Security**

- **No hardcoded API keys** - All keys must be set via environment variables
- **Secure file handling** - Proper validation and sanitization
- **Audit trails** - Complete logging of all operations
- **Error isolation** - Failures don't compromise system integrity

---

**Ready to transform your project ideas into complete BMAD specifications!** 🚀
