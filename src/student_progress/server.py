"""
Student Progress Tracker MCP Server

Tracks student performance across topics and assessments:
- Record assessment results
- Calculate topic mastery
- Identify learning gaps
- Provide analytics for teachers and students
"""

import json
import uuid
from mcp.server.fastmcp import FastMCP
from . import database as db

# Initialize MCP server
mcp = FastMCP("Student Progress Tracker")


# ============================================================
# STUDENT TOOLS
# ============================================================

@mcp.tool()
def create_student(
    name: str,
    email: str = None,
    grade_level: str = None
) -> str:
    """
    Create a new student record.
    
    Args:
        name: Student's full name
        email: Student's email address
        grade_level: Grade level (e.g., "9th Grade", "College Freshman")
    
    Returns:
        Confirmation with student details
    """
    student_id = f"stu-{uuid.uuid4().hex[:8]}"
    
    student = db.create_student(
        student_id=student_id,
        name=name,
        email=email,
        grade_level=grade_level
    )
    
    return f"""
✅ Student Created!

**ID:** `{student['id']}`
**Name:** {student['name']}
**Email:** {student['email'] or 'Not provided'}
**Grade Level:** {student['grade_level'] or 'Not specified'}

Next: Enroll the student in a course with `enroll_student`.
"""


@mcp.tool()
def list_students(course_id: str = None) -> str:
    """
    List all students, optionally filtered by course.
    
    Args:
        course_id: Optional course ID to filter by enrollment
    
    Returns:
        List of students
    """
    students = db.list_students(course_id)
    
    if not students:
        msg = f"No students enrolled in this course." if course_id else "No students found."
        return msg
    
    result = f"**Students{' in Course' if course_id else ''}:** ({len(students)} total)\n\n"
    
    for s in students:
        result += f"- **{s['name']}** (`{s['id']}`)"
        if s['grade_level']:
            result += f" - {s['grade_level']}"
        result += "\n"
    
    return result


@mcp.tool()
def get_student_profile(student_id: str) -> str:
    """
    Get comprehensive student profile with performance data.
    
    Args:
        student_id: The student ID
    
    Returns:
        Student profile with courses, statistics, and recent assessments
    """
    profile = db.get_student_profile(student_id)
    
    if not profile:
        return f"Student not found: {student_id}"
    
    stats = profile['statistics']
    avg_pct = stats['avg_percentage']
    avg_str = f"{avg_pct:.1f}%" if avg_pct is not None else "N/A"
    
    result = f"""
## 👤 Student Profile: {profile['name']}

**ID:** `{profile['id']}`
**Email:** {profile['email'] or 'Not provided'}
**Grade Level:** {profile['grade_level'] or 'Not specified'}

### 📊 Overall Statistics
- **Assessments Taken:** {stats['total_assessments'] or 0}
- **Average Score:** {avg_str}
- **Total Points:** {stats['total_points_earned'] or 0:.0f} / {stats['total_points_possible'] or 0:.0f}
"""
    
    if stats['total_time_spent']:
        hours = stats['total_time_spent'] // 3600
        mins = (stats['total_time_spent'] % 3600) // 60
        result += f"- **Total Time:** {hours}h {mins}m\n"
    
    if profile['courses']:
        result += "\n### 📚 Enrolled Courses\n"
        for c in profile['courses']:
            result += f"- **{c['name']}** ({c['subject']}) - {c['status']}\n"
    
    if profile['recent_assessments']:
        result += "\n### 📝 Recent Assessments\n"
        for a in profile['recent_assessments']:
            result += f"- **{a['assessment_name']}** ({a['assessment_type']}): {a['percentage']:.1f}%\n"
    
    return result


# ============================================================
# COURSE TOOLS
# ============================================================

