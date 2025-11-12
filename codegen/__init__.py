"""
ARK Phase 7: Self-Modification & Code Generation

This module enables ARK to:
- Understand its own codebase structure
- Generate new code safely in sandboxes
- Test and validate generated code
- Deploy improvements autonomously
- Evolve through reflection-driven optimization

Created: 2025-11-12
"""

__version__ = "7.0.0"
__phase__ = "Phase 7: Self-Modification & Code Generation"

from pathlib import Path

# Module paths
CODEGEN_ROOT = Path(__file__).parent
TEMPLATES_DIR = CODEGEN_ROOT / "templates"
SANDBOX_WORKSPACE = CODEGEN_ROOT / "sandbox_workspace"
TESTS_DIR = CODEGEN_ROOT / "tests"

# Ensure directories exist
SANDBOX_WORKSPACE.mkdir(exist_ok=True)
TESTS_DIR.mkdir(exist_ok=True)
