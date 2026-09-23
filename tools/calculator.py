"""Safe deterministic AST calculator for Sovereign AI Workbench.

Implements SEC-03, SEC-14, and 02_DESIGN_DOC.md §7.4:
- AST-based evaluation with strict allowlist of node types and functions.
- Strictly rejects attribute access (no '.'), imports, lambdas, comprehensions.
- Magnitude limits: rejects 9**9**9, exponents > 1000, and results > 1e100.
- Input length capped at 500 characters.
- Structured output: {inputs, formula, result, units, assumptions}.
"""

import ast
import math
import operator
from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel, Field

from tools.registry import ToolContext, audited_tool

# Maximum character length for mathematical formulas
MAX_FORMULA_LENGTH = 500

# Maximum magnitude to prevent CPU / memory exhaustion
MAX_EXPONENT_MAGNITUDE = 1000
MAX_RESULT_MAGNITUDE = 1e100

MATH_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

MATH_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "sqrt": math.sqrt,
    "cbrt": getattr(math, "cbrt", lambda x: math.pow(x, 1 / 3)),
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "pow": pow,
    "hypot": math.hypot,
    "degrees": math.degrees,
    "radians": math.radians,
    "min": min,
    "max": max,
}

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}


class SafeEvaluator(ast.NodeVisitor):
    """Safe AST visitor that evaluates expressions using only allowed primitives."""

    def __init__(self, variables: Dict[str, Union[int, float]]):
        self.variables = variables

    def visit(self, node: ast.AST) -> Union[int, float, bool]:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST):
        raise ValueError(
            f"Disallowed expression construct '{node.__class__.__name__}'. "
            "Only safe arithmetic operations and whitelisted math functions are permitted."
        )

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise ValueError(f"Disallowed constant type '{type(node.value).__name__}' in formula.")

    def visit_Name(self, node: ast.Name):
        if not isinstance(node.ctx, ast.Load):
            raise ValueError(f"Disallowed variable context '{node.ctx.__class__.__name__}'.")

        name = node.id
        if name in MATH_CONSTANTS:
            return MATH_CONSTANTS[name]
        if name in self.variables:
            val = self.variables[name]
            if not isinstance(val, (int, float)):
                raise ValueError(f"Variable '{name}' must be numeric, got {type(val).__name__}.")
            return val

        raise ValueError(f"Unknown or unapproved identifier '{name}'.")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in UNARY_OPERATORS:
            raise ValueError(f"Disallowed unary operator '{op_type.__name__}'.")
        operand = self.visit(node.operand)
        return UNARY_OPERATORS[op_type](operand)

    def visit_BinOp(self, node: ast.BinOp):
        op_type = type(node.op)
        if op_type not in BINARY_OPERATORS:
            raise ValueError(f"Disallowed binary operator '{op_type.__name__}'.")

        left = self.visit(node.left)
        right = self.visit(node.right)

        # Division by zero checks
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Division by zero in mathematical expression.")

        # Power / exponent limits (prevents 9**9**9 DoS)
        if op_type is ast.Pow:
            if abs(right) > MAX_EXPONENT_MAGNITUDE:
                raise ValueError(
                    f"Exponent magnitude {right} exceeds safe limit ({MAX_EXPONENT_MAGNITUDE})."
                )
            # Pre-computation magnitude check for large base and exponent
            if abs(left) > 10000 and right > 10:
                raise ValueError(f"Exponentiation result exceeds safe magnitude limit ({MAX_RESULT_MAGNITUDE}).")

        try:
            result = BINARY_OPERATORS[op_type](left, right)
        except OverflowError:
            raise ValueError("Numerical calculation overflow.")

        if isinstance(result, (int, float)) and abs(result) > MAX_RESULT_MAGNITUDE:
            raise ValueError(f"Calculation result exceeds maximum safe magnitude ({MAX_RESULT_MAGNITUDE}).")

        return result

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Attribute function calls (e.g. object.method()) are strictly forbidden.")

        func_name = node.func.id
        if func_name not in MATH_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not in the authorized math function whitelist.")

        args = [self.visit(arg) for arg in node.args]
        if node.keywords:
            raise ValueError("Keyword arguments are not supported in math function calls.")

        try:
            result = MATH_FUNCTIONS[func_name](*args)
        except Exception as e:
            raise ValueError(f"Error evaluating math function '{func_name}': {e}")

        if isinstance(result, (int, float)) and abs(result) > MAX_RESULT_MAGNITUDE:
            raise ValueError(f"Function '{func_name}' result exceeds maximum safe magnitude ({MAX_RESULT_MAGNITUDE}).")

        return result

    # Explicit rejection methods for high-risk AST nodes
    def visit_Attribute(self, node: ast.Attribute):
        raise ValueError("Attribute access ('.' operator) is strictly forbidden for security.")

    def visit_Subscript(self, node: ast.Subscript):
        raise ValueError("Subscript indexing ('[]') is strictly forbidden in calculator expressions.")

    def visit_Import(self, node: ast.Import):
        raise ValueError("Imports are strictly forbidden in calculator expressions.")

    def visit_ImportFrom(self, node: ast.ImportFrom):
        raise ValueError("Imports are strictly forbidden in calculator expressions.")


def evaluate_expression(formula: str, variables: Optional[Dict[str, Union[int, float]]] = None) -> Union[int, float]:
    """Parse and safely evaluate a mathematical expression string using restricted AST traversal."""
    if not isinstance(formula, str):
        raise TypeError(f"Formula must be a string, got {type(formula).__name__}.")

    stripped = formula.strip()
    if not stripped:
        raise ValueError("Formula expression cannot be empty.")

    if len(stripped) > MAX_FORMULA_LENGTH:
        raise ValueError(f"Formula length ({len(stripped)}) exceeds maximum limit of {MAX_FORMULA_LENGTH} characters.")

    try:
        parsed_tree = ast.parse(stripped, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in mathematical expression: {e}")

    evaluator = SafeEvaluator(variables or {})
    result = evaluator.visit(parsed_tree)

    if isinstance(result, bool):
        return int(result)
    return result


class CalculateArgs(BaseModel):
    """Input arguments for calculate tool."""

    formula: str = Field(description="Mathematical formula or expression (e.g. 'pi * (radius ** 2)')")
    inputs: Dict[str, Union[int, float]] = Field(
        default_factory=dict,
        description="Named input variables mapped to numeric values (e.g. {'radius': 5.0})",
    )
    units: Optional[str] = Field(default=None, description="Optional engineering units for the result (e.g. 'mm', 'MPa', 'kN')")
    assumptions: Optional[str] = Field(default=None, description="Engineering assumptions or design parameters")


class CalculateResult(BaseModel):
    """Structured result of calculation."""

    formula: str
    inputs: Dict[str, Union[int, float]]
    result: Union[int, float]
    units: Optional[str] = None
    assumptions: Optional[str] = None


@audited_tool(name="calculate", side_effects=False, needs_role=None)
def calculate(args: CalculateArgs, ctx: ToolContext) -> CalculateResult:
    """Safely calculate numerical engineering results using deterministic AST evaluation."""
    res = evaluate_expression(args.formula, variables=args.inputs)
    return CalculateResult(
        formula=args.formula,
        inputs=args.inputs,
        result=res,
        units=args.units,
        assumptions=args.assumptions,
    )
