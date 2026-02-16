"""Tests for the MCP server tool functions."""

import os
import tempfile
from unittest.mock import patch

import pytest

# Override database path before importing (may already be set by test_database.py)
if "STUDENT_PROGRESS_DB" not in os.environ:
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["STUDENT_PROGRESS_DB"] = _tmp.name
    _own_tmp = _tmp.name
else:
    _own_tmp = None

import src.student_progress.database as db
from src.student_progress.server import (
    create_assessment,
    create_course,
    create_student,
    create_topic,
    delete_course,
    delete_student,
    enroll_student,
    get_class_analytics,
    get_learning_gaps,
    get_student_history,
    get_student_profile,
    get_topic_mastery,
    list_assessments,
    list_courses,
    list_students,
    list_topics,
    recommend_focus_areas,
    record_assessment_result,
    unenroll_student,
    update_course,
    update_student,
)

FIXED_UUID = "aabbccdd"


@pytest.fixture(autouse=True)
def _clean_db():
    """Re-initialize the database before each test."""
    # Reset initialized flag to ensure schema exists even if temp file changed
    db._initialized = False
    conn = db.get_connection()
    for table in [
        "question_history",
        "topic_mastery",
        "assessment_results",
        "assessment_topics",
        "assessments",
        "topics",
        "enrollments",
        "courses",
        "students",
    ]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
    yield


@pytest.fixture()
def _seed_data():
    """Create student, course, topic, assessment, and enroll student."""
    db.create_student("stu-001", "Alice Johnson", "alice@school.edu", "9th Grade")
    db.create_course("course-001", "Algebra I", "Mathematics", "9th Grade")
    db.enroll_student("stu-001", "course-001")
    db.create_topic("topic-001", "course-001", "Linear Equations")
    db.create_assessment("assess-001", "course-001", "Chapter 1 Quiz", "quiz", 100, 10)


# ============================================================
# STUDENT TOOLS
# ============================================================


class TestCreateStudent:
    @patch("src.student_progress.server.uuid")
    def test_success(self, mock_uuid):
        mock_uuid.uuid4.return_value.hex = FIXED_UUID + "extra"
        result = create_student("Bob Smith", "bob@school.edu", "10th Grade")
        assert "Student Created" in result
        assert "Bob Smith" in result
        assert f"stu-{FIXED_UUID}" in result

    def test_empty_name_validation(self):
        result = create_student("", "bob@school.edu")
        assert result.startswith("Error:")
        assert "name" in result

    @patch("src.student_progress.server.uuid")
    def test_minimal_args(self, mock_uuid):
        mock_uuid.uuid4.return_value.hex = FIXED_UUID + "extra"
        result = create_student("Minimal Student")
        assert "Student Created" in result
        assert "Not provided" in result  # email
        assert "Not specified" in result  # grade


class TestListStudents:
    def test_empty(self):
        result = list_students()
        assert "No students found" in result

    def test_with_students(self, _seed_data):
        result = list_students()
        assert "Alice Johnson" in result
        assert "1 total" in result

    def test_filter_by_course(self, _seed_data):
        result = list_students("course-001")
        assert "Alice Johnson" in result
        assert "in Course" in result

    def test_empty_course(self, _seed_data):
        db.create_course("course-empty", "Empty", "Science")
        result = list_students("course-empty")
        assert "No students enrolled" in result


class TestGetStudentProfile:
    def test_not_found(self):
        result = get_student_profile("nonexistent")
        assert result.startswith("Error:")
        assert "not found" in result

    def test_success(self, _seed_data):
        result = get_student_profile("stu-001")
        assert "Alice Johnson" in result
        assert "Algebra I" in result


class TestUpdateStudent:
    def test_not_found(self):
        result = update_student("nonexistent", name="X")
        assert result.startswith("Error:")
        assert "not found" in result

    def test_success(self, _seed_data):
        result = update_student("stu-001", name="Alice Smith")
        assert "Student Updated" in result
        assert "Alice Smith" in result

    def test_empty_name_validation(self, _seed_data):
        result = update_student("stu-001", name="   ")
        assert result.startswith("Error:")


