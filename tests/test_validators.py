"""Tests for input validation functions."""

import pytest

from src.student_progress.validators import (
    ValidationError,
    validate_limit,
    validate_non_empty_string,
    validate_non_negative_number,
    validate_percentage_bounds,
    validate_points_earned,
    validate_positive_integer,
    validate_positive_number,
    validate_question_results,
    validate_weight,
)


class TestValidateNonEmptyString:
    def test_valid_string(self):
        assert validate_non_empty_string("hello", "field") == "hello"

    def test_strips_whitespace(self):
        assert validate_non_empty_string("  hello  ", "field") == "hello"

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="field must be a non-empty string"):
            validate_non_empty_string("", "field")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            validate_non_empty_string("   ", "field")

    def test_non_string_raises(self):
        with pytest.raises(ValidationError):
            validate_non_empty_string(123, "field")


class TestValidatePositiveNumber:
    def test_valid_float(self):
        assert validate_positive_number(1.5, "field") == 1.5

    def test_valid_int(self):
        assert validate_positive_number(10, "field") == 10.0

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="field must be a positive number"):
            validate_positive_number(0, "field")

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_positive_number(-5, "field")


class TestValidateNonNegativeNumber:
    def test_zero_ok(self):
        assert validate_non_negative_number(0, "field") == 0.0

    def test_positive_ok(self):
        assert validate_non_negative_number(5.5, "field") == 5.5

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="field must be a non-negative number"):
            validate_non_negative_number(-1, "field")


class TestValidatePercentageBounds:
    def test_valid_values(self):
        assert validate_percentage_bounds(0, "pct") == 0.0
        assert validate_percentage_bounds(50, "pct") == 50.0
        assert validate_percentage_bounds(100, "pct") == 100.0

    def test_below_zero_raises(self):
        with pytest.raises(ValidationError, match="pct must be between 0 and 100"):
            validate_percentage_bounds(-1, "pct")

    def test_above_100_raises(self):
        with pytest.raises(ValidationError):
            validate_percentage_bounds(101, "pct")


class TestValidatePointsEarned:
    def test_valid(self):
        validate_points_earned(80, 100)

    def test_zero_earned_ok(self):
        validate_points_earned(0, 100)

    def test_earned_equals_possible_ok(self):
        validate_points_earned(100, 100)

    def test_earned_exceeds_possible_raises(self):
        with pytest.raises(ValidationError, match="cannot exceed"):
            validate_points_earned(110, 100)

    def test_negative_earned_raises(self):
        with pytest.raises(ValidationError, match="points_earned must be a non-negative"):
            validate_points_earned(-5, 100)

    def test_zero_possible_raises(self):
        with pytest.raises(ValidationError, match="points_possible must be a positive"):
            validate_points_earned(0, 0)


class TestValidateLimit:
    def test_valid(self):
        assert validate_limit(10) == 10

    def test_min_value(self):
        assert validate_limit(1) == 1

    def test_max_value(self):
        assert validate_limit(500) == 500

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="limit must be between 1 and 500"):
            validate_limit(0)

    def test_over_max_raises(self):
        with pytest.raises(ValidationError):
            validate_limit(501)

    def test_custom_max(self):
        assert validate_limit(50, max_limit=100) == 50
        with pytest.raises(ValidationError):
            validate_limit(101, max_limit=100)


class TestValidatePositiveInteger:
    def test_valid(self):
        assert validate_positive_integer(5, "field") == 5

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="field must be a positive integer"):
            validate_positive_integer(0, "field")

    def test_float_raises(self):
        with pytest.raises(ValidationError):
            validate_positive_integer(1.5, "field")


class TestValidateQuestionResults:
    def test_valid(self):
        results = [
            {"question_id": "q1", "is_correct": True},
            {"question_id": "q2", "is_correct": False},
        ]
        assert validate_question_results(results) == results

    def test_not_a_list_raises(self):
        with pytest.raises(ValidationError, match="must be a list"):
            validate_question_results("not a list")

    def test_item_not_dict_raises(self):
        with pytest.raises(ValidationError, match=r"question_results\[0\] must be a dict"):
            validate_question_results(["not a dict"])

    def test_missing_question_id_raises(self):
        with pytest.raises(ValidationError, match="missing required field 'question_id'"):
            validate_question_results([{"is_correct": True}])

    def test_missing_is_correct_raises(self):
        with pytest.raises(ValidationError, match="missing required field 'is_correct'"):
            validate_question_results([{"question_id": "q1"}])


class TestValidateWeight:
    def test_valid(self):
        assert validate_weight(1.5) == 1.5

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="weight must be a positive number"):
            validate_weight(0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_weight(-1)
