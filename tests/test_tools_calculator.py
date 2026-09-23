"""Comprehensive tests for the safe deterministic AST calculator.

Covers:
- Arithmetic operations, order of operations, precedence
- Math constants (pi, e, tau)
- Whitelisted functions (sqrt, sin, cos, abs, round, log, pow, etc.)
- Variable inputs mapping
- Fuzz and security tests:
  - Rejection of attribute access (no '.')
  - Rejection of imports (__import__, import)
  - Rejection of unknown names and builtins (eval, exec, os, sys)
  - Rejection of 9**9**9 (magnitude & exponent protection)
  - Rejection of formulas exceeding 500 characters
  - Division by zero handling
- Audited tool execution & audit log verification
"""

import math
import pytest

from tools.calculator import (
    MAX_FORMULA_LENGTH,
    CalculateArgs,
    CalculateResult,
    calculate,
    evaluate_expression,
)
from tools.registry import ToolContext


# ==============================================================================
# 1. Correct arithmetic and mathematical evaluations
# ==============================================================================

def test_calculator_basic_arithmetic():
    assert evaluate_expression("2 + 2") == 4
    assert evaluate_expression("10 - 4.5") == 5.5
    assert evaluate_expression("3 * 7") == 21
    assert evaluate_expression("15 / 3") == 5.0
    assert evaluate_expression("17 // 3") == 5
    assert evaluate_expression("17 % 5") == 2
    assert evaluate_expression("2 ** 8") == 256
    assert evaluate_expression("-5 + 10") == 5
    assert evaluate_expression("-(3 * 4)") == -12


def test_calculator_operator_precedence():
    assert evaluate_expression("2 + 3 * 4") == 14
    assert evaluate_expression("(2 + 3) * 4") == 20
    assert evaluate_expression("2 ** 3 ** 2") == 512  # Right-associative exponentiation


def test_calculator_math_constants():
    assert evaluate_expression("pi") == math.pi
    assert evaluate_expression("e") == math.e
    assert evaluate_expression("tau") == math.tau
    assert abs(evaluate_expression("2 * pi * 10") - (2 * math.pi * 10)) < 1e-9


def test_calculator_whitelisted_functions():
    assert evaluate_expression("sqrt(144)") == 12.0
    assert evaluate_expression("abs(-42.5)") == 42.5
    assert evaluate_expression("round(3.14159, 2)") == 3.14
    assert evaluate_expression("floor(4.9)") == 4
    assert evaluate_expression("ceil(4.1)") == 5
    assert evaluate_expression("min(5, 2, 9)") == 2
    assert evaluate_expression("max(5, 2, 9)") == 9
    assert evaluate_expression("hypot(3, 4)") == 5.0
    assert evaluate_expression("log(e)") == 1.0
    assert evaluate_expression("log10(1000)") == 3.0


def test_calculator_variable_inputs():
    variables = {"radius": 7.0, "height": 10.0}
    # Cylinder volume: pi * r^2 * h
    res = evaluate_expression("pi * (radius ** 2) * height", variables=variables)
    expected = math.pi * (7.0 ** 2) * 10.0
    assert abs(res - expected) < 1e-9


# ==============================================================================
# 2. Security, Fuzz, and Magnitude Hardening Tests
# ==============================================================================

def test_calculator_rejects_attribute_access():
    """Attribute access ('.' operator) must be strictly forbidden."""
    with pytest.raises(ValueError, match="Attribute access"):
        evaluate_expression("().__class__.__base__")

    with pytest.raises(ValueError, match="Attribute"):
        evaluate_expression("(1).real")

    with pytest.raises(ValueError, match="Attribute"):
        evaluate_expression("math.sqrt(4)")


def test_calculator_rejects_imports_and_builtins():
    """Imports and dangerous built-ins must be strictly rejected."""
    with pytest.raises(ValueError, match="not in the authorized math function whitelist"):
        evaluate_expression("__import__('os')")

    with pytest.raises(ValueError, match="Attribute function calls|Attribute access"):
        evaluate_expression("__import__('os').system('dir')")

    with pytest.raises(ValueError, match="not in the authorized math function whitelist"):
        evaluate_expression("eval('2 + 2')")

    with pytest.raises(ValueError, match="not in the authorized math function whitelist"):
        evaluate_expression("open('/etc/passwd')")


def test_calculator_rejects_unapproved_identifiers():
    """Any name not in constants or inputs must be rejected."""
    with pytest.raises(ValueError, match="Unknown or unapproved identifier 'x'"):
        evaluate_expression("x + 5")


def test_calculator_rejects_power_bomb_dos():
    """Magnitude limits must reject 9**9**9 or huge exponents to prevent CPU / memory exhaustion."""
    # Exponent too large
    with pytest.raises(ValueError, match="Exponent magnitude .* exceeds safe limit"):
        evaluate_expression("2 ** 1000000")

    # Base large and exponent large
    with pytest.raises(ValueError, match="Exponentiation result exceeds safe magnitude limit"):
        evaluate_expression("99999 ** 20")

    # 9**9**9
    with pytest.raises(ValueError, match="exceeds safe.*limit"):
        evaluate_expression("9 ** 9 ** 9")


def test_calculator_rejects_long_input():
    """Input length exceeding 500 characters must be rejected."""
    long_formula = "1 + " * 200 + "1"  # > 600 chars
    assert len(long_formula) > MAX_FORMULA_LENGTH
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        evaluate_expression(long_formula)


def test_calculator_division_by_zero():
    """Zero division must raise ZeroDivisionError safely."""
    with pytest.raises(ZeroDivisionError, match="Division by zero"):
        evaluate_expression("100 / 0")

    with pytest.raises(ZeroDivisionError, match="Division by zero"):
        evaluate_expression("100 // 0")

    with pytest.raises(ZeroDivisionError, match="Division by zero"):
        evaluate_expression("100 % 0")


def test_calculator_rejects_empty_or_non_string():
    with pytest.raises(ValueError, match="cannot be empty"):
        evaluate_expression("   ")

    with pytest.raises(TypeError, match="must be a string"):
        evaluate_expression(12345)


# ==============================================================================
# 3. Audited Tool Execution
# ==============================================================================

def test_calculate_tool_execution():
    ctx = ToolContext(user_id="eng_01", role="engineer", clearance="INTERNAL", run_id="run_calc_01")
    args = CalculateArgs(
        formula="sqrt(force / area)",
        inputs={"force": 1000.0, "area": 10.0},
        units="MPa",
        assumptions="Uniform stress distribution",
    )

    res = calculate(args, ctx)
    assert isinstance(res, CalculateResult)
    assert res.result == 10.0
    assert res.units == "MPa"
    assert res.assumptions == "Uniform stress distribution"
