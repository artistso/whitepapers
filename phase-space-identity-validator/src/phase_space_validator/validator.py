"""Core consistency checks for proposed identities."""

from __future__ import annotations

from .dimensions import dimensions_equal, format_dimensions
from .models import IdentitySpec, Severity, ValidationIssue, ValidationReport


def validate_identity(spec: IdentitySpec) -> ValidationReport:
    """Validate a declared identity using conservative structural checks.

    This MVP does not parse arbitrary LaTeX or prove equations. It checks the
    supplied mathematical metadata and returns explicit, machine-readable
    diagnostics.
    """

    issues: list[ValidationIssue] = []
    lhs, rhs, context = spec.lhs, spec.rhs, spec.context

    if lhs.rank != rhs.rank and not context.allow_rank_coercion:
        issues.append(
            ValidationIssue(
                code="TYPE_RANK_MISMATCH",
                severity=Severity.ERROR,
                message=(
                    f"Tensor rank differs: {lhs.label!r} has rank {lhs.rank}, "
                    f"while {rhs.label!r} has rank {rhs.rank}."
                ),
            )
        )

    if not dimensions_equal(lhs.dimensions, rhs.dimensions):
        issues.append(
            ValidationIssue(
                code="DIMENSION_MISMATCH",
                severity=Severity.ERROR,
                message=(
                    f"Dimensions differ: {lhs.label!r} has "
                    f"{format_dimensions(lhs.dimensions)}, while {rhs.label!r} has "
                    f"{format_dimensions(rhs.dimensions)}."
                ),
            )
        )

    if lhs.is_operator != rhs.is_operator and not context.allow_operator_eigenvalue_equation:
        operator_side = lhs.label if lhs.is_operator else rhs.label
        value_side = rhs.label if lhs.is_operator else lhs.label
        issues.append(
            ValidationIssue(
                code="OPERATOR_VALUE_MISMATCH",
                severity=Severity.ERROR,
                message=(
                    f"{operator_side!r} is an operator but {value_side!r} is a value. "
                    "Declare an operator equation, an action on a state/function, or an "
                    "eigenvalue context."
                ),
            )
        )

    if lhs.is_operator and rhs.is_operator and lhs.differential_order != rhs.differential_order:
        issues.append(
            ValidationIssue(
                code="DIFFERENTIAL_ORDER_MISMATCH",
                severity=Severity.WARNING,
                message=(
                    f"Differential order differs: {lhs.differential_order} versus "
                    f"{rhs.differential_order}. This may be valid only with additional structure."
                ),
            )
        )

    if context.require_intrinsic:
        for side_name, obj in (("left", lhs), ("right", rhs)):
            if not obj.intrinsic:
                issues.append(
                    ValidationIssue(
                        code="NONINTRINSIC_CONSTRUCTION",
                        severity=Severity.ERROR,
                        message=(
                            f"The {side_name}-hand construction {obj.label!r} is declared "
                            "coordinate-dependent, but the context requires an intrinsic identity."
                        ),
                    )
                )

    if lhs.domain and rhs.domain and lhs.domain != rhs.domain:
        issues.append(
            ValidationIssue(
                code="DOMAIN_MISMATCH",
                severity=Severity.ERROR,
                message=f"Domains differ: {lhs.domain!r} versus {rhs.domain!r}.",
            )
        )

    if lhs.distributional != rhs.distributional:
        issues.append(
            ValidationIssue(
                code="DISTRIBUTIONAL_QUALIFICATION",
                severity=Severity.WARNING,
                message=(
                    "Only one side is marked distributional. State the test-function or "
                    "weak-equality interpretation explicitly."
                ),
            )
        )

    if not issues:
        issues.append(
            ValidationIssue(
                code="STRUCTURALLY_CONSISTENT",
                severity=Severity.INFO,
                message=(
                    "No declared rank, dimension, operator/value, covariance, domain, or "
                    "distributional inconsistency was found. This is not a proof of the identity."
                ),
            )
        )

    return ValidationReport(identity=spec.name, issues=tuple(issues))
