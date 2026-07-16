from __future__ import annotations

import json
from pathlib import Path

import pytest
import sympy as sp

from phase_space_validator.expressions import (
    Constant,
    CrossProduct,
    Equality,
    Gradient,
    Product,
    Symbol,
    expression_from_dict,
)
from phase_space_validator.symbolic_counterexample import (
    EvidenceLevel,
    SymbolicCounterexampleError,
    apply_mixed_cross_gradient,
    expression_to_sympy,
    falsify_equality,
    generate_bilinear_candidates,
)

ROOT = Path(__file__).resolve().parents[1]


def load_claim() -> Equality:
    data = json.loads(
        (ROOT / "examples" / "ast" / "cross-gradient-zero-expression.json").read_text(
            encoding="utf-8"
        )
    )
    expression = expression_from_dict(data)
    assert isinstance(expression, Equality)
    return expression


def mixed_operator() -> CrossProduct:
    return CrossProduct(left=Gradient(space="x"), right=Gradient(space="p"))


def test_scalar_ast_translation() -> None:
    expression = Product(factors=(Symbol("x1"), Symbol("p2")))
    assert expression_to_sympy(expression) == sp.Symbol("x1") * sp.Symbol("p2")


def test_cross_gradient_annihilates_diagonal_bilinear() -> None:
    x1, p1 = sp.symbols("x1 p1")
    assert apply_mixed_cross_gradient(mixed_operator(), x1 * p1) == (0, 0, 0)


def test_cross_gradient_detects_off_diagonal_bilinear() -> None:
    x1, p2 = sp.symbols("x1 p2")
    assert apply_mixed_cross_gradient(mixed_operator(), x1 * p2) == (0, 0, 1)


def test_candidate_order_is_deterministic() -> None:
    candidates = generate_bilinear_candidates()
    assert candidates[0].to_dict() == {
        "type": "product",
        "factors": [
            {"type": "symbol", "name": "x1"},
            {"type": "symbol", "name": "p1"},
        ],
    }
    assert candidates[1].to_dict()["factors"][1]["name"] == "p2"


def test_falsifier_finds_x1_p2_counterexample() -> None:
    result = falsify_equality(load_claim())
    assert result.evidence_level is EvidenceLevel.COUNTEREXAMPLE
    assert result.counterexample_found
    assert result.candidates_tested == 2
    assert result.witness == "p2*x1"
    assert result.left_action == ("0", "0", "1")
    assert result.right_action == ("0", "0", "0")
    assert result.residual == ("0", "0", "1")


def test_no_counterexample_result_is_not_a_proof() -> None:
    claim = load_claim()
    diagonal_only = (Product(factors=(Symbol("x1"), Symbol("p1"))),)
    result = falsify_equality(claim, diagonal_only)
    assert result.evidence_level is EvidenceLevel.NO_COUNTEREXAMPLE_FOUND
    assert not result.counterexample_found
    assert result.to_dict()["disclaimer"].endswith("is not a proof.")


def test_unsupported_claim_raises_stable_error() -> None:
    claim = Equality(left=Symbol("x"), right=Constant(0))
    with pytest.raises(SymbolicCounterexampleError) as error:
        falsify_equality(claim)
    assert error.value.code == "UNSUPPORTED_SYMBOLIC_CLAIM"
