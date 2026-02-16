"""Tests for the student progress tracker database layer."""

import os
import tempfile

import pytest

# Override database path before importing
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()

import src.student_progress.database as db

db.DATABASE_PATH = type(db.DATABASE_PATH)(_tmp.name)
db.init_database()


@pytest.fixture(autouse=True)
def _clean_db():
    """Re-initialize the database before each test."""
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
def sample_student():
    return db.create_student("stu-001", "Alice Johnson", "alice@school.edu", "9th Grade")


@pytest.fixture()
def sample_course():
    return db.create_course("course-001", "Algebra I", "Mathematics", "9th Grade")


@pytest.fixture()
def sample_topic(sample_course):
    return db.create_topic("topic-001", sample_course["id"], "Linear Equations")


@pytest.fixture()
def sample_assessment(sample_course):
    return db.create_assessment(
        "assess-001", sample_course["id"], "Chapter 1 Quiz", "quiz", 100, 10
    )


class TestStudentOperations:
    def test_create_student(self):
        student = db.create_student("stu-test", "Bob Smith", "bob@school.edu", "10th Grade")
        assert student["id"] == "stu-test"
        assert student["name"] == "Bob Smith"
        assert student["email"] == "bob@school.edu"
        assert student["grade_level"] == "10th Grade"

    def test_get_student(self, sample_student):
        student = db.get_student("stu-001")
        assert student is not None
        assert student["name"] == "Alice Johnson"

    def test_get_student_not_found(self):
        assert db.get_student("nonexistent") is None

    def test_list_students(self, sample_student):
        students = db.list_students()
        assert len(students) == 1
        assert students[0]["name"] == "Alice Johnson"

    def test_list_students_by_course(self, sample_student, sample_course):
        db.enroll_student("stu-001", "course-001")
        students = db.list_students("course-001")
        assert len(students) == 1

    def test_list_students_empty_course(self, sample_course):
        students = db.list_students("course-001")
        assert len(students) == 0


class TestCourseOperations:
    def test_create_course(self):
        course = db.create_course("c-test", "Biology 101", "Science", "10th Grade")
        assert course["id"] == "c-test"
        assert course["subject"] == "Science"

    def test_get_course(self, sample_course):
        course = db.get_course("course-001")
        assert course is not None
        assert course["name"] == "Algebra I"

    def test_get_course_not_found(self):
        assert db.get_course("nonexistent") is None

    def test_list_courses(self, sample_course):
        courses = db.list_courses()
        assert len(courses) == 1
        assert courses[0]["student_count"] == 0

    def test_enroll_student(self, sample_student, sample_course):
        assert db.enroll_student("stu-001", "course-001") is True

    def test_enroll_student_duplicate(self, sample_student, sample_course):
        db.enroll_student("stu-001", "course-001")
        assert db.enroll_student("stu-001", "course-001") is False


class TestTopicOperations:
    def test_create_topic(self, sample_course):
        topic = db.create_topic("t-test", "course-001", "Quadratic Equations", weight=1.5)
        assert topic["name"] == "Quadratic Equations"
        assert topic["weight"] == 1.5

    def test_list_topics(self, sample_topic):
        topics = db.list_topics("course-001")
        assert len(topics) == 1
        assert topics[0]["name"] == "Linear Equations"


class TestAssessmentOperations:
    def test_create_assessment(self, sample_course):
        assessment = db.create_assessment(
            "a-test", "course-001", "Midterm", "test", 200, 50, 3600
        )
        assert assessment["name"] == "Midterm"
        assert assessment["total_points"] == 200

    def test_get_assessment(self, sample_assessment):
        assessment = db.get_assessment("assess-001")
        assert assessment is not None
        assert assessment["assessment_type"] == "quiz"


class TestResultRecording:
    def test_record_result(self, sample_student, sample_assessment):
        result = db.record_assessment_result(
            "result-001", "stu-001", "assess-001",
            points_earned=85, points_possible=100,
        )
        assert result["percentage"] == 85.0

    def test_record_result_with_questions(
        self, sample_student, sample_assessment, sample_topic
    ):
        result = db.record_assessment_result(
            "result-002", "stu-001", "assess-001",
            points_earned=90, points_possible=100,
            question_results=[
                {
                    "question_id": "q1",
                    "topic_id": "topic-001",
                    "is_correct": True,
                    "difficulty": 0.3,
                },
                {
                    "question_id": "q2",
                    "topic_id": "topic-001",
                    "is_correct": True,
                    "difficulty": 0.5,
                },
                {
                    "question_id": "q3",
                    "topic_id": "topic-001",
                    "is_correct": False,
                    "difficulty": 0.7,
                },
            ],
        )
        assert result["percentage"] == 90.0

        mastery = db.get_topic_mastery("stu-001")
        assert len(mastery) == 1
        assert mastery[0]["topic_name"] == "Linear Equations"
        assert mastery[0]["questions_attempted"] == 3
        assert mastery[0]["questions_correct"] == 2


class TestAnalytics:
    def test_get_student_profile(self, sample_student, sample_course):
        db.enroll_student("stu-001", "course-001")
        profile = db.get_student_profile("stu-001")
        assert profile["name"] == "Alice Johnson"
        assert len(profile["courses"]) == 1

    def test_get_learning_gaps(self, sample_student, sample_assessment, sample_topic):
        db.record_assessment_result(
            "result-gap", "stu-001", "assess-001",
            points_earned=50, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
                {"question_id": "q2", "topic_id": "topic-001", "is_correct": False},
                {"question_id": "q3", "topic_id": "topic-001", "is_correct": False},
            ],
        )
        gaps = db.get_learning_gaps("stu-001", 0.7)
        assert len(gaps) == 1
        assert gaps[0]["topic_name"] == "Linear Equations"

    def test_get_student_history(self, sample_student, sample_assessment, sample_topic):
        db.record_assessment_result(
            "result-hist", "stu-001", "assess-001",
            points_earned=80, points_possible=100,
            question_results=[
                {"question_id": "q1", "topic_id": "topic-001", "is_correct": True},
            ],
        )
        history = db.get_student_history("stu-001")
        assert len(history) == 1
        assert history[0]["is_correct"] == 1

    def test_get_class_analytics(self, sample_student, sample_course, sample_assessment):
        db.enroll_student("stu-001", "course-001")
        db.record_assessment_result(
            "result-class", "stu-001", "assess-001",
            points_earned=88, points_possible=100,
        )
        analytics = db.get_class_analytics("course-001")
        assert analytics["overall"]["students_assessed"] == 1
        assert analytics["overall"]["avg_percentage"] == 88.0


def teardown_module():
    """Clean up temp database."""
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