@mcp.tool()
def create_course(
    name: str,
    subject: str,
    grade_level: str = None,
    question_bank_id: str = None
) -> str:
    """
    Create a new course.
    
    Args:
        name: Course name (e.g., "Algebra I", "Biology 101")
        subject: Subject area (e.g., "Mathematics", "Science")
        grade_level: Target grade level
        question_bank_id: Optional link to a question bank MCP
    
    Returns:
        Confirmation with course details
    """
    course_id = f"course-{uuid.uuid4().hex[:8]}"
    
    course = db.create_course(
        course_id=course_id,
        name=name,
        subject=subject,
        grade_level=grade_level,
        question_bank_id=question_bank_id
    )
    
    return f"""
✅ Course Created!

**ID:** `{course['id']}`
**Name:** {course['name']}
**Subject:** {course['subject']}
**Grade Level:** {course['grade_level'] or 'Not specified'}
**Question Bank:** {course['question_bank_id'] or 'Not linked'}

Next steps:
- Add topics with `create_topic`
- Enroll students with `enroll_student`
"""


@mcp.tool()
def list_courses() -> str:
    """
    List all courses.
    
    Returns:
        List of courses with student counts
    """
    courses = db.list_courses()
    
    if not courses:
        return "No courses found. Create one with `create_course`."
    
    result = "**Courses:**\n\n"
    
    for c in courses:
        result += f"### {c['name']}\n"
        result += f"- **ID:** `{c['id']}`\n"
        result += f"- **Subject:** {c['subject']}\n"
        result += f"- **Students:** {c['student_count']}\n\n"
    
    return result


@mcp.tool()
def enroll_student(student_id: str, course_id: str) -> str:
    """
    Enroll a student in a course.
    
    Args:
        student_id: The student ID
        course_id: The course ID
    
    Returns:
        Confirmation of enrollment
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    course = db.get_course(course_id)
    if not course:
        return f"Course not found: {course_id}"
    
    success = db.enroll_student(student_id, course_id)
    
    if success:
        return f"✅ Enrolled **{student['name']}** in **{course['name']}**"
    else:
        return f"Student is already enrolled in this course."


@mcp.tool()
def create_topic(
    course_id: str,
    name: str,
    weight: float = 1.0
) -> str:
    """
    Create a topic within a course for tracking mastery.
    
    Args:
        course_id: The course ID
        name: Topic name (e.g., "Linear Equations")
        weight: Importance weight for grading (default 1.0)
    
    Returns:
        Confirmation with topic details
    """
    course = db.get_course(course_id)
    if not course:
        return f"Course not found: {course_id}"
    
    topic_id = f"topic-{uuid.uuid4().hex[:8]}"
    
    topic = db.create_topic(
        topic_id=topic_id,
        course_id=course_id,
        name=name,
        weight=weight
    )
    
    return f"""
✅ Topic Created!

**ID:** `{topic['id']}`
**Name:** {topic['name']}
**Course:** {course['name']}
**Weight:** {topic['weight']}
"""


@mcp.tool()
def list_topics(course_id: str) -> str:
    """
    List topics for a course.
    
    Args:
        course_id: The course ID
    
    Returns:
        List of topics
    """
    course = db.get_course(course_id)
    if not course:
        return f"Course not found: {course_id}"
    
    topics = db.list_topics(course_id)
    
    if not topics:
        return f"No topics in '{course['name']}'. Create one with `create_topic`."
    
    result = f"**Topics in '{course['name']}':**\n\n"
    
    for t in topics:
        result += f"- **{t['name']}** (`{t['id']}`) - Weight: {t['weight']}\n"
    
    return result


# ============================================================
# ASSESSMENT TOOLS
# ============================================================

@mcp.tool()
def create_assessment(
    course_id: str,
    name: str,
    assessment_type: str,
    total_points: float,
    total_questions: int,
    time_limit_minutes: int = None
) -> str:
    """
    Create an assessment (test, quiz, homework).
    
    Args:
        course_id: The course ID
        name: Assessment name (e.g., "Chapter 3 Quiz")
        assessment_type: Type - "test", "quiz", "homework", "practice"
        total_points: Total points possible
        total_questions: Number of questions
        time_limit_minutes: Optional time limit in minutes
    
    Returns:
        Confirmation with assessment details
    """
    course = db.get_course(course_id)
    if not course:
        return f"Course not found: {course_id}"
    
    valid_types = ['test', 'quiz', 'homework', 'practice']
    if assessment_type not in valid_types:
        return f"Invalid type. Must be one of: {', '.join(valid_types)}"
    
    assessment_id = f"assess-{uuid.uuid4().hex[:8]}"
    time_limit_seconds = time_limit_minutes * 60 if time_limit_minutes else None
    
    assessment = db.create_assessment(
        assessment_id=assessment_id,
        course_id=course_id,
        name=name,
        assessment_type=assessment_type,
        total_points=total_points,
        total_questions=total_questions,
        time_limit_seconds=time_limit_seconds
    )
    
    return f"""
