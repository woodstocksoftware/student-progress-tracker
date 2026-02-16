"""Tests for the student progress tracker database layer."""

import os
import tempfile

import pytest

# Override database path before importing
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()

os.environ["STUDENT_PROGRESS_DB"] = _tmp.name

import src.student_progress.database as db


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


@pytest.fixture()
def enrolled_student(sample_student, sample_course):
    """Student enrolled in the sample course."""
    db.enroll_student("stu-001", "course-001")
    return sample_student


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

    def test_list_students_by_course(self, enrolled_student, sample_course):
        students = db.list_students("course-001")
        assert len(students) == 1

    def test_list_students_empty_course(self, sample_course):
        students = db.list_students("course-001")
        assert len(students) == 0


class TestStudentCRUD:
    def test_update_student_name(self, sample_student):
        updated = db.update_student("stu-001", name="Alice Smith")
        assert updated is not None
        assert updated["name"] == "Alice Smith"
        assert updated["email"] == "alice@school.edu"

    def test_update_student_email(self, sample_student):
        updated = db.update_student("stu-001", email="new@school.edu")
        assert updated["email"] == "new@school.edu"
        assert updated["name"] == "Alice Johnson"

    def test_update_student_not_found(self):
        assert db.update_student("nonexistent", name="X") is None

    def test_delete_student(self, sample_student):
        assert db.delete_student("stu-001") is True
        assert db.get_student("stu-001") is None

    def test_delete_student_not_found(self):
        assert db.delete_student("nonexistent") is False

    def test_delete_student_cascades_enrollment(self, enrolled_student, sample_course):
        db.delete_student("stu-001")
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


class TestCourseCRUD:
    def test_update_course_name(self, sample_course):
        updated = db.update_course("course-001", name="Algebra II")
        assert updated is not None
        assert updated["name"] == "Algebra II"
        assert updated["subject"] == "Mathematics"

    def test_update_course_subject(self, sample_course):
        updated = db.update_course("course-001", subject="Science")
        assert updated["subject"] == "Science"

    def test_update_course_not_found(self):
        assert db.update_course("nonexistent", name="X") is None

    def test_delete_course(self, sample_course):
        assert db.delete_course("course-001") is True
        assert db.get_course("course-001") is None

    def test_delete_course_not_found(self):
        assert db.delete_course("nonexistent") is False

    def test_unenroll_student(self, enrolled_student, sample_course):
        assert db.unenroll_student("stu-001", "course-001") is True
        students = db.list_students("course-001")
        assert len(students) == 0

    def test_unenroll_student_not_enrolled(self, sample_student, sample_course):
        assert db.unenroll_student("stu-001", "course-001") is False


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

    def test_list_assessments(self, sample_assessment):
        assessments = db.list_assessments("course-001")
        assert len(assessments) == 1
        assert assessments[0]["name"] == "Chapter 1 Quiz"
        assert assessments[0]["results_count"] == 0

    def test_list_assessments_empty(self, sample_course):
        assessments = db.list_assessments("course-001")
        assert len(assessments) == 0


class TestResultRecording:
    def test_record_result(self, enrolled_student, sample_assessment):
        result = db.record_assessment_result(
            "result-001", "stu-001", "assess-001",
            points_earned=85, points_possible=100,
        )
        assert result["percentage"] == 85.0

    def test_record_result_with_questions(
        self, enrolled_student, sample_assessment, sample_topic
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

    def test_retake_updates_existing(self, enrolled_student, sample_assessment):
        db.record_assessment_result(
            "result-001", "stu-001", "assess-001",
            points_earned=70, points_possible=100,
        )
        # Retake with a new result_id - should update existing row
        result = db.record_assessment_result(
            "result-002", "stu-001", "assess-001",
            points_earned=90, points_possible=100,
        )
        assert result["percentage"] == 90.0
        # The ID should be the original result's ID
        assert result["id"] == "result-001"


class TestEnrollmentCheck:
    def test_check_enrollment_enrolled(self, enrolled_student, sample_assessment):
        assert db.check_enrollment("stu-001", "assess-001") is True

    def test_check_enrollment_not_enrolled(self, sample_student, sample_assessment):
        assert db.check_enrollment("stu-001", "assess-001") is False


class TestAnalytics:
    def test_get_student_profile(self, enrolled_student, sample_course):
        profile = db.get_student_profile("stu-001")
        assert profile["name"] == "Alice Johnson"
        assert len(profile["courses"]) == 1

    def test_get_learning_gaps(self, enrolled_student, sample_assessment, sample_topic):
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

    def test_get_student_history(self, enrolled_student, sample_assessment, sample_topic):
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

    def test_get_class_analytics(self, enrolled_student, sample_course, sample_assessment):
        db.record_assessment_result(
            "result-class", "stu-001", "assess-001",
            points_earned=88, points_possible=100,
        )
        analytics = db.get_class_analytics("course-001")
        assert analytics["overall"]["students_assessed"] == 1
        assert analytics["overall"]["avg_percentage"] == 88.0


class TestDatabaseConfig:
    def test_wal_mode(self):
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            assert mode == "wal"
        finally:
            conn.close()

    def test_foreign_keys_enabled(self):
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            assert cursor.fetchone()[0] == 1
        finally:
            conn.close()


def teardown_module():
    """Clean up temp database."""
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
