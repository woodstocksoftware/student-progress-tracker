#!/usr/bin/env python
"""Run the Student Progress Tracker MCP server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.student_progress.server import mcp

mcp.run(transport="stdio")