✅ Assessment Created!

**ID:** `{assessment['id']}`
**Name:** {assessment['name']}
**Type:** {assessment['assessment_type'].title()}
**Course:** {course['name']}
**Points:** {assessment['total_points']}
**Questions:** {assessment['total_questions']}
**Time Limit:** {time_limit_minutes or 'None'} minutes
"""


@mcp.tool()
def record_assessment_result(
    student_id: str,
    assessment_id: str,
    points_earned: float,
    points_possible: float,
    time_spent_minutes: int = None,
    question_results: list = None
) -> str:
    """
    Record a student's assessment result.
    
    Args:
        student_id: The student ID
        assessment_id: The assessment ID
        points_earned: Points the student earned
        points_possible: Total points possible
        time_spent_minutes: Time spent in minutes
        question_results: Optional list of per-question results, each with:
            - question_id: Question identifier
            - topic_id: Topic the question belongs to
            - is_correct: Whether the answer was correct
            - time_spent_seconds: Time on this question
            - difficulty: Question difficulty (0-1)
            - bloom_level: Bloom's taxonomy level
    
    Returns:
        Result summary with updated mastery levels
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    assessment = db.get_assessment(assessment_id)
    if not assessment:
        return f"Assessment not found: {assessment_id}"
    
    result_id = f"result-{uuid.uuid4().hex[:8]}"
    time_spent_seconds = time_spent_minutes * 60 if time_spent_minutes else None
    
    result = db.record_assessment_result(
        result_id=result_id,
        student_id=student_id,
        assessment_id=assessment_id,
        points_earned=points_earned,
        points_possible=points_possible,
        time_spent_seconds=time_spent_seconds,
        question_results=question_results
    )
    
    # Get grade letter
    pct = result['percentage']
    if pct >= 90: grade = 'A'
    elif pct >= 80: grade = 'B'
    elif pct >= 70: grade = 'C'
    elif pct >= 60: grade = 'D'
    else: grade = 'F'
    
    response = f"""
✅ Assessment Result Recorded!

**Student:** {student['name']}
**Assessment:** {assessment['name']}
**Score:** {result['points_earned']:.1f} / {result['points_possible']:.1f}
**Percentage:** {result['percentage']:.1f}%
**Grade:** {grade}
"""
    
    if time_spent_minutes:
        response += f"**Time Spent:** {time_spent_minutes} minutes\n"
    
    # Show updated topic mastery if we have question-level data
    if question_results:
        mastery = db.get_topic_mastery(student_id)
        if mastery:
            response += "\n### Updated Topic Mastery\n"
            for m in mastery:
                level = m['mastery_level'] * 100
                trend_icon = {'improving': '📈', 'stable': '➡️', 'declining': '📉'}.get(m['trend'], '')
                response += f"- **{m['topic_name']}:** {level:.0f}% {trend_icon}\n"
    
    return response


# ============================================================
# ANALYTICS TOOLS
# ============================================================

