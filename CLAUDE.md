# Student Progress Tracker MCP Server

## Tech Stack

- **Language:** Python 3.12
- **Framework:** FastMCP (Model Context Protocol SDK)
- **Database:** SQLite3 (local file: `data/student_progress.db`)
- **Dependencies:** `mcp>=1.0.0`, `python-dateutil>=2.8.0`

## Project Structure

```
student-progress-tracker/
├── run_server.py                  # MCP server entry point (stdio transport)
├── src/
│   └── student_progress/
│       ├── __init__.py
│       ├── __main__.py            # Alternate entry: python -m src.student_progress
│       ├── server.py              # MCP tool definitions (15 tools)
│       └── database.py            # SQLite schema + queries (10 tables)
├── tests/
│   └── test_database.py           # Database unit tests
├── data/
│   └── student_progress.db        # SQLite database (auto-created, gitignored)
├── requirements.txt
└── pyproject.toml                 # Linting config (ruff)
```

## Running the Server

```bash
# Activate virtualenv
source venv/bin/activate

# Run directly
python run_server.py

# Or as a module
python -m src.student_progress
```

## Connecting to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "student-progress": {
      "command": "/path/to/student-progress-tracker/venv/bin/python",
      "args": ["/path/to/student-progress-tracker/run_server.py"]
    }
  }
}
```

## Connecting to Claude Code

Add to `.claude/settings.json` or project's `.mcp.json`:

```json
{
  "mcpServers": {
    "student-progress": {
      "command": "/path/to/student-progress-tracker/venv/bin/python",
      "args": ["/path/to/student-progress-tracker/run_server.py"]
    }
  }
}
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

## MCP Tools (15 total)

### Student Management
- `create_student(name, email?, grade_level?)` - Create student record
- `list_students(course_id?)` - List students, optionally by course
- `get_student_profile(student_id)` - Full profile with stats and recent assessments

### Course Management
- `create_course(name, subject, grade_level?, question_bank_id?)` - Create course
- `list_courses()` - List all courses with student counts
- `enroll_student(student_id, course_id)` - Enroll student in course
- `create_topic(course_id, name, weight?)` - Add topic for mastery tracking
- `list_topics(course_id)` - List topics in a course

### Assessment & Results
- `create_assessment(course_id, name, assessment_type, total_points, total_questions, time_limit_minutes?)` - Create test/quiz/homework/practice
- `record_assessment_result(student_id, assessment_id, points_earned, points_possible, time_spent_minutes?, question_results?)` - Record results with optional question-level data

### Analytics & Recommendations
- `get_topic_mastery(student_id, course_id?)` - Mastery levels with trend indicators
- `get_learning_gaps(student_id, threshold?)` - Topics below mastery threshold
- `get_student_history(student_id, topic_id?, limit?)` - Question-level performance history
- `get_class_analytics(course_id)` - Class-wide performance and grade distribution
- `recommend_focus_areas(student_id)` - Prioritized study recommendations

## Data Model

### Core Entities
- **students** - id, name, email, grade_level
- **courses** - id, name, subject, grade_level, question_bank_id (links to Question Bank MCP)
- **enrollments** - student_id + course_id composite key, status (active/completed/dropped)
- **topics** - id, course_id, name, parent_id (hierarchical), weight

### Assessment Data
- **assessments** - id, course_id, name, type, total_points, total_questions, time_limit
- **assessment_topics** - links assessments to topics with question/point counts
- **assessment_results** - student scores with JSON question_results

### Analytics Data
- **topic_mastery** - cached mastery level (0-1), questions attempted/correct, trend
- **question_history** - per-question correctness, time, difficulty, Bloom's level

## Architecture Notes

- All tool responses are markdown-formatted strings with emoji indicators
- Entity IDs use UUID hex prefixed by type: `stu-`, `course-`, `topic-`, `assess-`, `result-`
- Database auto-initializes schema on first import
- Topic mastery is recalculated when assessment results with question_results are recorded
- Trend detection compares recent accuracy to overall mastery (>10% delta = improving/declining)
- Designed for composition with [Question Bank MCP](https://github.com/woodstocksoftware/question-bank-mcp)

## Code Conventions

- Type hints on all function signatures
- Docstrings on all public functions
- Database functions return dicts (via `sqlite3.Row`)
- Server functions return formatted markdown strings
- Linting: ruff (configured in pyproject.toml)
