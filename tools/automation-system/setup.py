#!/usr/bin/env python3
"""
BMAD Automation System Setup Script

This script sets up the complete end-to-end BMAD automation system.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print("✅ Python version OK")
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found - required for BMAD installation")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found - required for BMAD installation")
        return False
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - will need to be configured")
    else:
        print("✅ ANTHROPIC_API_KEY configured")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    dependencies = [
        "claude-code-sdk",
        "pydantic",
        "watchdog", 
        "pyyaml",
        "python-dotenv",
        "rich"
    ]
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install"
        ] + dependencies, check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file template"""
    print("\n📝 Creating .env file template...")
    
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# BMAD Automation System Environment Variables

# Required: Anthropic API Key for Claude SDK
ANTHROPIC_API_KEY=your-api-key-here

# Optional: Claude Code CLI path (if not in PATH)
CLAUDE_CODE_PATH=claude

# Optional: Custom paths
BMAD_AUTOMATOR_PATH=bmad_automator_enhanced_md.py
"""
        env_file.write_text(env_content)
        print("✅ Created .env template")
        print("⚠️  Please edit .env and add your ANTHROPIC_API_KEY")
    else:
        print("✅ .env file already exists")

def verify_structure():
    """Verify directory structure"""
    print("\n📁 Verifying directory structure...")
    
    required_dirs = [
        "zone-dir",
        "project-drops", 
        ".claude/commands"
    ]
    
    required_files = [
        "drops.yaml",
        "sfs_agentic_drop_zone_enhanced.py",
        "bmad_automator_enhanced_md.py",
        "prompt_enhancer.py",
        "integrated_drop_zone.py",
        ".claude/commands/prompt_enhancer.md",
        ".claude/commands/bmad_project_init.md"
    ]
    
    # Check directories
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check files
    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ Missing file: {file_path}")
    
    return len(missing_files) == 0

def main():
    """Main setup function"""
    print("🚀 BMAD Automation System Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed")
        return False
    
    # Create .env file
    create_env_file()
    
    # Verify structure
    if not verify_structure():
        print("\n❌ Directory structure verification failed")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your ANTHROPIC_API_KEY")
    print("2. Run: python integrated_drop_zone.py")
    print("3. Drop a prompt.txt file in zone-dir/ to test")
    print("\n🔗 Workflow:")
    print("prompt.txt → PrompEnhancer → initProject.md → BMAD Automator → Complete Project")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