@mcp.tool()
def get_topic_mastery(student_id: str, course_id: str = None) -> str:
    """
    Get topic mastery levels for a student.
    
    Args:
        student_id: The student ID
        course_id: Optional course ID to filter by
    
    Returns:
        Topic mastery breakdown with trends
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    mastery = db.get_topic_mastery(student_id, course_id)
    
    if not mastery:
        return f"No mastery data for {student['name']} yet. Record some assessment results first."
    
    result = f"## 📊 Topic Mastery for {student['name']}\n\n"
    
    # Group by course
    by_course = {}
    for m in mastery:
        course_name = m['course_name']
        if course_name not in by_course:
            by_course[course_name] = []
        by_course[course_name].append(m)
    
    for course_name, topics in by_course.items():
        result += f"### {course_name}\n\n"
        result += "| Topic | Mastery | Questions | Trend |\n"
        result += "|-------|---------|-----------|-------|\n"
        
        for m in topics:
            level = m['mastery_level'] * 100
            trend_icon = {'improving': '📈', 'stable': '➡️', 'declining': '📉'}.get(m['trend'], '')
            
            # Mastery bar
            filled = int(level / 10)
            bar = '█' * filled + '░' * (10 - filled)
            
            result += f"| {m['topic_name']} | {bar} {level:.0f}% | {m['questions_attempted']} | {trend_icon} {m['trend'] or ''} |\n"
        
        result += "\n"
    
    return result


@mcp.tool()
def get_learning_gaps(student_id: str, threshold: float = 70.0) -> str:
    """
    Identify topics where student needs improvement.
    
    Args:
        student_id: The student ID
        threshold: Mastery threshold percentage (default 70%)
    
    Returns:
        List of topics below threshold with recommendations
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    gaps = db.get_learning_gaps(student_id, threshold / 100)
    
    if not gaps:
        return f"🎉 Great news! **{student['name']}** has no learning gaps below {threshold}% mastery."
    
    result = f"""
## 🎯 Learning Gaps for {student['name']}

Topics below {threshold}% mastery that need attention:

"""
    
    for g in gaps:
        level = g['mastery_level'] * 100
        questions = g['questions_attempted']
        
        # Severity
        if level < 40:
            severity = "🔴 Critical"
        elif level < 60:
            severity = "🟠 Needs Work"
        else:
            severity = "🟡 Almost There"
        
        result += f"### {g['topic_name']} ({g['course_name']})\n"
        result += f"- **Mastery:** {level:.0f}%\n"
        result += f"- **Status:** {severity}\n"
        result += f"- **Questions Attempted:** {questions}\n"
        result += f"- **Trend:** {g['trend'] or 'N/A'}\n\n"
    
    result += """
### 💡 Recommendations

1. Focus on the **Critical** topics first
2. Practice with easier questions to build confidence
3. Review explanations for missed questions
4. Take practice assessments to track improvement
"""
    
    return result


@mcp.tool()
def get_student_history(
    student_id: str,
    topic_id: str = None,
    limit: int = 20
) -> str:
    """
    Get detailed question-level history for a student.
    
    Args:
        student_id: The student ID
        topic_id: Optional topic ID to filter by
        limit: Maximum number of records (default 20)
    
    Returns:
        Question history with performance details
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    history = db.get_student_history(student_id, topic_id, limit)
    
    if not history:
        return f"No question history for {student['name']}."
    
    result = f"## 📜 Question History for {student['name']}\n\n"
    
    if topic_id:
        result += f"*Filtered by topic*\n\n"
    
    result += "| Question | Topic | Result | Difficulty | Time |\n"
    result += "|----------|-------|--------|------------|------|\n"
    
    for h in history:
        correct = "✅" if h['is_correct'] else "❌"
        topic = h['topic_name'] or 'N/A'
        diff = f"{h['difficulty']:.1f}" if h['difficulty'] else 'N/A'
        time_str = f"{h['time_spent_seconds']}s" if h['time_spent_seconds'] else 'N/A'
        
        result += f"| `{h['question_id'][:12]}...` | {topic} | {correct} | {diff} | {time_str} |\n"
    
    # Summary
    correct_count = sum(1 for h in history if h['is_correct'])
    total = len(history)
    
    result += f"\n**Summary:** {correct_count}/{total} correct ({correct_count/total*100:.0f}%)\n"
    
    return result


@mcp.tool()
def get_class_analytics(course_id: str) -> str:
    """
    Get class-wide analytics for a course.
    
    Args:
        course_id: The course ID
    
    Returns:
        Class performance overview with grade distribution and topic analysis
    """
    course = db.get_course(course_id)
    if not course:
        return f"Course not found: {course_id}"
    
    analytics = db.get_class_analytics(course_id)
    overall = analytics['overall']
    
    if not overall['students_assessed']:
        return f"No assessment data for '{course['name']}' yet."
    
    result = f"""
