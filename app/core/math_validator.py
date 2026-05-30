"""
SymPy-based mathematical validation.
Used to check student answers for correctness before LLM grading.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_answer(student_answer: str, correct_answer: str) -> dict[str, Any]:
    """
    Use SymPy to check if student answer is mathematically equivalent
    to the correct answer.
    
    Returns:
        {
            "is_correct": bool,
            "method": "sympy" | "fallback",
            "reason": str
        }
    """
    try:
        from sympy import simplify, sympify, SympifyError
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

        transformations = standard_transformations + (implicit_multiplication_application,)

        # Clean up the expressions
        student = _clean_expression(student_answer)
        correct = _clean_expression(correct_answer)

        if not student or not correct:
            return {
                "is_correct": None,
                "method": "fallback",
                "reason": "Could not parse expressions"
            }

        student_expr = parse_expr(student, transformations=transformations)
        correct_expr = parse_expr(correct, transformations=transformations)

        # Check equivalence
        difference = simplify(student_expr - correct_expr)

        is_correct = difference == 0

        return {
            "is_correct": is_correct,
            "method": "sympy",
            "reason": "Mathematically equivalent" if is_correct else f"Difference: {difference}"
        }

    except Exception as e:
        logger.warning("SymPy validation failed: %s", e)
        return {
            "is_correct": None,
            "method": "fallback",
            "reason": f"Could not validate: {e}"
        }


def validate_steps(steps: list[dict]) -> list[dict]:
    """
    Validate each step in a student's working.
    
    Each step should have:
        {"from": "expression", "to": "expression", "operation": "description"}
    
    Returns steps with validation results added.
    """
    validated = []
    for step in steps:
        result = _validate_single_step(step)
        validated.append({**step, **result})
    return validated


def _validate_single_step(step: dict) -> dict:
    """Validate a single transformation step."""
    try:
        from sympy import simplify, sympify
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

        transformations = standard_transformations + (implicit_multiplication_application,)

        from_expr_str = _clean_expression(step.get("from", ""))
        to_expr_str = _clean_expression(step.get("to", ""))

        if not from_expr_str or not to_expr_str:
            return {
                "classification": "unknown",
                "reason": "Could not parse step expressions",
                "sympy_checked": False
            }

        # Check for common invalid operations first
        invalid = _check_invalid_operations(step)
        if invalid:
            return {
                "classification": "invalid_method",
                "reason": invalid,
                "sympy_checked": False
            }

        # SymPy equivalence check
        from_expr = parse_expr(from_expr_str, transformations=transformations)
        to_expr = parse_expr(to_expr_str, transformations=transformations)
        difference = simplify(from_expr - to_expr)

        if difference == 0:
            return {
                "classification": "valid",
                "reason": "Transformation is mathematically correct",
                "sympy_checked": True
            }
        else:
            return {
                "classification": "incorrect",
                "reason": f"Transformation is incorrect. Difference: {difference}",
                "sympy_checked": True
            }

    except Exception as e:
        return {
            "classification": "unknown",
            "reason": f"Could not validate: {e}",
            "sympy_checked": False
        }


def _check_invalid_operations(step: dict) -> str | None:
    """
    Rule-based detection of common invalid mathematical operations.
    Returns error message if invalid, None if ok.
    """
    operation = step.get("operation", "").lower()
    from_expr = step.get("from", "")
    to_expr = step.get("to", "")

    # Rule 1: Cancelling terms across addition
    if "cancel" in operation and "+" in from_expr:
        return "Cannot cancel terms across addition e.g. (x+1)/x ≠ 1"

    # Rule 2: Division by zero
    if "/0" in to_expr or "/ 0" in to_expr:
        return "Division by zero is undefined"

    # Rule 3: Dropping terms
    if "drop" in operation or "ignore" in operation:
        return "Cannot drop or ignore terms without justification"

    return None


def _clean_expression(expr: str) -> str:
    """Clean a mathematical expression for SymPy parsing."""
    if not expr:
        return ""

    # Remove LaTeX formatting
    expr = expr.replace("$", "")
    expr = expr.replace("\\", "")
    expr = expr.replace("{", "(")
    expr = expr.replace("}", ")")
    expr = expr.replace("^", "**")
    expr = expr.replace("×", "*")
    expr = expr.replace("÷", "/")

    for word in ["therefore", "so", "thus", "hence"]:
        expr = expr.replace(word, "").strip()

    return expr.strip()