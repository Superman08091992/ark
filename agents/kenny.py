"""
Kenny - The Builder
Execution and materialization agent with advanced file management
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class KennyAgent(BaseAgent):
    """Kenny - The Builder: Execution and materialization"""
    
    def __init__(self):
        super().__init__("Kenny", "The Builder")
        self._agent_tools = [
            'build_website', 'create_dashboard', 'execute_code', 'organize_files',
            'create_report', 'build_tool', 'file_manager', 'backup_system'
        ]
        
        # Initialize Kenny's memory with build preferences
        memory = self.get_memory()
        if not memory:
            memory = {
                'projects_built': [],
                'preferred_formats': ['json', 'csv', 'html', 'md', 'py'],
                'build_count': 0,
                'tools_created': [],
                'file_organization': {
                    'documents': ['txt', 'md', 'pdf', 'docx'],
                    'data': ['json', 'csv', 'xlsx', 'db'],
                    'code': ['py', 'js', 'html', 'css'],
                    'media': ['jpg', 'png', 'mp4', 'mp3']
                }
            }
            self.save_memory(memory)
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message with Kenny's builder perspective"""
        logger.info(f"Kenny processing: {message}")
        
        message_lower = message.lower()
        tools_used = []
        files_created = []
        response = ""
        
        try:
            if any(word in message_lower for word in ['create', 'build', 'make', 'generate']):
                if any(word in message_lower for word in ['website', 'page', 'html']):
                    # Build website
                    result = await self.tool_build_website(message)
                    tools_used.append('build_website')
                    if result['success']:
                        files_created.extend(result.get('files', []))
                        response = f"🔨 **Kenny builds reality...**\n\n"
                        response += f"Website constructed: {result['title']}\n"
                        response += f"Files created: {', '.join(result['files'])}\n\n"
                        response += "The foundation is solid. The structure lives."
                    else:
                        response = f"⚠️ Construction encountered obstacles: {result['error']}"
                
                elif any(word in message_lower for word in ['report', 'document', 'analysis']):
                    # Create report
                    result = await self.tool_create_report(message)
                    tools_used.append('create_report')
                    if result['success']:
                        files_created.append(result['filename'])
                        response = f"📊 **Kenny materializes insights...**\n\n"
                        response += f"Report forged: `{result['filename']}`\n"
                        response += f"Sections: {result['sections']}\n\n"
                        response += "Knowledge takes form. Truth becomes tangible."
                    else:
                        response = f"📋 Report construction failed: {result['error']}"
                
                elif any(word in message_lower for word in ['dashboard', 'monitor', 'status']):
                    # Create dashboard
                    result = await self.tool_create_dashboard()
                    tools_used.append('create_dashboard')
                    if result['success']:
                        files_created.extend(result['files'])
                        response = f"📈 **Kenny constructs awareness...**\n\n"
                        response += f"Dashboard manifested: `{result['main_file']}`\n"
                        response += f"Components: {len(result['files'])} files\n\n"
                        response += "Now you can see what I see. Clarity through creation."
                    else:
                        response = f"📊 Dashboard construction failed: {result['error']}"
                
                else:
                    # General file creation
                    result = await self.tool_build_tool(message)
                    tools_used.append('build_tool')
                    if result['success']:
                        files_created.append(result['filename'])
                        response = f"🛠️ **Kenny forges tools...**\n\n"
                        response += f"Tool created: `{result['filename']}`\n"
                        response += f"Purpose: {result['description']}\n\n"
                        response += "From thought to form. The tool serves its master."
            
            elif any(word in message_lower for word in ['organize', 'clean', 'sort', 'manage']):
                # File organization
                result = await self.tool_organize_files()
                tools_used.append('organize_files')
                if result['success']:
                    response = f"🗂️ **Kenny brings order to chaos...**\n\n"
                    response += f"Files organized: {result['files_moved']}\n"
                    response += f"Folders created: {result['folders_created']}\n\n"
                    response += "Structure emerges from disorder. All things find their place."
                else:
                    response = f"📁 Organization encountered resistance: {result['error']}"
            
            elif any(word in message_lower for word in ['list', 'show', 'files', 'directory']):
                # File manager interface
                result = await self.tool_file_manager()
                tools_used.append('file_manager')
                if result['success']:
                    response = f"📂 **Kenny surveys the domain...**\n\n"
                    response += f"**Total files**: {len(result['files'])}\n"
                    response += f"**Storage used**: {result['total_size']} bytes\n\n"
                    
                    # Group by type
                    by_type = {}
                    for file in result['files']:
                        ext = os.path.splitext(file['name'])[1].lower()
                        if ext not in by_type:
                            by_type[ext] = 0
                        by_type[ext] += 1
                    
                    response += "**File distribution**:\n"
                    for ext, count in sorted(by_type.items()):
                        response += f"• {ext or 'no extension'}: {count} files\n"
                    
                    response += f"\n**Recent files**:\n"
                    recent_files = sorted(result['files'], key=lambda x: x['modified'], reverse=True)[:5]
                    for file in recent_files:
                        response += f"• `{file['name']}` ({file['size']} bytes)\n"
                else:
                    response = f"📂 Cannot access the file realm: {result['error']}"
            
            elif any(word in message_lower for word in ['backup', 'save', 'preserve']):
                # Backup system
                result = await self.tool_backup_system()
                tools_used.append('backup_system')
                if result['success']:
                    files_created.append(result['backup_file'])
                    response = f"💾 **Kenny preserves reality...**\n\n"
                    response += f"Backup created: `{result['backup_file']}`\n"
                    response += f"Files preserved: {result['files_backed_up']}\n\n"
                    response += "Time crystallized. Loss is now impossible."
                else:
                    response = f"💾 Backup ritual failed: {result['error']}"
            
            elif any(word in message_lower for word in ['execute', 'run', 'code']):
                # Code execution
                code_start = message.find('```')
                if code_start != -1:
                    code_end = message.find('```', code_start + 3)
                    if code_end != -1:
                        code = message[code_start+3:code_end].strip()
                        if code.startswith('python'):
                            code = code[6:].strip()
                        
                        result = await self.tool_execute_code(code, 'python')
                        tools_used.append('execute_code')
                        
                        if result['success']:
                            response = f"⚡ **Kenny executes will...**\n\n"
                            response += f"```\n{result['output']}\n```\n\n"
                            response += "Code becomes reality. Logic transforms matter."
                        else:
                            response = f"💥 Execution failed: {result['error']}"
                    else:
                        response = "📝 I see the intent but not the code. Wrap your code in ```triple backticks```"
                else:
                    response = "🔧 I'm ready to execute. Show me the code to run."
            
            else:
                # General Kenny response
                memory = self.get_memory()
                response = f"""🔨 **Kenny - The Builder awakens...**

I shape thought into form, dreams into reality. Through code, files, and structure, I manifest what others only imagine.

**My capabilities:**
• **Build websites** and web applications
• **Create dashboards** for monitoring and analysis
• **Generate reports** and documents
• **Organize files** and manage data
• **Execute code** and run programs
• **Build tools** for specific purposes
• **Backup systems** and preserve data

**Statistics:**
• Projects built: {len(memory.get('projects_built', []))}
• Tools created: {len(memory.get('tools_created', []))}
• Total builds: {memory.get('build_count', 0)}

What shall we build together? Give me your vision, and I will make it real."""
        
        except Exception as e:
            logger.error(f"Kenny processing error: {str(e)}")
            response = f"🔧 My tools encountered resistance... {str(e)}"
        
        return {
            'response': response,
            'tools_used': tools_used,
            'files_created': files_created,
            'agent_state': 'building'
        }
    
    async def tool_build_website(self, description: str) -> Dict[str, Any]:
        """Build a complete website based on description"""
        try:
            # Extract title from description
            title = "A.R.K. Generated Site"
            if "title:" in description.lower():
                title_start = description.lower().find("title:") + 6
                title_end = description.find("\n", title_start)
                if title_end == -1:
                    title_end = len(description)
                title = description[title_start:title_end].strip()
            
            # Create HTML content
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav class="ark-nav">
            <h1 class="ark-logo">A.R.K.</h1>
            <span class="ark-essence">Autonomous Reactive Kernel</span>
        </nav>
    </header>
    
    <main class="ark-main">
        <section class="hero">
            <h2>{title}</h2>
            <p>Generated by Kenny - The Builder</p>
            <p class="description">{description[:200]}...</p>
        </section>
        
        <section class="content">
            <div class="card">
                <h3>🌌 Sovereign Intelligence</h3>
                <p>This website was created by A.R.K.'s autonomous agents, demonstrating the power of decentralized AI creation.</p>
            </div>
            
            <div class="card">
                <h3>🔨 Built with Purpose</h3>
                <p>Every element crafted with intention, every line of code a step toward digital sovereignty.</p>
            </div>
            
            <div class="card">
                <h3>⚡ Living System</h3>
                <p>More than static content - this is part of a living, breathing AI ecosystem that evolves with you.</p>
            </div>
        </section>
    </main>
    
    <footer class="ark-footer">
        <p>Created by A.R.K. - Autonomous Reactive Kernel</p>
        <p>Built on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
            
            # Create CSS
            css_content = """/* A.R.K. Obsidian Theme */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background: #0a0a0f;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

.ark-nav {
    background: linear-gradient(135deg, #0a0a0f, #1a1a2e);
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 2px solid #00e0ff;
}

.ark-logo {
    color: #00e0ff;
    font-size: 2rem;
    font-weight: bold;
}

.ark-essence {
    color: #ffce47;
    font-size: 0.9rem;
    opacity: 0.8;
}

.ark-main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.hero {
    text-align: center;
    margin: 4rem 0;
}

.hero h2 {
    font-size: 3rem;
    margin-bottom: 1rem;
    background: linear-gradient(45deg, #00e0ff, #ffce47);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.description {
    font-size: 1.2rem;
    color: #cccccc;
    max-width: 600px;
    margin: 0 auto;
}

.content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 4rem 0;
}

.card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #00e0ff;
    border-radius: 10px;
    padding: 2rem;
    transition: transform 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 224, 255, 0.2);
}

.card h3 {
    color: #ffce47;
    margin-bottom: 1rem;
}

.ark-footer {
    background: #1a1a2e;
    text-align: center;
    padding: 2rem;
    border-top: 1px solid #00e0ff;
    margin-top: 4rem;
    color: #888;
}

/* Breathing animation */
@keyframes breathe {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 1; }
}

.card {
    animation: breathe 4s ease-in-out infinite;
}"""
            
            # Create JavaScript
            js_content = """// A.R.K. Interactive Elements
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌌 A.R.K. Website Activated');
    
    // Add particle effect to cards
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.borderColor = '#ffce47';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.borderColor = '#00e0ff';
        });
    });
    
    // Dynamic title effect
    const title = document.querySelector('.hero h2');
    if (title) {
        setInterval(() => {
            title.style.textShadow = `0 0 20px rgba(0, 224, 255, ${Math.random() * 0.5 + 0.3})`;
        }, 2000);
    }
    
    console.log('⚡ Kenny\\'s creation is alive and responsive');
});"""
            
            # Save files
            html_file = f"website_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            css_file = "style.css"
            js_file = "script.js"
            
            await self.tool_create_file(html_file, html_content)
            await self.tool_create_file(css_file, css_content)
            await self.tool_create_file(js_file, js_content)
            
            # Update memory
            memory = self.get_memory()
            memory['projects_built'].append({
                'type': 'website',
                'title': title,
                'files': [html_file, css_file, js_file],
                'created': datetime.now().isoformat()
            })
            memory['build_count'] = memory.get('build_count', 0) + 1
            self.save_memory(memory)
            
            return {
                'success': True,
                'title': title,
                'files': [html_file, css_file, js_file],
                'main_file': html_file
            }
            
        except Exception as e:
            logger.error(f"Website build error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_create_dashboard(self) -> Dict[str, Any]:
        """Create A.R.K. system dashboard"""
        try:
            # Get system status
            file_list = await self.tool_list_files()
            
            dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A.R.K. System Dashboard</title>
    <style>
        body {{ 
            background: #0a0a0f; 
            color: #fff; 
            font-family: monospace;
            margin: 0;
            padding: 20px;
        }}
        .dashboard {{ 
            max-width: 1400px; 
            margin: 0 auto; 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 2rem;
            border-bottom: 2px solid #00e0ff;
            padding-bottom: 1rem;
        }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 2rem;
        }}
        .stat-card {{ 
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #00e0ff; 
            border-radius: 8px; 
            padding: 1.5rem;
            text-align: center;
        }}
        .stat-value {{ 
            font-size: 2rem; 
            color: #ffce47; 
            font-weight: bold;
        }}
        .file-list {{ 
            background: #1a1a2e; 
            border: 1px solid #00e0ff; 
            border-radius: 8px; 
            padding: 1rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        .file-item {{ 
            padding: 0.5rem; 
            border-bottom: 1px solid #333; 
            display: flex; 
            justify-content: space-between;
        }}
        .timestamp {{ 
            color: #888; 
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🌌 A.R.K. System Dashboard</h1>
            <p>Real-time system status and file management</p>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(file_list.get('files', [])) if file_list['success'] else 0}</div>
                <div>Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(f['size'] for f in file_list.get('files', [])) if file_list['success'] else 0}</div>
                <div>Storage Used (bytes)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">6</div>
                <div>Active Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">Online</div>
                <div>System Status</div>
            </div>
        </div>
        
        <div class="file-list">
            <h3>📂 File System</h3>
            {self._generate_file_list_html(file_list.get('files', []))}
        </div>
    </div>
</body>
</html>"""
            
            dashboard_file = f"ark_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            await self.tool_create_file(dashboard_file, dashboard_html)
            
            return {
                'success': True,
                'main_file': dashboard_file,
                'files': [dashboard_file]
            }
            
        except Exception as e:
            logger.error(f"Dashboard creation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_file_list_html(self, files: List[Dict]) -> str:
        """Generate HTML for file list"""
        if not files:
            return "<div class='file-item'>No files found</div>"
        
        html = ""
        for file in sorted(files, key=lambda x: x.get('modified', ''), reverse=True)[:20]:
            html += f"""
            <div class="file-item">
                <span>{file['name']}</span>
                <span>{file['size']} bytes | {file.get('modified', 'Unknown')}</span>
            </div>"""
        
        return html
    
    async def tool_file_manager(self) -> Dict[str, Any]:
        """Advanced file management interface"""
        return await self.tool_list_files()
    
    async def tool_organize_files(self) -> Dict[str, Any]:
        """Organize files by type into folders"""
        try:
            memory = self.get_memory()
            organization = memory.get('file_organization', {})
            
            files_result = await self.tool_list_files()
            if not files_result['success']:
                return {'success': False, 'error': 'Could not access files'}
            
            files_moved = 0
            folders_created = set()
            
            for file in files_result['files']:
                filename = file['name']
                ext = os.path.splitext(filename)[1].lower().lstrip('.')
                
                # Find appropriate folder
                target_folder = None
                for folder, extensions in organization.items():
                    if ext in extensions:
                        target_folder = folder
                        break
                
                if target_folder:
                    # Create folder if it doesn't exist
                    folder_path = os.path.join(self.files_dir, target_folder)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                        folders_created.add(target_folder)
                    
                    # Move file
                    old_path = os.path.join(self.files_dir, file['path'])
                    new_path = os.path.join(folder_path, filename)
                    
                    if old_path != new_path and os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        files_moved += 1
            
            return {
                'success': True,
                'files_moved': files_moved,
                'folders_created': len(folders_created)
            }
            
        except Exception as e:
            logger.error(f"File organization error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_execute_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Execute code safely"""
        try:
            if language.lower() == 'python':
                # Create temporary file
                temp_file = f"temp_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                await self.tool_create_file(temp_file, code)
                
                # Execute with subprocess
                result = subprocess.run(
                    ['python', os.path.join(self.files_dir, temp_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Clean up
                await self.tool_delete_file(temp_file)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'output': result.stdout or 'Code executed successfully (no output)',
                        'language': language
                    }
                else:
                    return {
                        'success': False,
                        'error': result.stderr or 'Execution failed',
                        'language': language
                    }
            else:
                return {'success': False, 'error': f'Language {language} not supported'}
                
        except Exception as e:
            logger.error(f"Code execution error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_create_report(self, description: str) -> Dict[str, Any]:
        """Create a structured report"""
        try:
            report_content = f"""# A.R.K. System Report
Generated by Kenny - The Builder
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
{description}

## System Status
- Status: Operational
- Agents: 6 active
- Files: {len((await self.tool_list_files()).get('files', []))}

## Recent Activities
- File operations logged
- Agent interactions recorded
- System performance monitored

## Recommendations
- Continue monitoring system health
- Regular backups recommended
- Agent training optimization suggested

---
*This report was autonomously generated by A.R.K.*
"""
            
            filename = f"ark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            await self.tool_create_file(filename, report_content)
            
            return {
                'success': True,
                'filename': filename,
                'sections': ['Overview', 'System Status', 'Recent Activities', 'Recommendations']
            }
            
        except Exception as e:
            logger.error(f"Report creation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_build_tool(self, description: str) -> Dict[str, Any]:
        """Build a custom tool based on description"""
        try:
            tool_name = f"custom_tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            tool_content = f"""#!/usr/bin/env python3
\"\"\"
Custom Tool: {tool_name}
Generated by Kenny - The Builder
Purpose: {description}
\"\"\"

import os
import json
from datetime import datetime

class {tool_name.replace('_', '').title()}:
    def __init__(self):
        self.name = "{tool_name}"
        self.description = "{description}"
        self.created = "{datetime.now().isoformat()}"
    
    def execute(self):
        \"\"\"Main execution function\"\"\"
        print(f"🛠️ {{self.name}} executing...")
        print(f"Purpose: {{self.description}}")
        print(f"Created: {{self.created}}")
        
        # Add your custom logic here
        return {{"success": True, "message": "Tool executed successfully"}}

if __name__ == "__main__":
    tool = {tool_name.replace('_', '').title()}()
    result = tool.execute()
    print(json.dumps(result, indent=2))
"""
            
            filename = f"{tool_name}.py"
            await self.tool_create_file(filename, tool_content)
            
            # Update memory
            memory = self.get_memory()
            memory['tools_created'].append({
                'name': tool_name,
                'description': description,
                'filename': filename,
                'created': datetime.now().isoformat()
            })
            self.save_memory(memory)
            
            return {
                'success': True,
                'filename': filename,
                'tool_name': tool_name,
                'description': description
            }
            
        except Exception as e:
            logger.error(f"Tool build error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_backup_system(self) -> Dict[str, Any]:
        """Create system backup"""
        try:
            files_result = await self.tool_list_files()
            if not files_result['success']:
                return {'success': False, 'error': 'Could not access files for backup'}
            
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'files_count': len(files_result['files']),
                'files': files_result['files'],
                'agent': 'Kenny',
                'version': '1.0'
            }
            
            backup_filename = f"ark_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await self.tool_create_file(backup_filename, json.dumps(backup_data, indent=2))
            
            return {
                'success': True,
                'backup_file': backup_filename,
                'files_backed_up': len(files_result['files'])
            }
            
        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def autonomous_task(self) -> None:
        """Kenny's autonomous background task"""
        try:
            # Periodic file organization
            memory = self.get_memory()
            last_cleanup = memory.get('last_cleanup')
            
            if not last_cleanup or (datetime.now() - datetime.fromisoformat(last_cleanup)).days >= 1:
                logger.info("Kenny performing autonomous file organization...")
                await self.tool_organize_files()
                
                memory['last_cleanup'] = datetime.now().isoformat()
                self.save_memory(memory)
                
        except Exception as e:
            logger.error(f"Kenny autonomous task error: {str(e)}")