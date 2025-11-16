#!/usr/bin/env python3
"""
AI CLI Launcher
===============

Launcher script for the AI testing CLI. Run this from the project root.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path so ai can be imported as a module
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the CLI as a module
from ai.cli import main

if __name__ == '__main__':
    main()