class TestDeleteStudent:
    def test_no_confirm(self):
        result = delete_student("stu-001", confirm=False)
        assert result.startswith("Error:")
        assert "confirm=True" in result

    def test_not_found(self, _seed_data):
        result = delete_student("nonexistent", confirm=True)
        assert result.startswith("Error:")
        assert "not found" in result

    def test_success(self, _seed_data):
        result = delete_student("stu-001", confirm=True)
        assert "Deleted student" in result
        assert "Alice Johnson" in result


# ============================================================
# COURSE TOOLS
# ============================================================


class TestCreateCourse:
    @patch("src.student_progress.server.uuid")
    def test_success(self, mock_uuid):
        mock_uuid.uuid4.return_value.hex = FIXED_UUID + "extra"
        result = create_course("Biology 101", "Science", "10th Grade")
        assert "Course Created" in result
        assert "Biology 101" in result

    def test_empty_name_validation(self):
        result = create_course("", "Science")
        assert result.startswith("Error:")

    def test_empty_subject_validation(self):
        result = create_course("Biology", "")
        assert result.startswith("Error:")


class TestListCourses:
    def test_empty(self):
        result = list_courses()
        assert "No courses found" in result

    def test_with_courses(self, _seed_data):
        result = list_courses()
        assert "Algebra I" in result


class TestEnrollStudent:
    def test_student_not_found(self, _seed_data):
        result = enroll_student("nonexistent", "course-001")
        assert result.startswith("Error:")
        assert "Student not found" in result

    def test_course_not_found(self, _seed_data):
        result = enroll_student("stu-001", "nonexistent")
        assert result.startswith("Error:")
        assert "Course not found" in result

    def test_already_enrolled(self, _seed_data):
        result = enroll_student("stu-001", "course-001")
        assert result.startswith("Error:")
        assert "already enrolled" in result

    def test_success(self, _seed_data):
        db.create_student("stu-002", "Bob Smith")
        result = enroll_student("stu-002", "course-001")
        assert "Enrolled" in result


class TestUnenrollStudent:
    def test_student_not_found(self, _seed_data):
        result = unenroll_student("nonexistent", "course-001")
        assert result.startswith("Error:")
        assert "Student not found" in result

    def test_course_not_found(self, _seed_data):
        result = unenroll_student("stu-001", "nonexistent")
        assert result.startswith("Error:")
        assert "Course not found" in result

    def test_not_enrolled(self, _seed_data):
        db.create_student("stu-002", "Bob Smith")
        result = unenroll_student("stu-002", "course-001")
        assert result.startswith("Error:")
        assert "not enrolled" in result

    def test_success(self, _seed_data):
        result = unenroll_student("stu-001", "course-001")
        assert "Unenrolled" in result


class TestUpdateCourse:
    def test_not_found(self):
        result = update_course("nonexistent", name="X")
        assert result.startswith("Error:")

    def test_success(self, _seed_data):
        result = update_course("course-001", name="Algebra II")
        assert "Course Updated" in result
        assert "Algebra II" in result

    def test_empty_name_validation(self, _seed_data):
        result = update_course("course-001", name="")
        assert result.startswith("Error:")

    def test_empty_subject_validation(self, _seed_data):
        result = update_course("course-001", subject="  ")
        assert result.startswith("Error:")


class TestDeleteCourse:
    def test_no_confirm(self):
        result = delete_course("course-001", confirm=False)
        assert result.startswith("Error:")
        assert "confirm=True" in result

    def test_not_found(self):
        result = delete_course("nonexistent", confirm=True)
        assert result.startswith("Error:")

    def test_success(self, _seed_data):
        result = delete_course("course-001", confirm=True)
        assert "Deleted course" in result
        assert "Algebra I" in result


class TestCreateTopic:
    @patch("src.student_progress.server.uuid")
    def test_success(self, mock_uuid, _seed_data):
        mock_uuid.uuid4.return_value.hex = FIXED_UUID + "extra"
        result = create_topic("course-001", "Quadratics", 1.5)
        assert "Topic Created" in result
        assert "Quadratics" in result

    def test_course_not_found(self):
        result = create_topic("nonexistent", "Quadratics")
        assert result.startswith("Error:")
        assert "Course not found" in result

    def test_empty_name_validation(self, _seed_data):
        result = create_topic("course-001", "")
        assert result.startswith("Error:")

    def test_invalid_weight(self, _seed_data):
        result = create_topic("course-001", "Quadratics", 0)
        assert result.startswith("Error:")
        assert "weight" in result


