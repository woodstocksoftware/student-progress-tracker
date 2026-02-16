"""Input validation for Student Progress Tracker MCP tools."""


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_non_empty_string(value: str, field_name: str) -> str:
    """Validate that a string is non-empty and not just whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def validate_positive_number(value: float, field_name: str) -> float:
    """Validate that a number is positive (> 0)."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive number")
    return float(value)


def validate_non_negative_number(value: float, field_name: str) -> float:
    """Validate that a number is non-negative (>= 0)."""
    if not isinstance(value, (int, float)) or value < 0:
        raise ValidationError(f"{field_name} must be a non-negative number")
    return float(value)


def validate_percentage_bounds(value: float, field_name: str) -> float:
    """Validate that a value is between 0 and 100 (inclusive)."""
    if not isinstance(value, (int, float)) or value < 0 or value > 100:
        raise ValidationError(f"{field_name} must be between 0 and 100")
    return float(value)


def validate_points_earned(earned: float, possible: float) -> None:
    """Validate that points earned does not exceed points possible and both are non-negative."""
    if not isinstance(earned, (int, float)) or earned < 0:
        raise ValidationError("points_earned must be a non-negative number")
    if not isinstance(possible, (int, float)) or possible <= 0:
        raise ValidationError("points_possible must be a positive number")
    if earned > possible:
        raise ValidationError(
            f"points_earned ({earned}) cannot exceed points_possible ({possible})"
        )


def validate_limit(value: int, max_limit: int = 500) -> int:
    """Validate a limit/pagination parameter."""
    if not isinstance(value, int) or value < 1 or value > max_limit:
        raise ValidationError(f"limit must be between 1 and {max_limit}")
    return value


def validate_positive_integer(value: int, field_name: str) -> int:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer")
    return value


def validate_question_results(results: list) -> list:
    """Validate the structure of question_results list."""
    if not isinstance(results, list):
        raise ValidationError("question_results must be a list")
    for i, qr in enumerate(results):
        if not isinstance(qr, dict):
            raise ValidationError(f"question_results[{i}] must be a dict")
        if "question_id" not in qr:
            raise ValidationError(f"question_results[{i}] missing required field 'question_id'")
        if "is_correct" not in qr:
            raise ValidationError(f"question_results[{i}] missing required field 'is_correct'")
    return results


def validate_weight(value: float) -> float:
    """Validate a topic weight is positive."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationError("weight must be a positive number")
    return float(value)
