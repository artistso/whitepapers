from __future__ import annotations

import json
from pathlib import Path

from phase_space_validator.expressions import (
    Constant,
    CrossProduct,
    Equality,
    Gradient,
    Power,
    Product,
    Sum,
    Symbol,
    expression_from_dict,
)
from phase_space_validator.tensor_inference import (
    IndexVariance,
    TensorContext,
    TensorIndex,
    analyze_tensor,
    check_equality_tensors,
)

ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str) -> Equality:
    data = json.loads((ROOT / "examples" / "ast" / name).read_text(encoding="utf-8"))
    expression = expression_from_dict(data)
    assert isinstance(expression, Equality)
    return expression


def issue_codes(report: object) -> set[str]:
    return {issue.code for issue in report.issues}  # type: ignore[attr-defined]


def test_index_tokens_encode_variance() -> None:
    upper = TensorIndex.from_token("^i")
    lower = TensorIndex.from_token("_j")
    default = TensorIndex.from_token("k")
    assert upper.variance is IndexVariance.CONTRAVARIANT
    assert lower.variance is IndexVariance.COVARIANT
    assert default.variance is IndexVariance.COVARIANT


def test_canonical_commutator_has_matching_rank_two_signature() -> None:
    report = check_equality_tensors(load_example("canonical-commutator-expression.json"))
    assert report.consistent
    assert report.left.rank == 2
    assert report.right.rank == 2


def test_motivating_ansatz_reports_rank_and_space_failures() -> None:
    report = check_equality_tensors(load_example("invalid-cross-gradient-expression.json"))
    assert not report.consistent
    assert {"TYPE_RANK_MISMATCH", "CROSS_PRODUCT_SPACE_MISMATCH"} <= issue_codes(report)
    assert report.left.rank == 1
    assert report.right.rank == 0


def test_kronecker_delta_contraction_removes_dummy_index() -> None:
    report = check_equality_tensors(load_example("kronecker-contraction-expression.json"))
    assert report.consistent
    assert report.left.rank == 1
    assert report.left.indices[0].name == "i"
    assert report.left.indices[0].variance is IndexVariance.CONTRAVARIANT


def test_same_variance_repetition_is_rejected() -> None:
    expression = Product(
        factors=(
            Symbol("x", indices=("_i",)),
            Symbol("p", indices=("_i",)),
        )
    )
    analysis = analyze_tensor(expression)
    assert "SAME_VARIANCE_CONTRACTION" in issue_codes(analysis)
    assert analysis.signature.rank == 2


def test_index_multiplicity_is_rejected() -> None:
    expression = Product(
        factors=(
            Symbol("x", indices=("^i",)),
            Symbol("p", indices=("_i",)),
            Symbol("x", indices=("^i",)),
        )
    )
    analysis = analyze_tensor(expression)
    assert "INDEX_MULTIPLICITY" in issue_codes(analysis)


def test_cross_product_requires_three_dimensions() -> None:
    expression = CrossProduct(
        left=Symbol("x", indices=("i",)),
        right=Symbol("p", indices=("j",)),
    )
    context = TensorContext(
        space_dimensions={"spatial": 2, "position": 2, "momentum": 2}
    )
    analysis = analyze_tensor(expression, context=context)
    assert "CROSS_PRODUCT_REQUIRES_3D" in issue_codes(analysis)


def test_cross_product_requires_vectors() -> None:
    expression = CrossProduct(left=Constant(1), right=Symbol("x", indices=("i",)))
    analysis = analyze_tensor(expression)
    assert "CROSS_PRODUCT_REQUIRES_VECTORS" in issue_codes(analysis)


def test_sum_requires_matching_free_indices() -> None:
    expression = Sum(
        terms=(
            Symbol("x", indices=("i",)),
            Symbol("x", indices=("j",)),
        )
    )
    analysis = analyze_tensor(expression)
    assert "TENSOR_SUM_MISMATCH" in issue_codes(analysis)


def test_non_scalar_power_is_not_silently_defined() -> None:
    expression = Power(base=Symbol("x", indices=("i",)), exponent=2)
    analysis = analyze_tensor(expression)
    assert "TENSOR_POWER_UNDEFINED" in issue_codes(analysis)


def test_unknown_tensor_symbol_is_reported() -> None:
    analysis = analyze_tensor(Symbol("mystery", indices=("i",)))
    assert "UNKNOWN_TENSOR_SYMBOL" in issue_codes(analysis)


def test_gradient_of_scalar_has_rank_one() -> None:
    analysis = analyze_tensor(Gradient(space="x", operand=Constant(1)))
    assert analysis.signature.rank == 1
    assert not analysis.issues
