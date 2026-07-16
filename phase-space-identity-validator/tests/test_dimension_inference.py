from __future__ import annotations

from pathlib import Path

import pytest

from phase_space_validator.dimension_inference import (
    ACTION,
    DEFAULT_REGISTRY,
    Dimension,
    DimensionInferenceError,
    check_equality_dimensions,
    infer_dimension,
)
from phase_space_validator.expressions import (
    Derivative,
    Equality,
    Gradient,
    PoissonBracket,
    Sum,
    Symbol,
    load_expression,
)

ROOT = Path(__file__).resolve().parents[1]


def test_invalid_cross_gradient_dimension_mismatch() -> None:
    expression = load_expression(ROOT / "examples/ast/invalid-cross-gradient-expression.json")
    assert isinstance(expression, Equality)
    report = check_equality_dimensions(expression)
    assert not report.consistent
    assert report.code == "DIMENSION_MISMATCH"
    assert report.left.format() == "M^-1 L^-2 T"
    assert report.right.format() == "M^2 L^4 T^-2"


def test_canonical_commutator_dimensions_match() -> None:
    expression = load_expression(ROOT / "examples/ast/canonical-commutator-expression.json")
    assert isinstance(expression, Equality)
    report = check_equality_dimensions(expression)
    assert report.consistent
    assert report.code is None
    assert report.left == ACTION
    assert report.right == ACTION


def test_canonical_poisson_bracket_is_dimensionless() -> None:
    expression = PoissonBracket(Symbol("x"), Symbol("p"))
    assert infer_dimension(expression).format() == "1"


def test_derivative_and_applied_gradient_dimensions() -> None:
    derivative = Derivative(variable="x", operand=Symbol("p"))
    gradient = Gradient(space="x", operand=Symbol("p"))
    assert infer_dimension(derivative).format() == "M T^-1"
    assert infer_dimension(gradient).format() == "M T^-1"


def test_incompatible_sum_is_rejected() -> None:
    expression = Sum((Symbol("x"), Symbol("p")))
    with pytest.raises(DimensionInferenceError) as error:
        infer_dimension(expression)
    assert error.value.code == "INCOMPATIBLE_SUM"
    assert error.value.path == "$.terms[1]"


def test_unknown_symbol_reports_path() -> None:
    with pytest.raises(DimensionInferenceError) as error:
        infer_dimension(Symbol("mystery"))
    assert error.value.code == "UNKNOWN_SYMBOL"
    assert error.value.path == "$"


def test_dimension_arithmetic_normalizes_zero_exponents() -> None:
    length = Dimension.from_mapping({"L": 1})
    assert length.multiply(length.power(-1)).format() == "1"
    assert DEFAULT_REGISTRY.coordinate_dimension("p", "$p").format() == "M L T^-1"
