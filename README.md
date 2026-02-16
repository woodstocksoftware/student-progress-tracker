# Student Progress Tracker MCP Server

MCP server for AI-powered student progress tracking and learning analytics. Connects to Claude Desktop or Claude Code to give AI assistants the ability to manage students, track assessments, calculate mastery levels, identify learning gaps, and recommend focus areas.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard that lets AI assistants like Claude connect to external tools and data sources. This server exposes student progress tracking as MCP tools that Claude can call directly during conversations.

## Features

- **Student profiles** - Create and manage student records with grade levels
- **Course enrollment** - Organize students into courses with topics
- **Assessment tracking** - Record tests, quizzes, homework, and practice results
- **Mastery levels** - Automatic topic mastery calculation from question-level data
- **Learning gap analysis** - Identify topics below threshold with severity ratings
- **Focus recommendations** - Prioritized study suggestions based on trends
- **Class analytics** - Grade distribution and topic performance across a class
- **Question-level telemetry** - Track correctness, time, difficulty, and Bloom's level per question

## Quick Start

### Install

```bash
git clone https://github.com/woodstocksoftware/student-progress-tracker.git
cd student-progress-tracker
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "student-progress": {
      "command": "/absolute/path/to/student-progress-tracker/venv/bin/python",
      "args": ["/absolute/path/to/student-progress-tracker/run_server.py"]
    }
  }
}
```

Restart Claude Desktop. The tools will appear automatically.

### Configure Claude Code

Add to your project's `.mcp.json` or global settings:

```json
{
  "mcpServers": {
    "student-progress": {
      "command": "/absolute/path/to/student-progress-tracker/venv/bin/python",
      "args": ["/absolute/path/to/student-progress-tracker/run_server.py"]
    }
  }
}
```

### Try It

```
You: Create a student named Alice in 9th grade
You: Create a course called Algebra I in Mathematics
You: Enroll Alice in Algebra I
You: Create a topic "Linear Equations" in the Algebra course
You: Record Alice's quiz: 85 out of 100
You: What are Alice's learning gaps?
You: What should Alice focus on next?
```

## Tool Reference

### Student Management

#### `create_student`
Create a new student record.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Student's full name |
| `email` | string | No | Email address |
| `grade_level` | string | No | e.g., "9th Grade", "College Freshman" |

```
Create a student named Alice Johnson, email alice@school.edu, in 9th grade
```

#### `list_students`
List all students, optionally filtered by course.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | No | Filter by course enrollment |

#### `get_student_profile`
Comprehensive profile with courses, statistics, and recent assessments.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |

### Course Management

#### `create_course`
Create a new course.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | e.g., "Algebra I", "Biology 101" |
| `subject` | string | Yes | e.g., "Mathematics", "Science" |
| `grade_level` | string | No | Target grade level |
| `question_bank_id` | string | No | Link to Question Bank MCP |

#### `list_courses`
List all courses with enrolled student counts.

#### `enroll_student`
Enroll a student in a course.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |
| `course_id` | string | Yes | The course ID |

#### `create_topic`
Add a topic within a course for mastery tracking.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | The course ID |
| `name` | string | Yes | e.g., "Linear Equations" |
| `weight` | float | No | Importance weight (default 1.0) |

#### `list_topics`
List all topics in a course.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | The course ID |

### Assessment & Results

#### `create_assessment`
Create a test, quiz, homework, or practice assessment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | The course ID |
| `name` | string | Yes | e.g., "Chapter 3 Quiz" |
| `assessment_type` | string | Yes | `test`, `quiz`, `homework`, or `practice` |
| `total_points` | float | Yes | Total points possible |
| `total_questions` | int | Yes | Number of questions |
| `time_limit_minutes` | int | No | Time limit in minutes |

#### `record_assessment_result`
Record a student's assessment result with optional question-level data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |
| `assessment_id` | string | Yes | The assessment ID |
| `points_earned` | float | Yes | Points earned |
| `points_possible` | float | Yes | Total points possible |
| `time_spent_minutes` | int | No | Time spent in minutes |
| `question_results` | list | No | Per-question data (see below) |

Each item in `question_results`:
```json
{
  "question_id": "q1",
  "topic_id": "topic-abc123",
  "is_correct": true,
  "time_spent_seconds": 45,
  "difficulty": 0.5,
  "bloom_level": "application"
}
```

### Analytics & Recommendations

