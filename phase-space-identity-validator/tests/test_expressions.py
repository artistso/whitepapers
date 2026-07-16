from __future__ import annotations

import json
from pathlib import Path

import pytest

from phase_space_validator.expressions import (
    Commutator,
    Derivative,
    Equality,
    ExpressionParseError,
    Gradient,
    Product,
    Symbol,
    expression_depth,
    expression_from_dict,
    load_expression,
    walk_expression,
)

ROOT = Path(__file__).resolve().parents[1]


def test_invalid_cross_gradient_round_trip() -> None:
    expression = load_expression(ROOT / "examples/ast/invalid-cross-gradient-expression.json")
    assert isinstance(expression, Equality)
    assert expression.kind == "equality"
    assert len(walk_expression(expression)) == 11
    assert expression_depth(expression) == 5
    assert expression_from_dict(expression.to_dict()) == expression


def test_canonical_commutator_shape() -> None:
    expression = load_expression(ROOT / "examples/ast/canonical-commutator-expression.json")
    assert isinstance(expression, Equality)
    assert isinstance(expression.left, Commutator)
    assert isinstance(expression.right, Product)
    assert len(expression.right.factors) == 4


def test_derivative_and_gradient_serialization() -> None:
    expression = Derivative(
        variable="x",
        operand=Gradient(space="p", operand=Symbol("f")),
        order=2,
    )
    assert expression_from_dict(expression.to_dict()) == expression


def test_unknown_fields_are_rejected_with_path() -> None:
    with pytest.raises(ExpressionParseError, match=r"\$: unknown fields typo"):
        expression_from_dict({"type": "symbol", "name": "x", "typo": 1})


def test_unknown_node_type_is_rejected() -> None:
    with pytest.raises(ExpressionParseError, match="unsupported expression type"):
        expression_from_dict({"type": "curlish"})


def test_single_factor_product_is_rejected() -> None:
    with pytest.raises(ExpressionParseError, match="product requires at least two factors"):
        expression_from_dict(
            {
                "type": "product",
                "factors": [{"type": "symbol", "name": "x"}],
            }
        )


def test_noninteger_power_is_rejected() -> None:
    with pytest.raises(ExpressionParseError, match=r"\$\.exponent: expected an integer"):
        expression_from_dict(
            {
                "type": "power",
                "base": {"type": "symbol", "name": "x"},
                "exponent": 0.5,
            }
        )


def test_expression_json_is_canonical() -> None:
    expression = load_expression(ROOT / "examples/ast/canonical-commutator-expression.json")
    encoded = json.dumps(expression.to_dict(), sort_keys=True)
    assert "commutator" in encoded
    assert "canonical" not in encoded
