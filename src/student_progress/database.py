"""
Student Progress Tracker database.
Tracks student performance across topics and assessments.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "student_progress.db"


def get_connection():
    """Get database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize database with schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- Students
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            grade_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Courses (links to question banks)
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade_level TEXT,
            question_bank_id TEXT,  -- Links to question-bank-mcp
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Student enrollments
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',  -- active, completed, dropped
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        
        -- Topics (mirrored from question bank for tracking)
        CREATE TABLE IF NOT EXISTS topics (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_id TEXT,
            weight REAL DEFAULT 1.0,  -- Importance weight for overall grade
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        
        -- Assessments (tests, quizzes, homework)
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            name TEXT NOT NULL,
            assessment_type TEXT NOT NULL,  -- test, quiz, homework, practice
            total_points REAL NOT NULL,
            total_questions INTEGER NOT NULL,
            administered_at TEXT,
            time_limit_seconds INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        
        -- Assessment topic coverage
        CREATE TABLE IF NOT EXISTS assessment_topics (
            assessment_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            question_count INTEGER DEFAULT 0,
            points REAL DEFAULT 0,
            PRIMARY KEY (assessment_id, topic_id),
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
        
        -- Individual student assessment results
        CREATE TABLE IF NOT EXISTS assessment_results (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            assessment_id TEXT NOT NULL,
            
            -- Overall scores
            score REAL NOT NULL,
            points_earned REAL NOT NULL,
            points_possible REAL NOT NULL,
            percentage REAL NOT NULL,
            
            -- Timing
            started_at TEXT,
            completed_at TEXT,
            time_spent_seconds INTEGER,
            
            -- Question-level data (JSON)
            question_results TEXT,  -- JSON array of per-question data
            
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
            UNIQUE(student_id, assessment_id)
        );
        
        -- Topic mastery tracking (calculated/cached)
        CREATE TABLE IF NOT EXISTS topic_mastery (
            student_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            
            -- Mastery metrics
            mastery_level REAL DEFAULT 0,  -- 0.0 to 1.0
            questions_attempted INTEGER DEFAULT 0,
            questions_correct INTEGER DEFAULT 0,
            
            -- Trend data
            recent_accuracy REAL,  -- Last 5 attempts
            trend TEXT,  -- improving, stable, declining
            
            -- Timestamps
            first_attempt_at TEXT,
            last_attempt_at TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY (student_id, topic_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
        
        -- Detailed question-level history for analytics
        CREATE TABLE IF NOT EXISTS question_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            question_id TEXT NOT NULL,  -- Links to question-bank-mcp
            topic_id TEXT,
            assessment_result_id TEXT,
            
            -- Response data
            is_correct INTEGER NOT NULL,  -- 0 or 1
            time_spent_seconds INTEGER,
            attempts INTEGER DEFAULT 1,
            
            -- Question metadata at time of attempt
            difficulty REAL,
            bloom_level TEXT,
            
            attempted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (assessment_result_id) REFERENCES assessment_results(id) ON DELETE CASCADE
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_results_student ON assessment_results(student_id);
        CREATE INDEX IF NOT EXISTS idx_results_assessment ON assessment_results(assessment_id);
        CREATE INDEX IF NOT EXISTS idx_mastery_student ON topic_mastery(student_id);
        CREATE INDEX IF NOT EXISTS idx_history_student ON question_history(student_id);
        CREATE INDEX IF NOT EXISTS idx_history_topic ON question_history(topic_id);
    """)
    
    conn.commit()
    conn.close()


# Initialize on import
init_database()


# ============================================================
# STUDENT OPERATIONS
# ============================================================

def create_student(student_id: str, name: str, email: str = None, 
                   grade_level: str = None) -> dict:
    """Create a new student."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO students (id, name, email, grade_level)
        VALUES (?, ?, ?, ?)
    """, (student_id, name, email, grade_level))
    
    conn.commit()
    conn.close()
    
    return {
        "id": student_id,
        "name": name,
        "email": email,
        "grade_level": grade_level
    }


def get_student(student_id: str) -> Optional[dict]:
    """Get student by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def list_students(course_id: str = None) -> list:
    """List students, optionally filtered by course enrollment."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if course_id:
        cursor.execute("""
            SELECT s.* FROM students s
            JOIN enrollments e ON e.student_id = s.id
            WHERE e.course_id = ? AND e.status = 'active'
            ORDER BY s.name
        """, (course_id,))
    else:
        cursor.execute("SELECT * FROM students ORDER BY name")
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# COURSE OPERATIONS
# ============================================================

def create_course(course_id: str, name: str, subject: str,
                  grade_level: str = None, question_bank_id: str = None) -> dict:
    """Create a new course."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO courses (id, name, subject, grade_level, question_bank_id)
        VALUES (?, ?, ?, ?, ?)
    """, (course_id, name, subject, grade_level, question_bank_id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": course_id,
        "name": name,
        "subject": subject,
        "grade_level": grade_level,
        "question_bank_id": question_bank_id
    }


def get_course(course_id: str) -> Optional[dict]:
    """Get course by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def list_courses() -> list:
    """List all courses."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, COUNT(DISTINCT e.student_id) as student_count
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'active'
        GROUP BY c.id
        ORDER BY c.name
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def enroll_student(student_id: str, course_id: str) -> bool:
    """Enroll a student in a course."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO enrollments (student_id, course_id)
            VALUES (?, ?)
        """, (student_id, course_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ============================================================
# TOPIC OPERATIONS
# ============================================================

def create_topic(topic_id: str, course_id: str, name: str,
                 parent_id: str = None, weight: float = 1.0) -> dict:
    """Create a topic for a course."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO topics (id, course_id, name, parent_id, weight)
        VALUES (?, ?, ?, ?, ?)
    """, (topic_id, course_id, name, parent_id, weight))
    
    conn.commit()
    conn.close()
    
    return {"id": topic_id, "course_id": course_id, "name": name, 
            "parent_id": parent_id, "weight": weight}


def list_topics(course_id: str) -> list:
    """List topics for a course."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM topics WHERE course_id = ? ORDER BY name
    """, (course_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# ASSESSMENT OPERATIONS
# ============================================================

def create_assessment(assessment_id: str, course_id: str, name: str,
                      assessment_type: str, total_points: float,
                      total_questions: int, time_limit_seconds: int = None) -> dict:
    """Create an assessment."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO assessments (id, course_id, name, assessment_type, 
                                 total_points, total_questions, time_limit_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (assessment_id, course_id, name, assessment_type, 
          total_points, total_questions, time_limit_seconds))
    
    conn.commit()
    conn.close()
    
    return {
        "id": assessment_id,
        "course_id": course_id,
        "name": name,
        "assessment_type": assessment_type,
        "total_points": total_points,
        "total_questions": total_questions
    }


def get_assessment(assessment_id: str) -> Optional[dict]:
    """Get assessment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


# ============================================================
# RESULT RECORDING
# ============================================================

def record_assessment_result(
    result_id: str,
    student_id: str,
    assessment_id: str,
    points_earned: float,
    points_possible: float,
    time_spent_seconds: int = None,
    question_results: list = None
) -> dict:
    """Record a student's assessment result."""
    conn = get_connection()
    cursor = conn.cursor()
    
    percentage = (points_earned / points_possible * 100) if points_possible > 0 else 0
    
    cursor.execute("""
        INSERT INTO assessment_results 
        (id, student_id, assessment_id, score, points_earned, points_possible,
         percentage, time_spent_seconds, question_results, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (result_id, student_id, assessment_id, points_earned, points_earned,
          points_possible, percentage, time_spent_seconds,
          json.dumps(question_results) if question_results else None,
          datetime.now().isoformat()))
    
    # Update topic mastery based on question results
    if question_results:
        _update_topic_mastery(cursor, student_id, question_results, result_id)
    
    conn.commit()
    conn.close()
    
    return {
        "id": result_id,
        "student_id": student_id,
        "assessment_id": assessment_id,
        "points_earned": points_earned,
        "points_possible": points_possible,
        "percentage": percentage
    }


def _update_topic_mastery(cursor, student_id: str, question_results: list, result_id: str):
    """Update topic mastery based on question results."""
    # Group results by topic
    topic_stats = {}
    
    for qr in question_results:
        topic_id = qr.get('topic_id')
        if not topic_id:
            continue
            
        if topic_id not in topic_stats:
            topic_stats[topic_id] = {'correct': 0, 'total': 0}
        
        topic_stats[topic_id]['total'] += 1
        if qr.get('is_correct'):
            topic_stats[topic_id]['correct'] += 1
        
        # Record question history
        cursor.execute("""
            INSERT INTO question_history 
            (student_id, question_id, topic_id, assessment_result_id,
             is_correct, time_spent_seconds, difficulty, bloom_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, qr.get('question_id'), topic_id, result_id,
              1 if qr.get('is_correct') else 0, qr.get('time_spent_seconds'),
              qr.get('difficulty'), qr.get('bloom_level')))
    
    # Update mastery for each topic
    now = datetime.now().isoformat()
    
    for topic_id, stats in topic_stats.items():
        # Get existing mastery record
        cursor.execute("""
            SELECT * FROM topic_mastery 
            WHERE student_id = ? AND topic_id = ?
        """, (student_id, topic_id))
        
        existing = cursor.fetchone()
        
        if existing:
            new_attempted = existing['questions_attempted'] + stats['total']
            new_correct = existing['questions_correct'] + stats['correct']
            new_mastery = new_correct / new_attempted if new_attempted > 0 else 0
            
            # Calculate trend based on recent vs overall
            recent_accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            if recent_accuracy > existing['mastery_level'] + 0.1:
                trend = 'improving'
            elif recent_accuracy < existing['mastery_level'] - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
            
            cursor.execute("""
                UPDATE topic_mastery SET
                    mastery_level = ?,
                    questions_attempted = ?,
                    questions_correct = ?,
                    recent_accuracy = ?,
                    trend = ?,
                    last_attempt_at = ?,
                    updated_at = ?
                WHERE student_id = ? AND topic_id = ?
            """, (new_mastery, new_attempted, new_correct, recent_accuracy,
                  trend, now, now, student_id, topic_id))
        else:
            mastery = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            cursor.execute("""
                INSERT INTO topic_mastery 
                (student_id, topic_id, mastery_level, questions_attempted,
                 questions_correct, recent_accuracy, trend, first_attempt_at, 
                 last_attempt_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, topic_id, mastery, stats['total'], stats['correct'],
                  mastery, 'stable', now, now, now))


# ============================================================
# ANALYTICS QUERIES
# ============================================================

def get_student_profile(student_id: str) -> Optional[dict]:
    """Get comprehensive student profile with performance data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Basic info
    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return None
    
    profile = dict(student)
    
    # Enrolled courses
    cursor.execute("""
        SELECT c.*, e.enrolled_at, e.status
        FROM courses c
        JOIN enrollments e ON e.course_id = c.id
        WHERE e.student_id = ?
    """, (student_id,))
    profile['courses'] = [dict(row) for row in cursor.fetchall()]
    
    # Overall statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assessments,
            AVG(percentage) as avg_percentage,
            SUM(points_earned) as total_points_earned,
            SUM(points_possible) as total_points_possible,
            SUM(time_spent_seconds) as total_time_spent
        FROM assessment_results
        WHERE student_id = ?
    """, (student_id,))
    stats = dict(cursor.fetchone())
    profile['statistics'] = stats
    
    # Recent assessments
    cursor.execute("""
        SELECT ar.*, a.name as assessment_name, a.assessment_type
        FROM assessment_results ar
        JOIN assessments a ON a.id = ar.assessment_id
        WHERE ar.student_id = ?
        ORDER BY ar.completed_at DESC
        LIMIT 5
    """, (student_id,))
    profile['recent_assessments'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return profile


def get_topic_mastery(student_id: str, course_id: str = None) -> list:
    """Get topic mastery levels for a student."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT tm.*, t.name as topic_name, t.course_id, c.name as course_name
        FROM topic_mastery tm
        JOIN topics t ON t.id = tm.topic_id
        JOIN courses c ON c.id = t.course_id
        WHERE tm.student_id = ?
    """
    params = [student_id]
    
    if course_id:
        query += " AND t.course_id = ?"
        params.append(course_id)
    
    query += " ORDER BY tm.mastery_level ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_learning_gaps(student_id: str, threshold: float = 0.7) -> list:
    """Identify topics where student is below mastery threshold."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tm.*, t.name as topic_name, c.name as course_name
        FROM topic_mastery tm
        JOIN topics t ON t.id = tm.topic_id
        JOIN courses c ON c.id = t.course_id
        WHERE tm.student_id = ? AND tm.mastery_level < ?
        ORDER BY tm.mastery_level ASC
    """, (student_id, threshold))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_student_history(student_id: str, topic_id: str = None, 
                        limit: int = 50) -> list:
    """Get detailed question-level history for a student."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT qh.*, t.name as topic_name
        FROM question_history qh
        LEFT JOIN topics t ON t.id = qh.topic_id
        WHERE qh.student_id = ?
    """
    params = [student_id]
    
    if topic_id:
        query += " AND qh.topic_id = ?"
        params.append(topic_id)
    
    query += " ORDER BY qh.attempted_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_class_analytics(course_id: str) -> dict:
    """Get class-wide analytics for a course."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Overall class performance
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT ar.student_id) as students_assessed,
            COUNT(ar.id) as total_assessments,
            AVG(ar.percentage) as avg_percentage,
            MIN(ar.percentage) as min_percentage,
            MAX(ar.percentage) as max_percentage
        FROM assessment_results ar
        JOIN assessments a ON a.id = ar.assessment_id
        WHERE a.course_id = ?
    """, (course_id,))
    overall = dict(cursor.fetchone())
    
    # Performance by topic
    cursor.execute("""
        SELECT 
            t.id, t.name,
            AVG(tm.mastery_level) as avg_mastery,
            COUNT(tm.student_id) as students_attempted,
            SUM(CASE WHEN tm.mastery_level < 0.7 THEN 1 ELSE 0 END) as struggling_count
        FROM topics t
        LEFT JOIN topic_mastery tm ON tm.topic_id = t.id
        WHERE t.course_id = ?
        GROUP BY t.id
        ORDER BY avg_mastery ASC
    """, (course_id,))
    by_topic = [dict(row) for row in cursor.fetchall()]
    
    # Grade distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN ar.percentage >= 90 THEN 'A'
                WHEN ar.percentage >= 80 THEN 'B'
                WHEN ar.percentage >= 70 THEN 'C'
                WHEN ar.percentage >= 60 THEN 'D'
                ELSE 'F'
            END as grade,
            COUNT(*) as count
        FROM assessment_results ar
        JOIN assessments a ON a.id = ar.assessment_id
        WHERE a.course_id = ?
        GROUP BY grade
        ORDER BY grade
    """, (course_id,))
    grade_dist = {row['grade']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "overall": overall,
        "by_topic": by_topic,
        "grade_distribution": grade_dist
    }


if __name__ == "__main__":
    # Test the database
    print("Testing Student Progress Tracker Database...")
    
    # Create a course
    course = create_course("alg-101", "Algebra I", "Mathematics", "9th Grade", "bank-43da5128")
    print(f"\nCreated course: {course['name']}")
    
    # Create topics
    create_topic("t-linear", "alg-101", "Linear Equations")
    create_topic("t-quad", "alg-101", "Quadratic Equations")
    print("Created topics")
    
    # Create a student
    student = create_student("stu-001", "Alice Johnson", "alice@school.edu", "9th Grade")
    print(f"Created student: {student['name']}")
    
    # Enroll student
    enroll_student("stu-001", "alg-101")
    print("Enrolled student in course")
    
    # Create an assessment
    assessment = create_assessment("quiz-1", "alg-101", "Linear Equations Quiz", 
                                   "quiz", 100, 10)
    print(f"Created assessment: {assessment['name']}")
    
    # Record a result
    result = record_assessment_result(
        "result-001", "stu-001", "quiz-1",
        points_earned=85, points_possible=100,
        time_spent_seconds=1200,
        question_results=[
            {"question_id": "q1", "topic_id": "t-linear", "is_correct": True, "difficulty": 0.3},
            {"question_id": "q2", "topic_id": "t-linear", "is_correct": True, "difficulty": 0.5},
            {"question_id": "q3", "topic_id": "t-linear", "is_correct": False, "difficulty": 0.7},
        ]
    )
    print(f"Recorded result: {result['percentage']:.1f}%")
    
    # Get student profile
    profile = get_student_profile("stu-001")
    print(f"\nStudent Profile:")
    print(f"  Name: {profile['name']}")
    print(f"  Courses: {len(profile['courses'])}")
    print(f"  Avg Score: {profile['statistics']['avg_percentage']:.1f}%")
    
    # Get topic mastery
    mastery = get_topic_mastery("stu-001")
    print(f"\nTopic Mastery:")
    for m in mastery:
        print(f"  {m['topic_name']}: {m['mastery_level']*100:.0f}%")
    
    print("\n✅ Database test complete!")
