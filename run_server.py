#!/usr/bin/env python
"""Run the Student Progress Tracker MCP server."""
import sys
sys.path.insert(0, '/Users/james/projects/student-progress-tracker')

from src.student_progress.server import mcp
mcp.run(transport="stdio")
