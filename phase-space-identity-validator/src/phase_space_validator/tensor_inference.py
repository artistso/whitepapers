"""Tensor-rank and free-index inference over the controlled expression AST."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .expressions import (
    Commutator,
    Constant,
    CrossProduct,
    Derivative,
    Equality,
    Expression,
    Gradient,
    PoissonBracket,
    Power,
    Product,
    Sum,
    Symbol,
    TensorProduct,
    WedgeProduct,
)
from .models import Severity


class IndexVariance(StrEnum):
    COVARIANT = "down"
    CONTRAVARIANT = "up"

    @property
    def marker(self) -> str:
        return "_" if self is IndexVariance.COVARIANT else "^"

    @property
    def opposite(self) -> IndexVariance:
        if self is IndexVariance.COVARIANT:
            return IndexVariance.CONTRAVARIANT
        return IndexVariance.COVARIANT


@dataclass(frozen=True)
class TensorIndex:
    """One free tensor index with variance and vector-space identity."""

    name: str
    variance: IndexVariance = IndexVariance.COVARIANT
    space: str = "spatial"
    anonymous: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("index name must not be empty")
        if not self.space.strip():
            raise ValueError("index space must not be empty")

    @classmethod
    def from_token(
        cls,
        token: str,
        *,
        default_variance: IndexVariance = IndexVariance.COVARIANT,
        space: str = "spatial",
    ) -> TensorIndex:
        if not token.strip():
            raise ValueError("index token must not be empty")
        variance = default_variance
        name = token
        if token.startswith("^"):
            variance = IndexVariance.CONTRAVARIANT
            name = token[1:]
        elif token.startswith("_"):
            variance = IndexVariance.COVARIANT
            name = token[1:]
        if not name.strip():
            raise ValueError("index token must contain a name")
        return cls(name=name, variance=variance, space=space)

    @property
    def token(self) -> str:
        return f"{self.variance.marker}{self.name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "variance": self.variance.value,
            "space": self.space,
            "anonymous": self.anonymous,
        }


@dataclass(frozen=True)
class TensorSignature:
    """Best-effort tensor signature represented by its free indices."""

    indices: tuple[TensorIndex, ...] = ()

    @classmethod
    def scalar(cls) -> TensorSignature:
        return cls()

    @property
    def rank(self) -> int:
        return len(self.indices)

    @property
    def is_scalar(self) -> bool:
        return not self.indices

    def format(self) -> str:
        if self.is_scalar:
            return "scalar"
        rendered = " ".join(
            "*" if index.anonymous else f"{index.variance.marker}{index.name}"
            for index in self.indices
        )
        spaces = sorted({index.space for index in self.indices})
        return f"rank {self.rank} [{rendered}] in {', '.join(spaces)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "formatted": self.format(),
            "free_indices": [index.to_dict() for index in self.indices],
        }


@dataclass(frozen=True)
class TensorSymbolSpec:
    rank: int
    default_variance: tuple[IndexVariance, ...] = ()
    space: str = "spatial"

    def __post_init__(self) -> None:
        if self.rank < 0:
            raise ValueError("tensor symbol rank must be non-negative")
        if self.default_variance and len(self.default_variance) != self.rank:
            raise ValueError("default variance count must equal tensor rank")
        if not self.space.strip():
            raise ValueError("tensor symbol space must not be empty")


@dataclass(frozen=True)
class TensorContext:
    space_dimensions: Mapping[str, int] = field(
        default_factory=lambda: {
            "spatial": 3,
            "position": 3,
            "momentum": 3,
        }
    )

    def dimension_for_space(self, space: str) -> int | None:
        return self.space_dimensions.get(space)


@dataclass(frozen=True)
class TensorRegistry:
    symbols: Mapping[str, TensorSymbolSpec] = field(default_factory=dict)
    coordinate_spaces: Mapping[str, str] = field(default_factory=dict)

    def symbol_spec(self, name: str) -> TensorSymbolSpec | None:
        return self.symbols.get(name)

    def coordinate_space(self, name: str) -> str:
        return self.coordinate_spaces.get(name, name)


@dataclass(frozen=True)
class TensorIssue:
    code: str
    path: str
    message: str
    severity: Severity = Severity.ERROR

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class TensorAnalysis:
    signature: TensorSignature
    issues: tuple[TensorIssue, ...] = ()


@dataclass(frozen=True)
class TensorCheckReport:
    left: TensorSignature
    right: TensorSignature
    issues: tuple[TensorIssue, ...]

    @property
    def consistent(self) -> bool:
        return not any(issue.severity is Severity.ERROR for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "consistent": self.consistent,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
        }


DEFAULT_TENSOR_REGISTRY = TensorRegistry(
    symbols={
        "x": TensorSymbolSpec(rank=1),
        "p": TensorSymbolSpec(rank=1),
        "hbar": TensorSymbolSpec(rank=0),
        "delta": TensorSymbolSpec(rank=2),
        "epsilon": TensorSymbolSpec(rank=3),
        "I": TensorSymbolSpec(rank=0),
    },
    coordinate_spaces={
        "x": "position",
        "p": "momentum",
    },
)

DEFAULT_TENSOR_CONTEXT = TensorContext()


def analyze_tensor(
    expression: Expression,
    registry: TensorRegistry = DEFAULT_TENSOR_REGISTRY,
    context: TensorContext = DEFAULT_TENSOR_CONTEXT,
    *,
    path: str = "$",
) -> TensorAnalysis:
    """Infer a best-effort tensor signature and accumulate structural issues."""

    if isinstance(expression, Constant):
        return TensorAnalysis(TensorSignature.scalar())

    if isinstance(expression, Symbol):
        return _analyze_symbol(expression, registry, path)

    if isinstance(expression, Derivative):
        operand = analyze_tensor(expression.operand, registry, context, path=f"{path}.operand")
        space = registry.coordinate_space(expression.variable)
        derivative_indices = tuple(
            _anonymous_index(f"d{order}", space)
            for order in range(1, expression.order + 1)
        )
        return TensorAnalysis(
            TensorSignature(derivative_indices + operand.signature.indices),
            operand.issues,
        )

    if isinstance(expression, Gradient):
        space = registry.coordinate_space(expression.space)
        gradient_index = _anonymous_index("grad", space)
        if expression.operand is None:
            return TensorAnalysis(TensorSignature((gradient_index,)))
        operand = analyze_tensor(expression.operand, registry, context, path=f"{path}.operand")
        return TensorAnalysis(
            TensorSignature((gradient_index,) + operand.signature.indices),
            operand.issues,
        )

    if isinstance(expression, CrossProduct):
        left = analyze_tensor(expression.left, registry, context, path=f"{path}.left")
        right = analyze_tensor(expression.right, registry, context, path=f"{path}.right")
        issues = [*left.issues, *right.issues]
        if left.signature.rank != 1 or right.signature.rank != 1:
            issues.append(
                TensorIssue(
                    code="CROSS_PRODUCT_REQUIRES_VECTORS",
                    path=path,
                    message=(
                        "cross product requires rank-1 operands; received "
                        f"ranks {left.signature.rank} and {right.signature.rank}"
                    ),
                )
            )
        left_space = _single_space(left.signature)
        right_space = _single_space(right.signature)
        if left_space and right_space and left_space != right_space:
            issues.append(
                TensorIssue(
                    code="CROSS_PRODUCT_SPACE_MISMATCH",
                    path=path,
                    message=f"cross-product operands belong to {left_space!r} and {right_space!r}",
                )
            )
        for side, space in (("left", left_space), ("right", right_space)):
            if space is None:
                continue
            dimension = context.dimension_for_space(space)
            if dimension is not None and dimension != 3:
                issues.append(
                    TensorIssue(
                        code="CROSS_PRODUCT_REQUIRES_3D",
                        path=f"{path}.{side}",
                        message=f"cross product is configured only in 3D, but {space!r} is {dimension}D",
                    )
                )
        output_space = left_space if left_space == right_space and left_space else "mixed"
        return TensorAnalysis(
            TensorSignature((_anonymous_index("cross", output_space),)),
            tuple(issues),
        )

    if isinstance(expression, TensorProduct):
        return _analyze_binary_join(expression, registry, context, path, contract=False)

    if isinstance(expression, WedgeProduct):
        return _analyze_binary_join(expression, registry, context, path, contract=False)

    if isinstance(expression, (Commutator, PoissonBracket)):
        return _analyze_binary_join(expression, registry, context, path, contract=True)

    if isinstance(expression, Product):
        analyses = tuple(
            analyze_tensor(factor, registry, context, path=f"{path}.factors[{index}]")
            for index, factor in enumerate(expression.factors)
        )
        indices = tuple(index for analysis in analyses for index in analysis.signature.indices)
        free, contraction_issues = _contract_indices(indices, path)
        issues = tuple(issue for analysis in analyses for issue in analysis.issues)
        return TensorAnalysis(TensorSignature(free), issues + contraction_issues)

    if isinstance(expression, Sum):
        analyses = tuple(
            analyze_tensor(term, registry, context, path=f"{path}.terms[{index}]")
            for index, term in enumerate(expression.terms)
        )
        reference = analyses[0].signature
        issues = [issue for analysis in analyses for issue in analysis.issues]
        for index, analysis in enumerate(analyses[1:], start=1):
            if not signatures_compatible(reference, analysis.signature):
                issues.append(
                    TensorIssue(
                        code="TENSOR_SUM_MISMATCH",
                        path=f"{path}.terms[{index}]",
                        message=(
                            f"term has {analysis.signature.format()}, expected {reference.format()}"
                        ),
                    )
                )
        return TensorAnalysis(reference, tuple(issues))

    if isinstance(expression, Power):
        base = analyze_tensor(expression.base, registry, context, path=f"{path}.base")
        issues = list(base.issues)
        if expression.exponent == 0:
            return TensorAnalysis(TensorSignature.scalar(), tuple(issues))
        if expression.exponent == 1:
            return base
        if not base.signature.is_scalar:
            issues.append(
                TensorIssue(
                    code="TENSOR_POWER_UNDEFINED",
                    path=path,
                    message=(
                        "ordinary integer powers are defined here only for scalars; "
                        f"base has rank {base.signature.rank}"
                    ),
                )
            )
        return TensorAnalysis(base.signature, tuple(issues))

    if isinstance(expression, Equality):
        report = check_equality_tensors(expression, registry, context, path=path)
        return TensorAnalysis(report.left, report.issues)

    return TensorAnalysis(
        TensorSignature.scalar(),
        (
            TensorIssue(
                code="UNSUPPORTED_TENSOR_NODE",
                path=path,
                message=f"tensor inference is not implemented for {type(expression).__name__}",
            ),
        ),
    )


def check_equality_tensors(
    equality: Equality,
    registry: TensorRegistry = DEFAULT_TENSOR_REGISTRY,
    context: TensorContext = DEFAULT_TENSOR_CONTEXT,
    *,
    path: str = "$",
) -> TensorCheckReport:
    left = analyze_tensor(equality.left, registry, context, path=f"{path}.left")
    right = analyze_tensor(equality.right, registry, context, path=f"{path}.right")
    issues = [*left.issues, *right.issues]

    if left.signature.rank != right.signature.rank:
        issues.append(
            TensorIssue(
                code="TYPE_RANK_MISMATCH",
                path=path,
                message=(
                    f"left side has rank {left.signature.rank}, "
                    f"right side has rank {right.signature.rank}"
                ),
            )
        )
    elif not signatures_compatible(left.signature, right.signature):
        issues.append(
            TensorIssue(
                code="FREE_INDEX_MISMATCH",
                path=path,
                message=(
                    f"left side has {left.signature.format()}, "
                    f"right side has {right.signature.format()}"
                ),
            )
        )

    return TensorCheckReport(left.signature, right.signature, tuple(issues))


def signatures_compatible(left: TensorSignature, right: TensorSignature) -> bool:
    """Compare signatures, treating anonymous indices as name wildcards."""

    if left.rank != right.rank:
        return False
    for left_index, right_index in zip(left.indices, right.indices, strict=True):
        if left_index.space != right_index.space:
            return False
        if left_index.variance != right_index.variance:
            return False
        if not left_index.anonymous and not right_index.anonymous:
            if left_index.name != right_index.name:
                return False
    return True


def _analyze_symbol(
    expression: Symbol,
    registry: TensorRegistry,
    path: str,
) -> TensorAnalysis:
    spec = registry.symbol_spec(expression.name)
    issues: list[TensorIssue] = []
    if spec is None:
        inferred_rank = len(expression.indices)
        issues.append(
            TensorIssue(
                code="UNKNOWN_TENSOR_SYMBOL",
                path=path,
                message=f"no tensor metadata is registered for symbol {expression.name!r}",
            )
        )
        spec = TensorSymbolSpec(rank=inferred_rank, space=expression.space or "spatial")

    if expression.indices and len(expression.indices) != spec.rank:
        issues.append(
            TensorIssue(
                code="INDEX_COUNT_MISMATCH",
                path=f"{path}.indices",
                message=(
                    f"symbol {expression.name!r} has declared rank {spec.rank} "
                    f"but {len(expression.indices)} indices were supplied"
                ),
            )
        )

    space = expression.space or spec.space
    indices: list[TensorIndex] = []
    if expression.indices:
        for position, token in enumerate(expression.indices):
            default = (
                spec.default_variance[position]
                if position < len(spec.default_variance)
                else IndexVariance.COVARIANT
            )
            try:
                indices.append(TensorIndex.from_token(token, default_variance=default, space=space))
            except ValueError as exc:
                issues.append(
                    TensorIssue(
                        code="INVALID_INDEX_TOKEN",
                        path=f"{path}.indices[{position}]",
                        message=str(exc),
                    )
                )
    else:
        defaults = spec.default_variance or (IndexVariance.COVARIANT,) * spec.rank
        indices.extend(
            _anonymous_index(f"{expression.name}{position}", space, variance)
            for position, variance in enumerate(defaults)
        )

    return TensorAnalysis(TensorSignature(tuple(indices)), tuple(issues))


def _analyze_binary_join(
    expression: Commutator | PoissonBracket | TensorProduct | WedgeProduct,
    registry: TensorRegistry,
    context: TensorContext,
    path: str,
    *,
    contract: bool,
) -> TensorAnalysis:
    left = analyze_tensor(expression.left, registry, context, path=f"{path}.left")
    right = analyze_tensor(expression.right, registry, context, path=f"{path}.right")
    indices = left.signature.indices + right.signature.indices
    contraction_issues: tuple[TensorIssue, ...] = ()
    if contract:
        indices, contraction_issues = _contract_indices(indices, path)
    return TensorAnalysis(
        TensorSignature(indices),
        left.issues + right.issues + contraction_issues,
    )


def _contract_indices(
    indices: tuple[TensorIndex, ...],
    path: str,
) -> tuple[tuple[TensorIndex, ...], tuple[TensorIssue, ...]]:
    groups: dict[tuple[str, str], list[tuple[int, TensorIndex]]] = defaultdict(list)
    for position, index in enumerate(indices):
        if not index.anonymous:
            groups[(index.space, index.name)].append((position, index))

    removed: set[int] = set()
    issues: list[TensorIssue] = []
    for (space, name), occurrences in groups.items():
        if len(occurrences) == 1:
            continue
        if len(occurrences) > 2:
            issues.append(
                TensorIssue(
                    code="INDEX_MULTIPLICITY",
                    path=path,
                    message=(
                        f"index {name!r} in space {space!r} appears {len(occurrences)} times; "
                        "Einstein contraction permits at most two occurrences"
                    ),
                )
            )
            continue
        (left_position, left_index), (right_position, right_index) = occurrences
        if left_index.variance is right_index.variance:
            issues.append(
                TensorIssue(
                    code="SAME_VARIANCE_CONTRACTION",
                    path=path,
                    message=(
                        f"index {name!r} appears twice with variance "
                        f"{left_index.variance.value!r}"
                    ),
                )
            )
            continue
        removed.update({left_position, right_position})

    free = tuple(index for position, index in enumerate(indices) if position not in removed)
    return free, tuple(issues)


def _anonymous_index(
    name: str,
    space: str,
    variance: IndexVariance = IndexVariance.COVARIANT,
) -> TensorIndex:
    return TensorIndex(name=name, variance=variance, space=space, anonymous=True)


def _single_space(signature: TensorSignature) -> str | None:
    spaces = {index.space for index in signature.indices}
    if len(spaces) == 1:
        return next(iter(spaces))
    return None
