"""A deliberately small arithmetic language for authored activity models.

Parameter explorations and expression repairs need to compute a number from
authored text.  ``eval`` is never an option for text that travels through a
data file, so this walks Python's own syntax tree and admits arithmetic,
comparisons, boolean connectives and a short list of pure functions — nothing
with a name it does not recognise, no attribute access, no subscripts.

The browser carries a matching evaluator (``web/learning-games/play.js``) for
live read-outs.  It is display only: every checked response is recomputed
here, from the reader's parameter values, against the authored target.
"""
from __future__ import annotations

import ast
import math
import operator
from typing import Dict, Iterable

_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_COMPARE = {
    ast.Eq: lambda a, b: math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
    ast.NotEq: lambda a, b: not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
    ast.Lt: lambda a, b: a < b and not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
    ast.LtE: lambda a, b: a < b or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
    ast.Gt: lambda a, b: a > b and not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
    ast.GtE: lambda a, b: a > b or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9),
}
FUNCTIONS = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "round": round,
    "floor": math.floor, "ceil": math.ceil, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log10": math.log10, "exp": math.exp,
}
CONSTANTS = {"pi": math.pi, "e": math.e}
# A power tower is the one way arithmetic alone can exhaust a server.
_MAX_POWER = 64
_MAX_MAGNITUDE = 1e18


class ExpressionError(ValueError):
    """The text is not an expression this language admits."""


def _normalise(text: str) -> str:
    text = str(text).strip()
    for typed, plain in (("×", "*"), ("·", "*"), ("÷", "/"), ("−", "-"), ("^", "**"),
                         ("≤", "<="), ("≥", ">="), ("≠", "!=")):
        text = text.replace(typed, plain)
    return text


def parse(text: str) -> ast.AST:
    source = _normalise(text)
    if not source or len(source) > 240:
        raise ExpressionError("expression is empty or too long")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError("not an arithmetic expression: %s" % text) from exc
    _check(tree.body)
    return tree


def _check(node: ast.AST) -> None:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ExpressionError("only numbers are allowed")
        return
    if isinstance(node, ast.Name):
        return
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        _check(node.left)
        _check(node.right)
        return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Not)):
        _check(node.operand)
        return
    if isinstance(node, ast.Compare) and all(type(op) in _COMPARE for op in node.ops):
        _check(node.left)
        for comparator in node.comparators:
            _check(comparator)
        return
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        for value in node.values:
            _check(value)
        return
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS and not node.keywords):
        for argument in node.args:
            _check(argument)
        return
    raise ExpressionError("unsupported syntax in expression")


def names(text: str) -> set:
    """Variable names the expression reads (functions and constants excluded)."""
    found = set()
    for node in ast.walk(parse(text)):
        if isinstance(node, ast.Name) and node.id not in FUNCTIONS and node.id not in CONSTANTS:
            found.add(node.id)
    return found


def evaluate(text: str, variables: Dict[str, float] = None):
    """The value of an authored expression; raises ExpressionError on failure."""
    scope = dict(CONSTANTS)
    scope.update(variables or {})
    try:
        value = _eval(parse(text).body, scope)
    except ExpressionError:
        raise
    except (ArithmeticError, ValueError, TypeError) as exc:
        raise ExpressionError("expression cannot be evaluated: %s" % exc) from exc
    if isinstance(value, bool):
        return value
    if isinstance(value, complex) or not math.isfinite(float(value)) or abs(value) > _MAX_MAGNITUDE:
        raise ExpressionError("expression leaves the supported range")
    return value


def _eval(node: ast.AST, scope: Dict[str, float]):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in scope:
            raise ExpressionError("unknown name: %s" % node.id)
        return scope[node.id]
    if isinstance(node, ast.BinOp):
        left, right = _eval(node.left, scope), _eval(node.right, scope)
        if isinstance(node.op, ast.Pow) and (abs(right) > _MAX_POWER or abs(left) > 1e6):
            raise ExpressionError("power is outside the supported range")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand, scope)
        if isinstance(node.op, ast.Not):
            return not value
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Compare):
        left = _eval(node.left, scope)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, scope)
            if not _COMPARE[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        values = (_eval(value, scope) for value in node.values)
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.Call):
        return FUNCTIONS[node.func.id](*[_eval(argument, scope) for argument in node.args])
    raise ExpressionError("unsupported syntax in expression")


def number(text: str):
    """Parse a reader's typed number: decimals, a leading sign, simple fractions."""
    cleaned = _normalise(text).replace(",", "").replace(" ", "")
    if not cleaned or len(cleaned) > 40:
        return None
    try:
        if "/" in cleaned:
            top, _, bottom = cleaned.partition("/")
            return float(top) / float(bottom)
        return float(cleaned)
    except (ValueError, ZeroDivisionError):
        return None


def same_number(given: str, expected: str) -> bool:
    left, right = number(given), number(expected)
    if left is None or right is None:
        return False
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9)


def all_numbers(values: Iterable[str]) -> bool:
    return all(number(value) is not None for value in values)