#### `get_topic_mastery`
View mastery levels by topic with trend indicators.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |
| `course_id` | string | No | Filter by course |

#### `get_learning_gaps`
Identify topics below a mastery threshold.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |
| `threshold` | float | No | Mastery threshold % (default 70) |

#### `get_student_history`
Question-level performance history.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |
| `topic_id` | string | No | Filter by topic |
| `limit` | int | No | Max records (default 20) |

#### `get_class_analytics`
Class-wide performance overview with grade distribution and topic analysis.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `course_id` | string | Yes | The course ID |

#### `recommend_focus_areas`
Personalized study recommendations prioritized by trend and mastery level.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `student_id` | string | Yes | The student ID |

## Data Model

```
Students ──── Enrollments ──── Courses ──── Topics
   │                              │           │
   │                              │           │
   └──── Assessment Results ──── Assessments  │
              │                               │
              │                               │
         Question History ──── Topic Mastery ─┘
```

### Tables

| Table | Purpose |
|-------|---------|
| `students` | Student records (id, name, email, grade_level) |
| `courses` | Courses with subject and optional question bank link |
| `enrollments` | Student-course relationships with status |
| `topics` | Hierarchical topics within courses with weights |
| `assessments` | Tests, quizzes, homework, practice |
| `assessment_topics` | Which topics an assessment covers |
| `assessment_results` | Student scores with JSON question-level data |
| `topic_mastery` | Cached mastery level (0-1), trend, question stats |
| `question_history` | Per-question correctness, timing, difficulty, Bloom's level |

### Mastery Calculation

Mastery is calculated as `questions_correct / questions_attempted` per topic. Trends are detected by comparing recent accuracy to overall mastery:

- **Improving** - Recent accuracy > mastery + 10%
- **Stable** - Within 10% of mastery
- **Declining** - Recent accuracy < mastery - 10%

## Usage Examples

### Track a Student's Math Mastery Over Time

```
1. Create a student and course
2. Add topics: Linear Equations, Quadratic Equations, Polynomials
3. Record quiz results with question_results linking to topics
4. View mastery: "Show me Alice's topic mastery for Algebra I"
5. Check gaps: "What are Alice's learning gaps?"
6. Get recommendations: "What should Alice focus on next?"
```

### Monitor a Class

```
1. Create a course with multiple enrolled students
2. Record assessment results for each student
3. View analytics: "Show class analytics for Algebra I"
4. See grade distribution and struggling topic areas
```

## Architecture

```
Claude (Desktop/Code)
    │
    │ MCP Protocol (stdio)
    │
    ▼
┌─────────────────────────────┐
│  server.py (FastMCP)        │
│  15 tools with @mcp.tool()  │
│  Markdown response format   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  database.py (SQLite)       │
│  10 tables, auto-init       │
│  Foreign keys + indexes     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  data/student_progress.db   │
│  Local file (gitignored)    │
└─────────────────────────────┘
```

Key design decisions:
- **FastMCP** decorators for tool registration with auto-generated JSON schemas
- **stdio transport** for communication with Claude
- **SQLite** for zero-config local persistence
- **Markdown responses** with emoji indicators for readability in chat
- **UUID-prefixed IDs** (`stu-`, `course-`, `topic-`, `assess-`, `result-`) for clarity
- **JSON question_results** for flexible per-question data storage

## Integration with Question Bank MCP

Designed to compose with [Question Bank MCP](https://github.com/woodstocksoftware/question-bank-mcp):

```
Question Bank MCP              Student Progress Tracker
┌───────────────────┐          ┌───────────────────────┐
│ Questions         │          │ Students              │
│ Topics            │◄────────►│ Enrollments           │
│ Difficulty levels │          │ Assessment Results    │
│ Bloom's taxonomy  │          │ Topic Mastery         │
└───────────────────┘          └───────────────────────┘
```

Link them via `question_bank_id` when creating a course.

## Testing

```bash
source venv/bin/activate
pip install pytest
pytest tests/ -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes with type hints and docstrings
4. Run linting: `ruff check src/`
5. Run tests: `pytest tests/ -v`
6. Commit and open a pull request

## License

MIT

---

Part of the **Ed-Tech MCP Suite** by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)

| MCP Server | Purpose |
|------------|---------|
| [Question Bank](https://github.com/woodstocksoftware/question-bank-mcp) | Create and manage questions |
| **Student Progress** | Track performance and mastery |
