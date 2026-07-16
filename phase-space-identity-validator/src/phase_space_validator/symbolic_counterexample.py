"""Symbolic counterexample search for controlled differential-operator claims."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import sympy as sp

from .expressions import (
    Constant,
    CrossProduct,
    Equality,
    Expression,
    Gradient,
    Power,
    Product,
    Sum,
)
from .expressions import Symbol as AstSymbol


class EvidenceLevel(StrEnum):
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    NO_COUNTEREXAMPLE_FOUND = "NO_COUNTEREXAMPLE_FOUND"


class SymbolicCounterexampleError(ValueError):
    """Stable, path-aware failure from symbolic counterexample analysis."""

    def __init__(self, code: str, path: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"


@dataclass(frozen=True)
class SymbolicContext:
    """Coordinate families used by symbolic differential operators."""

    coordinate_families: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "x": ("x1", "x2", "x3"),
            "p": ("p1", "p2", "p3"),
        }
    )

    def family(self, name: str, path: str) -> tuple[sp.Symbol, ...]:
        try:
            names = self.coordinate_families[name]
        except KeyError as exc:
            raise SymbolicCounterexampleError(
                code="UNKNOWN_SYMBOLIC_COORDINATE",
                path=path,
                message=f"no symbolic coordinate family is registered for {name!r}",
            ) from exc
        if len(names) != 3:
            raise SymbolicCounterexampleError(
                code="SYMBOLIC_CROSS_PRODUCT_REQUIRES_3D",
                path=path,
                message=f"coordinate family {name!r} contains {len(names)} components",
            )
        return tuple(sp.Symbol(component) for component in names)

    def symbol_table(self) -> dict[str, sp.Symbol]:
        return {
            name: sp.Symbol(name)
            for family in self.coordinate_families.values()
            for name in family
        }


@dataclass(frozen=True)
class CounterexampleResult:
    evidence_level: EvidenceLevel
    candidates_tested: int
    witness: str | None
    left_action: tuple[str, ...] | None
    right_action: tuple[str, ...] | None
    residual: tuple[str, ...] | None

    @property
    def counterexample_found(self) -> bool:
        return self.evidence_level is EvidenceLevel.COUNTEREXAMPLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_level": self.evidence_level.value,
            "counterexample_found": self.counterexample_found,
            "candidates_tested": self.candidates_tested,
            "witness": self.witness,
            "left_action": list(self.left_action) if self.left_action is not None else None,
            "right_action": list(self.right_action) if self.right_action is not None else None,
            "residual": list(self.residual) if self.residual is not None else None,
            "disclaimer": (
                "A counterexample disproves a universal claim. Failure to find one within the "
                "configured search space is not a proof."
            ),
        }


DEFAULT_SYMBOLIC_CONTEXT = SymbolicContext()


def expression_to_sympy(
    expression: Expression,
    context: SymbolicContext = DEFAULT_SYMBOLIC_CONTEXT,
    *,
    path: str = "$",
) -> sp.Expr:
    """Translate the scalar subset of the controlled AST into a SymPy expression."""

    symbols = context.symbol_table()

    if isinstance(expression, Constant):
        if expression.value == "pi":
            return sp.pi
        if expression.value == "i":
            return sp.I
        if isinstance(expression.value, str):
            return sp.Symbol(expression.value)
        return sp.sympify(expression.value)

    if isinstance(expression, AstSymbol):
        return symbols.get(expression.name, sp.Symbol(expression.name))

    if isinstance(expression, Product):
        return sp.Mul(
            *(
                expression_to_sympy(factor, context, path=f"{path}.factors[{index}]")
                for index, factor in enumerate(expression.factors)
            )
        )

    if isinstance(expression, Sum):
        return sp.Add(
            *(
                expression_to_sympy(term, context, path=f"{path}.terms[{index}]")
                for index, term in enumerate(expression.terms)
            )
        )

    if isinstance(expression, Power):
        base = expression_to_sympy(expression.base, context, path=f"{path}.base")
        return sp.Pow(base, expression.exponent)

    raise SymbolicCounterexampleError(
        code="UNSUPPORTED_SYMBOLIC_EXPRESSION",
        path=path,
        message=f"scalar translation is not implemented for {type(expression).__name__}",
    )


def apply_mixed_cross_gradient(
    operator: CrossProduct,
    function: sp.Expr,
    context: SymbolicContext = DEFAULT_SYMBOLIC_CONTEXT,
    *,
    path: str = "$",
) -> tuple[sp.Expr, sp.Expr, sp.Expr]:
    """Apply ``nabla_a cross nabla_b`` to a scalar function in three dimensions."""

    if not _is_unapplied_gradient(operator.left) or not _is_unapplied_gradient(operator.right):
        raise SymbolicCounterexampleError(
            code="UNSUPPORTED_SYMBOLIC_OPERATOR",
            path=path,
            message="mixed cross-gradient application requires two unapplied gradient operands",
        )

    left_variables = context.family(operator.left.space, f"{path}.left.space")
    right_variables = context.family(operator.right.space, f"{path}.right.space")

    components = (
        sp.diff(function, left_variables[1], right_variables[2])
        - sp.diff(function, left_variables[2], right_variables[1]),
        sp.diff(function, left_variables[2], right_variables[0])
        - sp.diff(function, left_variables[0], right_variables[2]),
        sp.diff(function, left_variables[0], right_variables[1])
        - sp.diff(function, left_variables[1], right_variables[0]),
    )
    return tuple(sp.simplify(component) for component in components)


def generate_bilinear_candidates(
    context: SymbolicContext = DEFAULT_SYMBOLIC_CONTEXT,
    *,
    left_space: str = "x",
    right_space: str = "p",
) -> tuple[Expression, ...]:
    """Generate deterministic degree-two witnesses ``a_i b_j``."""

    left_names = context.coordinate_families.get(left_space)
    right_names = context.coordinate_families.get(right_space)
    if left_names is None or right_names is None:
        raise SymbolicCounterexampleError(
            code="UNKNOWN_SYMBOLIC_COORDINATE",
            path="$",
            message=f"cannot generate candidates for {left_space!r} and {right_space!r}",
        )
    return tuple(
        Product(factors=(AstSymbol(left_name), AstSymbol(right_name)))
        for left_name in left_names
        for right_name in right_names
    )


def falsify_equality(
    equality: Equality,
    candidates: Sequence[Expression] | None = None,
    context: SymbolicContext = DEFAULT_SYMBOLIC_CONTEXT,
) -> CounterexampleResult:
    """Search for a witness that falsifies a supported universal operator equality."""

    operator, operator_on_left = _extract_zero_operator_claim(equality, context)
    candidate_expressions = tuple(
        candidates
        or generate_bilinear_candidates(
            context,
            left_space=operator.left.space,
            right_space=operator.right.space,
        )
    )

    for tested, candidate in enumerate(candidate_expressions, start=1):
        witness = expression_to_sympy(candidate, context, path=f"$.candidates[{tested - 1}]")
        operator_action = apply_mixed_cross_gradient(operator, witness, context, path="$.operator")
        zero_action = (sp.S.Zero, sp.S.Zero, sp.S.Zero)
        left_action = operator_action if operator_on_left else zero_action
        right_action = zero_action if operator_on_left else operator_action
        residual = tuple(
            sp.simplify(left_component - right_component)
            for left_component, right_component in zip(left_action, right_action, strict=True)
        )
        if any(component != 0 for component in residual):
            return CounterexampleResult(
                evidence_level=EvidenceLevel.COUNTEREXAMPLE,
                candidates_tested=tested,
                witness=sp.sstr(witness),
                left_action=_format_vector(left_action),
                right_action=_format_vector(right_action),
                residual=_format_vector(residual),
            )

    return CounterexampleResult(
        evidence_level=EvidenceLevel.NO_COUNTEREXAMPLE_FOUND,
        candidates_tested=len(candidate_expressions),
        witness=None,
        left_action=None,
        right_action=None,
        residual=None,
    )


def _extract_zero_operator_claim(
    equality: Equality,
    context: SymbolicContext,
) -> tuple[CrossProduct, bool]:
    if isinstance(equality.left, CrossProduct) and _is_symbolic_zero(equality.right, context):
        return equality.left, True
    if isinstance(equality.right, CrossProduct) and _is_symbolic_zero(equality.left, context):
        return equality.right, False
    raise SymbolicCounterexampleError(
        code="UNSUPPORTED_SYMBOLIC_CLAIM",
        path="$",
        message="v0.5 supports only mixed cross-gradient equalities against zero",
    )


def _is_symbolic_zero(expression: Expression, context: SymbolicContext) -> bool:
    try:
        return sp.simplify(expression_to_sympy(expression, context)) == 0
    except SymbolicCounterexampleError:
        return False


def _is_unapplied_gradient(expression: Expression) -> bool:
    return isinstance(expression, Gradient) and expression.operand is None


def _format_vector(vector: Sequence[sp.Expr]) -> tuple[str, ...]:
    return tuple(sp.sstr(sp.simplify(component)) for component in vector)
