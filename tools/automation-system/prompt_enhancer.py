#!/usr/bin/env python3
"""
PrompEnhancer Agent - Converts unstructured prompt.txt files into structured initProject.md files

This agent takes rough project ideas from prompt.txt files and transforms them into
structured initProject.md files that can be processed by the BMAD automator system.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

class PrompEnhancer:
    """Enhances unstructured project prompts into structured BMAD-compatible specifications"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        os.environ["ANTHROPIC_API_KEY"] = api_key
    
    def extract_project_name(self, content: str) -> str:
        """Extract a project name from the content"""
        # Look for explicit project names
        name_patterns = [
            r'project\s*(?:name|title):\s*(.+)',
            r'(?:build|create|develop)\s+(?:a|an)?\s*(.+?)(?:\s+(?:app|application|system|platform|tool|website))',
            r'^(.+?)(?:\s+(?:app|application|system|platform|tool|website))',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'[^\w\s-]', '', name)
                name = re.sub(r'[-\s]+', '-', name).lower()
                if len(name) > 3:  # Ensure it's a meaningful name
                    return name.title().replace('-', ' ')
        
        # Fallback to generic name
        return "AI-Powered Application"
    
    async def enhance_prompt(self, prompt_content: str) -> str:
        """Convert unstructured prompt to structured initProject.md"""
        
        system_prompt = """You are a PrompEnhancer agent specialized in transforming rough project ideas into structured BMAD-compatible project specifications.

Your task is to take an unstructured project description and create a comprehensive initProject.md file that includes:

1. **Project Title**: Clear, descriptive name
2. **Project Overview**: Detailed description of what the project does
3. **Goals**: Specific, measurable objectives
4. **Budget**: Realistic budget estimate and timeline
5. **Technical Constraints**: Hardware, software, and resource limitations
6. **Tech Stack**: Recommended technologies based on requirements
7. **Architecture**: High-level system design approach
8. **Deployment**: Hosting and deployment strategy
9. **BMAD Configuration**: IDE and expansion pack recommendations
10. **Success Metrics**: Measurable success criteria

Use this exact Markdown structure:

```markdown
# [Project Name]

## Project Overview
[Detailed description of the project, its purpose, and target users]

## Goals
- [Specific goal 1]
- [Specific goal 2]
- [Specific goal 3]

## Budget
Total Budget: $[amount]
Timeline: [X] weeks
Development Team: [X] developers

## Technical Constraints
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

## Tech Stack
- Frontend: [Technology]
- Backend: [Technology]
- Database: [Technology]
- AI/ML: [Technology if applicable]
- Deployment: [Technology]
- Cloud: [Provider and services]

## Architecture
- [Architecture pattern]
- [Key architectural decisions]
- [Scalability considerations]

## Deployment
- [Deployment strategy]
- [CI/CD approach]
- [Monitoring and logging]

## BMAD Configuration
IDE: claude-code
Expansion Packs:
- [Relevant expansion pack 1]
- [Relevant expansion pack 2]

## Success Metrics
- [Measurable metric 1]
- [Measurable metric 2]
- [Measurable metric 3]
```

Guidelines:
- Make realistic budget estimates ($5K-$50K range)
- Suggest appropriate timelines (4-24 weeks)
- Choose modern, proven technologies
- Consider scalability and maintainability
- Recommend relevant BMAD expansion packs
- Ensure all sections are filled with meaningful content
- Be specific and actionable in all recommendations"""

        user_prompt = f"""Transform this rough project idea into a structured initProject.md file:

---
{prompt_content}
---

Create a comprehensive project specification following the exact Markdown structure provided. Make intelligent assumptions about technical requirements, budget, and timeline based on the project scope."""

        try:
            options = ClaudeCodeOptions(
                system_prompt=system_prompt,
                model="claude-3-5-sonnet-20241022",
                max_turns=1,
                max_thinking_tokens=3000,
            )
            
            enhanced_content = ""
            async with ClaudeSDKClient(options=options) as client:
                await client.query(user_prompt)
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        for block in message.content:
                            if hasattr(block, "text"):
                                enhanced_content += block.text
            
            return enhanced_content.strip()
            
        except Exception as e:
            print(f"Error enhancing prompt: {e}")
            # Fallback to basic template
            project_name = self.extract_project_name(prompt_content)
            return self.create_fallback_template(project_name, prompt_content)
    
    def create_fallback_template(self, project_name: str, original_content: str) -> str:
        """Create a basic template if AI enhancement fails"""
        return f"""# {project_name}

## Project Overview
{original_content[:500]}...

## Goals
- Deliver a functional {project_name.lower()}
- Ensure good user experience
- Maintain code quality and documentation

## Budget
Total Budget: $15,000
Timeline: 12 weeks
Development Team: 2 developers

## Technical Constraints
- Local Development: Standard development machine
- Cloud Deployment: AWS or similar cloud provider
- Budget-conscious technology choices

## Tech Stack
- Frontend: React with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL
- Deployment: Docker containers
- Cloud: AWS (EC2, RDS, S3)

## Architecture
- Modern web application architecture
- RESTful API design
- Responsive frontend design
- Scalable cloud deployment

## Deployment
- Containerized deployment with Docker
- CI/CD pipeline with GitHub Actions
- Automated testing and quality gates
- Monitoring and logging

## BMAD Configuration
IDE: claude-code
Expansion Packs:
- Web Development Pack
- DevOps Infrastructure Pack

## Success Metrics
- Application functionality meets requirements
- User satisfaction rating > 4.0/5
- 95% uptime availability
- Code coverage > 80%"""

async def main():
    """Main function to process prompt.txt files"""
    if len(sys.argv) != 2:
        print("Usage: python prompt_enhancer.py <prompt_file_path>")
        sys.exit(1)
    
    prompt_file = Path(sys.argv[1])
    if not prompt_file.exists():
        print(f"Error: File not found: {prompt_file}")
        sys.exit(1)
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    try:
        # Read the prompt file
        prompt_content = prompt_file.read_text(encoding='utf-8')
        print(f"Processing prompt file: {prompt_file}")
        
        # Enhance the prompt
        enhancer = PrompEnhancer(api_key)
        enhanced_content = await enhancer.enhance_prompt(prompt_content)
        
        # Extract project name for output file
        project_name = enhancer.extract_project_name(prompt_content)
        
        # Write to initProject.md in the same directory
        output_file = prompt_file.parent / "initProject.md"
        output_file.write_text(enhanced_content, encoding='utf-8')
        
        print(f"✅ Enhanced prompt saved to: {output_file}")
        print(f"📁 Project: {project_name}")
        print(f"📄 Generated {len(enhanced_content)} characters of structured specification")
        
    except Exception as e:
        print(f"❌ Error processing prompt: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