class TestListTopics:
    def test_course_not_found(self):
        result = list_topics("nonexistent")
        assert result.startswith("Error:")
        assert "Course not found" in result

    def test_empty(self, _seed_data):
        db.create_course("course-empty", "Empty", "Science")
        result = list_topics("course-empty")
        assert "No topics" in result

    def test_with_topics(self, _seed_data):
        result = list_topics("course-001")
        assert "Linear Equations" in result


# ============================================================
# ASSESSMENT TOOLS
# ============================================================


class TestCreateAssessment:
    @patch("src.student_progress.server.uuid")
    def test_success(self, mock_uuid, _seed_data):
        mock_uuid.uuid4.return_value.hex = FIXED_UUID + "extra"
        result = create_assessment("course-001", "Midterm", "test", 200, 50, 60)
        assert "Assessment Created" in result
        assert "Midterm" in result
        assert "200" in result

    def test_course_not_found(self):
        result = create_assessment("nonexistent", "Midterm", "test", 100, 10)
        assert result.startswith("Error:")
        assert "Course not found" in result

    def test_invalid_type(self, _seed_data):
        result = create_assessment("course-001", "Midterm", "essay", 100, 10)
        assert result.startswith("Error:")
        assert "Invalid type" in result

    def test_empty_name_validation(self, _seed_data):
        result = create_assessment("course-001", "", "quiz", 100, 10)
        assert result.startswith("Error:")

    def test_zero_points_validation(self, _seed_data):
        result = create_assessment("course-001", "Quiz", "quiz", 0, 10)
        assert result.startswith("Error:")

    def test_zero_questions_validation(self, _seed_data):
        result = create_assessment("course-001", "Quiz", "quiz", 100, 0)
        assert result.startswith("Error:")


class TestListAssessments:
    def test_course_not_found(self):
        result = list_assessments("nonexistent")
        assert result.startswith("Error:")

    def test_empty(self, _seed_data):
        db.create_course("course-empty", "Empty", "Science")
        result = list_assessments("course-empty")
        assert "No assessments" in result

    def test_with_assessments(self, _seed_data):
        result = list_assessments("course-001")
        assert "Chapter 1 Quiz" in result


class TestRecordAssessmentResult:
    def test_student_not_found(self, _seed_data):
        result = record_assessment_result("nonexistent", "assess-001", 80, 100)
        assert result.startswith("Error:")
        assert "Student not found" in result

    def test_assessment_not_found(self, _seed_data):
        result = record_assessment_result("stu-001", "nonexistent", 80, 100)
        assert result.startswith("Error:")
        assert "Assessment not found" in result

    def test_not_enrolled(self, _seed_data):
        db.create_student("stu-002", "Bob Smith")
        # stu-002 is not enrolled in course-001
        result = record_assessment_result("stu-002", "assess-001", 80, 100)
        assert result.startswith("Error:")
        assert "not enrolled" in result

    def test_points_validation(self, _seed_data):
        result = record_assessment_result("stu-001", "assess-001", 110, 100)
        assert result.startswith("Error:")
        assert "cannot exceed" in result

    def test_negative_points_validation(self, _seed_data):
        result = record_assessment_result("stu-001", "assess-001", -5, 100)
        assert result.startswith("Error:")

    def test_success(self, _seed_data):
        result = record_assessment_result("stu-001", "assess-001", 85, 100)
        assert "Result Recorded" in result
        assert "85.0%" in result
        assert "**Grade:** B" in result

    def test_grade_a(self, _seed_data):
        result = record_assessment_result("stu-001", "assess-001", 95, 100)
        assert "**Grade:** A" in result

    def test_grade_f(self, _seed_data):
        result = record_assessment_result("stu-001", "assess-001", 40, 100)
        assert "**Grade:** F" in result

    def test_with_question_results(self, _seed_data):
        result = record_assessment_result(
            "stu-001", "assess-001", 80, 100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
                {"question_id": "q2", "topic_id": "topic-001", "is_correct": False},
            ],
        )
        assert "Result Recorded" in result
        assert "Topic Mastery" in result

    def test_invalid_question_results(self, _seed_data):
        result = record_assessment_result(
            "stu-001", "assess-001", 80, 100,
            question_results="not a list",
        )
        assert result.startswith("Error:")

    def test_with_time_spent(self, _seed_data):
        result = record_assessment_result(
            "stu-001", "assess-001", 80, 100, time_spent_minutes=30,
        )
        assert "30 minutes" in result


