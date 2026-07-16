"""Physical-dimension inference over the controlled expression AST."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
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

_BASE_ORDER = ("M", "L", "T", "Q", "Theta")


@dataclass(frozen=True)
class Dimension:
    """Immutable sparse vector of base-dimension exponents."""

    exponents: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(
            sorted(
                ((str(symbol), int(power)) for symbol, power in self.exponents if int(power) != 0),
                key=lambda item: _dimension_sort_key(item[0]),
            )
        )
        if len({symbol for symbol, _ in normalized}) != len(normalized):
            raise ValueError("dimension symbols must be unique")
        object.__setattr__(self, "exponents", normalized)

    @classmethod
    def from_mapping(cls, values: Mapping[str, int] | None = None) -> Dimension:
        return cls(tuple((symbol, exponent) for symbol, exponent in (values or {}).items()))

    @classmethod
    def dimensionless(cls) -> Dimension:
        return cls()

    def to_mapping(self) -> dict[str, int]:
        return dict(self.exponents)

    def multiply(self, other: Dimension) -> Dimension:
        values = self.to_mapping()
        for symbol, exponent in other.exponents:
            values[symbol] = values.get(symbol, 0) + exponent
        return Dimension.from_mapping(values)

    def divide(self, other: Dimension) -> Dimension:
        return self.multiply(other.power(-1))

    def power(self, exponent: int) -> Dimension:
        if isinstance(exponent, bool) or not isinstance(exponent, int):
            raise TypeError("dimension exponent must be an integer")
        return Dimension(tuple((symbol, power * exponent) for symbol, power in self.exponents))

    def format(self) -> str:
        if not self.exponents:
            return "1"
        return " ".join(
            symbol if exponent == 1 else f"{symbol}^{exponent}"
            for symbol, exponent in self.exponents
        )


@dataclass(frozen=True)
class DimensionRegistry:
    """Dimension assignments for symbols and coordinate spaces."""

    symbols: Mapping[str, Dimension] = field(default_factory=dict)
    coordinates: Mapping[str, Dimension] = field(default_factory=dict)
    poisson_scale: Dimension = field(default_factory=Dimension.dimensionless)

    def symbol_dimension(self, name: str, path: str) -> Dimension:
        try:
            return self.symbols[name]
        except KeyError as exc:
            raise DimensionInferenceError(
                code="UNKNOWN_SYMBOL",
                path=path,
                message=f"no dimension is registered for symbol {name!r}",
            ) from exc

    def coordinate_dimension(self, name: str, path: str) -> Dimension:
        try:
            return self.coordinates[name]
        except KeyError as exc:
            raise DimensionInferenceError(
                code="UNKNOWN_COORDINATE",
                path=path,
                message=f"no coordinate dimension is registered for {name!r}",
            ) from exc


@dataclass(frozen=True)
class DimensionInferenceError(ValueError):
    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} at {self.path}: {self.message}"


@dataclass(frozen=True)
class DimensionCheckReport:
    left: Dimension
    right: Dimension
    consistent: bool
    code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "consistent": self.consistent,
            "code": self.code,
            "left": {
                "dimensions": self.left.to_mapping(),
                "formatted": self.left.format(),
            },
            "right": {
                "dimensions": self.right.to_mapping(),
                "formatted": self.right.format(),
            },
        }


MASS = Dimension.from_mapping({"M": 1})
LENGTH = Dimension.from_mapping({"L": 1})
TIME = Dimension.from_mapping({"T": 1})
MOMENTUM = Dimension.from_mapping({"M": 1, "L": 1, "T": -1})
ACTION = Dimension.from_mapping({"M": 1, "L": 2, "T": -1})
INVERSE_ACTION = ACTION.power(-1)

DEFAULT_REGISTRY = DimensionRegistry(
    symbols={
        "x": LENGTH,
        "p": MOMENTUM,
        "hbar": ACTION,
        "delta": Dimension.dimensionless(),
        "I": Dimension.dimensionless(),
    },
    coordinates={
        "x": LENGTH,
        "p": MOMENTUM,
    },
    poisson_scale=INVERSE_ACTION,
)


def infer_dimension(
    expression: Expression,
    registry: DimensionRegistry = DEFAULT_REGISTRY,
    *,
    path: str = "$",
) -> Dimension:
    """Infer one expression's physical dimension recursively."""

    if isinstance(expression, Constant):
        return Dimension.dimensionless()

    if isinstance(expression, Symbol):
        return registry.symbol_dimension(expression.name, path)

    if isinstance(expression, Derivative):
        operand = infer_dimension(expression.operand, registry, path=f"{path}.operand")
        variable = registry.coordinate_dimension(expression.variable, f"{path}.variable")
        return operand.divide(variable.power(expression.order))

    if isinstance(expression, Gradient):
        coordinate = registry.coordinate_dimension(expression.space, f"{path}.space")
        operator_dimension = coordinate.power(-1)
        if expression.operand is None:
            return operator_dimension
        operand = infer_dimension(expression.operand, registry, path=f"{path}.operand")
        return operator_dimension.multiply(operand)

    if isinstance(expression, PoissonBracket):
        left = infer_dimension(expression.left, registry, path=f"{path}.left")
        right = infer_dimension(expression.right, registry, path=f"{path}.right")
        return left.multiply(right).multiply(registry.poisson_scale)

    if isinstance(
        expression,
        (CrossProduct, TensorProduct, WedgeProduct, Commutator),
    ):
        left = infer_dimension(expression.left, registry, path=f"{path}.left")
        right = infer_dimension(expression.right, registry, path=f"{path}.right")
        return left.multiply(right)

    if isinstance(expression, Power):
        base = infer_dimension(expression.base, registry, path=f"{path}.base")
        return base.power(expression.exponent)

    if isinstance(expression, Product):
        result = Dimension.dimensionless()
        for index, factor in enumerate(expression.factors):
            result = result.multiply(
                infer_dimension(factor, registry, path=f"{path}.factors[{index}]")
            )
        return result

    if isinstance(expression, Sum):
        dimensions = tuple(
            infer_dimension(term, registry, path=f"{path}.terms[{index}]")
            for index, term in enumerate(expression.terms)
        )
        reference = dimensions[0]
        for index, dimension in enumerate(dimensions[1:], start=1):
            if dimension != reference:
                raise DimensionInferenceError(
                    code="INCOMPATIBLE_SUM",
                    path=f"{path}.terms[{index}]",
                    message=(
                        f"term has dimension {dimension.format()}, expected {reference.format()}"
                    ),
                )
        return reference

    if isinstance(expression, Equality):
        report = check_equality_dimensions(expression, registry, path=path)
        if not report.consistent:
            raise DimensionInferenceError(
                code="DIMENSION_MISMATCH",
                path=path,
                message=(
                    f"left side is {report.left.format()}, right side is {report.right.format()}"
                ),
            )
        return report.left

    raise DimensionInferenceError(
        code="UNSUPPORTED_NODE",
        path=path,
        message=f"dimension inference is not implemented for {type(expression).__name__}",
    )


def check_equality_dimensions(
    equality: Equality,
    registry: DimensionRegistry = DEFAULT_REGISTRY,
    *,
    path: str = "$",
) -> DimensionCheckReport:
    """Infer and compare the two sides of an equality."""

    left = infer_dimension(equality.left, registry, path=f"{path}.left")
    right = infer_dimension(equality.right, registry, path=f"{path}.right")
    consistent = left == right
    return DimensionCheckReport(
        left=left,
        right=right,
        consistent=consistent,
        code=None if consistent else "DIMENSION_MISMATCH",
    )


def _dimension_sort_key(symbol: str) -> tuple[int, str]:
    try:
        return (_BASE_ORDER.index(symbol), symbol)
    except ValueError:
        return (len(_BASE_ORDER), symbol)
