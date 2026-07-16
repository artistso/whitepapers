from __future__ import annotations

import json
from pathlib import Path

from phase_space_validator.dimensions import dimensions_equal, format_dimensions
from phase_space_validator.models import IdentitySpec
from phase_space_validator.validator import validate_identity

ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str) -> IdentitySpec:
    data = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
    return IdentitySpec.from_dict(data)


def test_invalid_cross_gradient_reports_core_failures() -> None:
    report = validate_identity(load_example("invalid-cross-gradient.json"))
    codes = {issue.code for issue in report.issues}
    assert not report.valid
    assert {
        "TYPE_RANK_MISMATCH",
        "DIMENSION_MISMATCH",
        "OPERATOR_VALUE_MISMATCH",
        "NONINTRINSIC_CONSTRUCTION",
        "DOMAIN_MISMATCH",
    } <= codes


def test_canonical_commutator_is_structurally_consistent() -> None:
    report = validate_identity(load_example("canonical-commutator.json"))
    assert report.valid
    assert [issue.code for issue in report.issues] == ["STRUCTURALLY_CONSISTENT"]


def test_zero_dimension_exponents_are_removed() -> None:
    assert dimensions_equal({"A": 1, "L": 0}, {"A": 1})


def test_dimension_formatter() -> None:
    assert format_dimensions({"A": -1, "L": 2}) == "A^-1 L^2"


def test_negative_rank_is_rejected() -> None:
    data = {
        "name": "bad rank",
        "lhs": {"label": "lhs", "rank": -1},
        "rhs": {"label": "rhs", "rank": 0},
    }
    try:
        IdentitySpec.from_dict(data)
    except ValueError as exc:
        assert "rank" in str(exc)
    else:
        raise AssertionError("negative rank should be rejected")