# ============================================================
# ANALYTICS TOOLS
# ============================================================


class TestGetTopicMastery:
    def test_student_not_found(self):
        result = get_topic_mastery("nonexistent")
        assert result.startswith("Error:")

    def test_no_data(self, _seed_data):
        result = get_topic_mastery("stu-001")
        assert "No mastery data" in result

    def test_with_data(self, _seed_data):
        db.record_assessment_result(
            "result-tm", "stu-001", "assess-001",
            points_earned=80, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = get_topic_mastery("stu-001")
        assert "Linear Equations" in result
        assert "Algebra I" in result


class TestGetLearningGaps:
    def test_student_not_found(self):
        result = get_learning_gaps("nonexistent")
        assert result.startswith("Error:")

    def test_invalid_threshold(self, _seed_data):
        result = get_learning_gaps("stu-001", 150)
        assert result.startswith("Error:")

    def test_no_gaps(self, _seed_data):
        db.record_assessment_result(
            "result-lg", "stu-001", "assess-001",
            points_earned=100, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = get_learning_gaps("stu-001", 70)
        assert "Great news" in result

    def test_with_gaps(self, _seed_data):
        db.record_assessment_result(
            "result-lgap", "stu-001", "assess-001",
            points_earned=30, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": False},
                {"question_id": "q2", "topic_id": "topic-001", "is_correct": False},
                {"question_id": "q3", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = get_learning_gaps("stu-001", 70)
        assert "Learning Gaps" in result
        assert "Linear Equations" in result
        assert "Critical" in result


class TestGetStudentHistory:
    def test_student_not_found(self):
        result = get_student_history("nonexistent")
        assert result.startswith("Error:")

    def test_no_history(self, _seed_data):
        result = get_student_history("stu-001")
        assert "No question history" in result

    def test_invalid_limit(self, _seed_data):
        result = get_student_history("stu-001", limit=0)
        assert result.startswith("Error:")

    def test_with_history(self, _seed_data):
        db.record_assessment_result(
            "result-sh", "stu-001", "assess-001",
            points_earned=80, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = get_student_history("stu-001")
        assert "Question History" in result
        assert "1/1 correct" in result

    def test_with_topic_filter(self, _seed_data):
        db.record_assessment_result(
            "result-shf", "stu-001", "assess-001",
            points_earned=80, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = get_student_history("stu-001", topic_id="topic-001")
        assert "Filtered by topic" in result


class TestGetClassAnalytics:
    def test_course_not_found(self):
        result = get_class_analytics("nonexistent")
        assert result.startswith("Error:")

    def test_no_data(self, _seed_data):
        result = get_class_analytics("course-001")
        assert "No assessment data" in result

    def test_with_data(self, _seed_data):
        db.record_assessment_result(
            "result-ca", "stu-001", "assess-001",
            points_earned=88, points_possible=100,
        )
        result = get_class_analytics("course-001")
        assert "Class Analytics" in result
        assert "88.0%" in result
        assert "Grade Distribution" in result


class TestRecommendFocusAreas:
    def test_student_not_found(self):
        result = recommend_focus_areas("nonexistent")
        assert result.startswith("Error:")

    def test_no_data(self, _seed_data):
        result = recommend_focus_areas("stu-001")
        assert "Not enough data" in result

    def test_no_gaps(self, _seed_data):
        db.record_assessment_result(
            "result-rfa", "stu-001", "assess-001",
            points_earned=100, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
                {"question_id": "q2", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = recommend_focus_areas("stu-001")
        assert "Excellent work" in result

    def test_with_gaps(self, _seed_data):
        db.record_assessment_result(
            "result-rfag", "stu-001", "assess-001",
            points_earned=30, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": False},
                {"question_id": "q2", "topic_id": "topic-001", "is_correct": False},
                {"question_id": "q3", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        result = recommend_focus_areas("stu-001")
        assert "Priority Order" in result
        assert "Linear Equations" in result


def teardown_module():
    """Clean up temp database if we created one."""
    if _own_tmp:
        try:
            os.unlink(_own_tmp)
        except OSError:
            pass
