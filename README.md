# Student Progress Tracker MCP Server

An MCP (Model Context Protocol) server that tracks student performance across topics and assessments, identifies learning gaps, and provides personalized recommendations.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MCP](https://img.shields.io/badge/MCP-1.26-green)
![Claude](https://img.shields.io/badge/Claude-Desktop-blueviolet)

## What It Does

Claude becomes an educational analytics assistant:

- **Track student performance** across courses and topics
- **Record assessment results** with question-level detail
- **Calculate mastery levels** using performance data
- **Identify learning gaps** and struggling students
- **Provide recommendations** for what to study next
- **Generate class analytics** for teachers

## Demo

Ask Claude things like:

- "Create a student named Alice in 9th grade"
- "Enroll Alice in Algebra I"
- "Record Alice's quiz result: 85 out of 100"
- "What are Alice's learning gaps?"
- "What should Alice focus on next?"
- "Show me class analytics for Algebra I"

## Tools

### Student Management
| Tool | Description |
|------|-------------|
| `create_student` | Create a new student record |
| `list_students` | List students, optionally by course |
| `get_student_profile` | Comprehensive profile with stats |

### Course Management
| Tool | Description |
|------|-------------|
| `create_course` | Create a course (links to Question Bank MCP) |
| `list_courses` | List all courses |
| `enroll_student` | Enroll a student in a course |
| `create_topic` | Add a topic for mastery tracking |
| `list_topics` | List topics in a course |

### Assessment & Results
| Tool | Description |
|------|-------------|
| `create_assessment` | Create a test, quiz, or homework |
| `record_assessment_result` | Record results with question-level data |

### Analytics & Recommendations
| Tool | Description |
|------|-------------|
| `get_topic_mastery` | See mastery levels by topic |
| `get_learning_gaps` | Find topics below threshold |
| `get_student_history` | Question-level performance history |
| `get_class_analytics` | Class-wide performance overview |
| `recommend_focus_areas` | Personalized study recommendations |

## Key Features

### Mastery Tracking
- Tracks correct/incorrect responses per topic
- Calculates mastery percentage (0-100%)
- Detects trends (improving, stable, declining)

### Learning Gap Analysis
- Identifies topics below mastery threshold
- Prioritizes by severity and trend
- Provides actionable recommendations

### Question-Level Telemetry
Records per-question data including:
- Correct/incorrect
- Time spent
- Difficulty level
- Bloom's taxonomy level

## Integration with Question Bank MCP

This server is designed to work with the [Question Bank MCP](https://github.com/woodstocksoftware/question-bank-mcp):
```
Question Bank MCP          Student Progress Tracker
┌─────────────────┐        ┌─────────────────────┐
│ • Questions     │        │ • Students          │
│ • Topics        │◄──────►│ • Enrollments       │
│ • Difficulty    │        │ • Assessment Results│
│ • Bloom's Level │        │ • Topic Mastery     │
└─────────────────┘        └─────────────────────┘
```

## Setup

### 1. Clone and Install
```bash
git clone https://github.com/woodstocksoftware/student-progress-tracker.git
cd student-progress-tracker

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

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

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. The student progress tools will be available.

## Project Structure
```
student-progress-tracker/
├── run_server.py              # MCP server entry point
├── src/
│   └── student_progress/
│       ├── server.py          # MCP tools
│       └── database.py        # SQLite database
├── data/
│   └── student_progress.db    # SQLite database (auto-created)
└── requirements.txt
```

## Data Model
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Students   │────►│  Enrollments │◄────│   Courses    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                         │
       │                                         │
       ▼                                         ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Results    │────►│  Assessments │     │    Topics    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                         │
       │                                         │
       ▼                                         ▼
┌──────────────┐                          ┌──────────────┐
│   Question   │─────────────────────────►│    Topic     │
│   History    │                          │   Mastery    │
└──────────────┘                          └──────────────┘
```

## Use Cases

### For Teachers
- Track individual student progress
- Identify struggling students early
- See class-wide performance patterns
- Adjust curriculum based on gaps

### For Students
- See personalized study recommendations
- Track progress over time
- Identify weak areas to focus on

### For Ed-Tech Platforms
- Foundation for adaptive learning systems
- Data source for learning analytics
- Integration point for curriculum builders

## Part of the Ed-Tech MCP Suite

| MCP Server | Purpose |
|------------|---------|
| [Question Bank](https://github.com/woodstocksoftware/question-bank-mcp) | Create and manage questions |
| **Student Progress** | Track performance and mastery |
| *Coming Soon* | Adaptive testing, curriculum builder |

## License

MIT

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)
