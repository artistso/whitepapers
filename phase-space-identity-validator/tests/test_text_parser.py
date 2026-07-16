from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from phase_space_validator.dimension_inference import check_equality_dimensions
from phase_space_validator.expressions import (
    Derivative,
    Equality,
    Gradient,
    PoissonBracket,
    Power,
    Product,
    Sum,
    Symbol,
    load_expression,
)
from phase_space_validator.symbolic_counterexample import EvidenceLevel, falsify_equality
from phase_space_validator.tensor_inference import check_equality_tensors
from phase_space_validator.text_parser import TextParseError, parse_text_expression, tokenize_text

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("text_name", "json_name"),
    [
        ("invalid-cross-gradient.txt", "invalid-cross-gradient-expression.json"),
        ("canonical-commutator.txt", "canonical-commutator-expression.json"),
        ("kronecker-contraction.txt", "kronecker-contraction-expression.json"),
        ("cross-gradient-zero.txt", "cross-gradient-zero-expression.json"),
    ],
)
def test_text_fixtures_match_existing_ast_semantics(text_name: str, json_name: str) -> None:
    text = (ROOT / "examples" / "text" / text_name).read_text(encoding="utf-8")
    parsed = parse_text_expression(text).to_dict()
    expected = load_expression(ROOT / "examples" / "ast" / json_name).to_dict()
    assert _normalize_legacy_indices(parsed) == _normalize_legacy_indices(expected)


def test_operator_precedence_and_division() -> None:
    expression = parse_text_expression("a+b*c/d")
    assert isinstance(expression, Sum)
    assert isinstance(expression.terms[1], Product)
    reciprocal = expression.terms[1].factors[-1]
    assert isinstance(reciprocal, Power)
    assert reciprocal.exponent == -1


def test_gradient_with_operand() -> None:
    expression = parse_text_expression("nabla_x(x^2)")
    assert isinstance(expression, Gradient)
    assert expression.space == "x"
    assert isinstance(expression.operand, Power)


def test_partial_derivative_call() -> None:
    expression = parse_text_expression("partial(x^3, x, 2)")
    assert isinstance(expression, Derivative)
    assert expression.variable == "x"
    assert expression.order == 2


def test_poisson_bracket() -> None:
    expression = parse_text_expression("{x_i,p_j}")
    assert isinstance(expression, PoissonBracket)


def test_compact_and_braced_indices() -> None:
    compact = parse_text_expression("delta_ij")
    braced = parse_text_expression("T^{mu}_{nu}")
    assert compact == Symbol("delta", ("_i", "_j"))
    assert braced == Symbol("T", ("^mu", "_nu"))


def test_numeric_power_is_not_an_index() -> None:
    expression = parse_text_expression("hbar^-2")
    assert isinstance(expression, Power)
    assert expression.exponent == -2


def test_explicit_multiplication_is_required() -> None:
    with pytest.raises(TextParseError) as captured:
        parse_text_expression("2 pi")
    assert captured.value.code == "EXPLICIT_MULTIPLICATION_REQUIRED"
    assert captured.value.column == 3


def test_errors_include_line_and_column() -> None:
    with pytest.raises(TextParseError) as captured:
        parse_text_expression("x +\n@")
    error = captured.value
    assert error.code == "UNEXPECTED_CHARACTER"
    assert error.line == 2
    assert error.column == 1


def test_multiple_relations_are_rejected() -> None:
    with pytest.raises(TextParseError) as captured:
        parse_text_expression("x = p = hbar")
    assert captured.value.code == "MULTIPLE_RELATIONS"


def test_tokenizer_emits_terminal_token() -> None:
    tokens = tokenize_text("x_i")
    assert [token.value for token in tokens] == ["x", "_", "i", ""]


def test_parsed_invalid_ansatz_reaches_dimension_and_tensor_engines() -> None:
    expression = parse_text_expression("nabla_x cross nabla_p = hbar^2/(2*pi)")
    assert isinstance(expression, Equality)
    dimension_report = check_equality_dimensions(expression)
    tensor_report = check_equality_tensors(expression)
    assert not dimension_report.consistent
    assert not tensor_report.consistent
    assert "TYPE_RANK_MISMATCH" in {issue.code for issue in tensor_report.issues}


def test_parsed_zero_claim_reaches_symbolic_falsifier() -> None:
    expression = parse_text_expression("nabla_x cross nabla_p = 0")
    assert isinstance(expression, Equality)
    result = falsify_equality(expression)
    assert result.evidence_level is EvidenceLevel.COUNTEREXAMPLE
    assert result.witness == "p2*x1"
    assert result.residual == ("0", "0", "1")


def _normalize_legacy_indices(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_legacy_indices(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized = {key: _normalize_legacy_indices(item) for key, item in value.items()}
    if normalized.get("type") == "symbol" and "indices" in normalized:
        normalized["indices"] = [
            index if index.startswith(("_", "^")) else f"_{index}"
            for index in normalized["indices"]
        ]
    return normalized