## 📈 Class Analytics: {course['name']}

### Overall Performance
- **Students Assessed:** {overall['students_assessed']}
- **Total Assessments:** {overall['total_assessments']}
- **Average Score:** {overall['avg_percentage']:.1f}%
- **Score Range:** {overall['min_percentage']:.0f}% - {overall['max_percentage']:.0f}%

### Grade Distribution
"""
    
    grades = analytics['grade_distribution']
    total_grades = sum(grades.values()) if grades else 0
    
    for grade in ['A', 'B', 'C', 'D', 'F']:
        count = grades.get(grade, 0)
        pct = (count / total_grades * 100) if total_grades > 0 else 0
        bar_len = int(pct / 5)
        bar = '█' * bar_len
        result += f"- **{grade}:** {bar} {count} ({pct:.0f}%)\n"
    
    if analytics['by_topic']:
        result += "\n### Topic Performance (Class Average)\n\n"
        result += "| Topic | Avg Mastery | Students | Struggling |\n"
        result += "|-------|-------------|----------|------------|\n"
        
        for t in analytics['by_topic']:
            avg = (t['avg_mastery'] or 0) * 100
            result += f"| {t['name']} | {avg:.0f}% | {t['students_attempted']} | {t['struggling_count']} |\n"
    
    return result


@mcp.tool()
def recommend_focus_areas(student_id: str) -> str:
    """
    Get personalized recommendations for what a student should focus on.
    
    Args:
        student_id: The student ID
    
    Returns:
        Prioritized list of topics to study with rationale
    """
    student = db.get_student(student_id)
    if not student:
        return f"Student not found: {student_id}"
    
    # Get gaps and mastery
    gaps = db.get_learning_gaps(student_id, 0.8)  # Below 80%
    mastery = db.get_topic_mastery(student_id)
    
    if not mastery:
        return f"Not enough data to make recommendations for {student['name']}. Complete some assessments first."
    
    result = f"""
## 🎯 Recommended Focus Areas for {student['name']}

"""
    
    if not gaps:
        result += "🌟 **Excellent work!** All topics are at 80%+ mastery.\n\n"
        result += "### Suggestions for Continued Growth\n"
        result += "- Challenge yourself with harder questions\n"
        result += "- Help tutor other students\n"
        result += "- Explore advanced topics\n"
        return result
    
    # Prioritize: declining trends first, then lowest mastery
    prioritized = sorted(gaps, key=lambda x: (
        0 if x['trend'] == 'declining' else 1,
        x['mastery_level']
    ))
    
    result += "### Priority Order\n\n"
    
    for i, topic in enumerate(prioritized[:5], 1):
        level = topic['mastery_level'] * 100
        trend = topic['trend'] or 'unknown'
        
        # Reason for priority
        if trend == 'declining':
            reason = "📉 Skills declining - review needed"
        elif level < 50:
            reason = "🔴 Major gap - foundational concepts"
        elif level < 70:
            reason = "🟠 Moderate gap - practice needed"
        else:
            reason = "🟡 Minor gap - almost there"
        
        result += f"**{i}. {topic['topic_name']}** ({topic['course_name']})\n"
        result += f"   - Current: {level:.0f}% | Trend: {trend}\n"
        result += f"   - {reason}\n\n"
    
    result += """
### 💡 Study Tips

1. **Start with Priority 1** - Don't move on until you reach 70%+
2. **Practice daily** - 15-20 minutes is better than cramming
3. **Review mistakes** - Read explanations for wrong answers
4. **Ask for help** - Talk to your teacher about difficult concepts
"""
    
    return result


# ============================================================
# MAIN
# ============================================================

def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
