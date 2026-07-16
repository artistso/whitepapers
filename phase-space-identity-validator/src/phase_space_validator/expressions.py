"""Controlled expression abstract syntax tree.

The AST intentionally covers a small, explicit grammar. It is designed as the
stable input layer for later dimension, tensor, and symbolic inference passes.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar


class ExpressionParseError(ValueError):
    """Raised when serialized expression data does not match the grammar."""


class Expression(ABC):
    """Base class for every controlled expression node."""

    kind: ClassVar[str]

    @property
    def children(self) -> tuple[Expression, ...]:
        return ()

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize this node to the canonical JSON-compatible form."""


@dataclass(frozen=True)
class Symbol(Expression):
    kind: ClassVar[str] = "symbol"

    name: str
    indices: tuple[str, ...] = ()
    space: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("symbol name must not be empty")
        if any(not index.strip() for index in self.indices):
            raise ValueError("symbol indices must not be empty")
        if self.space is not None and not self.space.strip():
            raise ValueError("symbol space must not be empty")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.kind, "name": self.name}
        if self.indices:
            data["indices"] = list(self.indices)
        if self.space is not None:
            data["space"] = self.space
        return data


@dataclass(frozen=True)
class Constant(Expression):
    kind: ClassVar[str] = "constant"

    value: int | float | str

    def __post_init__(self) -> None:
        if isinstance(self.value, bool):
            raise ValueError("boolean values are not mathematical constants")
        if isinstance(self.value, str) and not self.value.strip():
            raise ValueError("constant value must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.kind, "value": self.value}


@dataclass(frozen=True)
class Derivative(Expression):
    kind: ClassVar[str] = "derivative"

    variable: str
    operand: Expression
    order: int = 1
    partial: bool = True

    def __post_init__(self) -> None:
        if not self.variable.strip():
            raise ValueError("derivative variable must not be empty")
        if self.order < 1:
            raise ValueError("derivative order must be positive")
        _require_expression(self.operand, "derivative operand")

    @property
    def children(self) -> tuple[Expression, ...]:
        return (self.operand,)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.kind,
            "variable": self.variable,
            "operand": self.operand.to_dict(),
        }
        if self.order != 1:
            data["order"] = self.order
        if not self.partial:
            data["partial"] = False
        return data


@dataclass(frozen=True)
class Gradient(Expression):
    kind: ClassVar[str] = "gradient"

    space: str
    operand: Expression | None = None

    def __post_init__(self) -> None:
        if not self.space.strip():
            raise ValueError("gradient space must not be empty")
        if self.operand is not None:
            _require_expression(self.operand, "gradient operand")

    @property
    def children(self) -> tuple[Expression, ...]:
        return () if self.operand is None else (self.operand,)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.kind, "space": self.space}
        if self.operand is not None:
            data["operand"] = self.operand.to_dict()
        return data


@dataclass(frozen=True)
class BinaryExpression(Expression):
    left: Expression
    right: Expression

    def __post_init__(self) -> None:
        _require_expression(self.left, f"{self.kind} left operand")
        _require_expression(self.right, f"{self.kind} right operand")

    @property
    def children(self) -> tuple[Expression, ...]:
        return (self.left, self.right)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.kind,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(frozen=True)
class CrossProduct(BinaryExpression):
    kind: ClassVar[str] = "cross_product"


@dataclass(frozen=True)
class TensorProduct(BinaryExpression):
    kind: ClassVar[str] = "tensor_product"


@dataclass(frozen=True)
class WedgeProduct(BinaryExpression):
    kind: ClassVar[str] = "wedge_product"


@dataclass(frozen=True)
class Commutator(BinaryExpression):
    kind: ClassVar[str] = "commutator"


@dataclass(frozen=True)
class PoissonBracket(BinaryExpression):
    kind: ClassVar[str] = "poisson_bracket"


@dataclass(frozen=True)
class Power(Expression):
    kind: ClassVar[str] = "power"

    base: Expression
    exponent: int

    def __post_init__(self) -> None:
        _require_expression(self.base, "power base")
        if isinstance(self.exponent, bool) or not isinstance(self.exponent, int):
            raise ValueError("power exponent must be an integer")

    @property
    def children(self) -> tuple[Expression, ...]:
        return (self.base,)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.kind,
            "base": self.base.to_dict(),
            "exponent": self.exponent,
        }


@dataclass(frozen=True)
class Product(Expression):
    kind: ClassVar[str] = "product"

    factors: tuple[Expression, ...]

    def __post_init__(self) -> None:
        if len(self.factors) < 2:
            raise ValueError("product requires at least two factors")
        for factor in self.factors:
            _require_expression(factor, "product factor")

    @property
    def children(self) -> tuple[Expression, ...]:
        return self.factors

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.kind, "factors": [factor.to_dict() for factor in self.factors]}


@dataclass(frozen=True)
class Sum(Expression):
    kind: ClassVar[str] = "sum"

    terms: tuple[Expression, ...]

    def __post_init__(self) -> None:
        if len(self.terms) < 2:
            raise ValueError("sum requires at least two terms")
        for term in self.terms:
            _require_expression(term, "sum term")

    @property
    def children(self) -> tuple[Expression, ...]:
        return self.terms

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.kind, "terms": [term.to_dict() for term in self.terms]}


@dataclass(frozen=True)
class Equality(BinaryExpression):
    kind: ClassVar[str] = "equality"

    relation: str = "="

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.relation not in {"=", "≈", "≡"}:
            raise ValueError("unsupported equality relation")

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        if self.relation != "=":
            data["relation"] = self.relation
        return data


def expression_from_dict(data: dict[str, Any], *, path: str = "$") -> Expression:
    """Parse one canonical JSON object into an expression node."""

    if not isinstance(data, dict):
        raise ExpressionParseError(f"{path}: expression must be an object")
    kind = data.get("type")
    if not isinstance(kind, str) or not kind:
        raise ExpressionParseError(f"{path}: missing nonempty string field 'type'")

    try:
        if kind == Symbol.kind:
            _check_keys(data, {"type", "name"}, {"indices", "space"}, path)
            indices = data.get("indices", [])
            if not isinstance(indices, list) or not all(isinstance(item, str) for item in indices):
                raise ExpressionParseError(f"{path}.indices: expected an array of strings")
            return Symbol(
                name=_string_field(data, "name", path),
                indices=tuple(indices),
                space=_optional_string_field(data, "space", path),
            )

        if kind == Constant.kind:
            _check_keys(data, {"type", "value"}, set(), path)
            value = data["value"]
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise ExpressionParseError(f"{path}.value: expected a number or string")
            return Constant(value=value)

        if kind == Derivative.kind:
            _check_keys(data, {"type", "variable", "operand"}, {"order", "partial"}, path)
            order = data.get("order", 1)
            partial = data.get("partial", True)
            if isinstance(order, bool) or not isinstance(order, int):
                raise ExpressionParseError(f"{path}.order: expected an integer")
            if not isinstance(partial, bool):
                raise ExpressionParseError(f"{path}.partial: expected a boolean")
            return Derivative(
                variable=_string_field(data, "variable", path),
                operand=expression_from_dict(data["operand"], path=f"{path}.operand"),
                order=order,
                partial=partial,
            )

        if kind == Gradient.kind:
            _check_keys(data, {"type", "space"}, {"operand"}, path)
            operand_data = data.get("operand")
            operand = (
                None
                if operand_data is None
                else expression_from_dict(operand_data, path=f"{path}.operand")
            )
            return Gradient(space=_string_field(data, "space", path), operand=operand)

        binary_types: dict[str, type[BinaryExpression]] = {
            CrossProduct.kind: CrossProduct,
            TensorProduct.kind: TensorProduct,
            WedgeProduct.kind: WedgeProduct,
            Commutator.kind: Commutator,
            PoissonBracket.kind: PoissonBracket,
        }
        if kind in binary_types:
            _check_keys(data, {"type", "left", "right"}, set(), path)
            return binary_types[kind](
                left=expression_from_dict(data["left"], path=f"{path}.left"),
                right=expression_from_dict(data["right"], path=f"{path}.right"),
            )

        if kind == Power.kind:
            _check_keys(data, {"type", "base", "exponent"}, set(), path)
            exponent = data["exponent"]
            if isinstance(exponent, bool) or not isinstance(exponent, int):
                raise ExpressionParseError(f"{path}.exponent: expected an integer")
            return Power(
                base=expression_from_dict(data["base"], path=f"{path}.base"),
                exponent=exponent,
            )

        if kind == Product.kind:
            _check_keys(data, {"type", "factors"}, set(), path)
            return Product(
                factors=_parse_expression_array(data["factors"], f"{path}.factors")
            )

        if kind == Sum.kind:
            _check_keys(data, {"type", "terms"}, set(), path)
            return Sum(terms=_parse_expression_array(data["terms"], f"{path}.terms"))

        if kind == Equality.kind:
            _check_keys(data, {"type", "left", "right"}, {"relation"}, path)
            relation = data.get("relation", "=")
            if not isinstance(relation, str):
                raise ExpressionParseError(f"{path}.relation: expected a string")
            return Equality(
                left=expression_from_dict(data["left"], path=f"{path}.left"),
                right=expression_from_dict(data["right"], path=f"{path}.right"),
                relation=relation,
            )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ExpressionParseError):
            raise
        raise ExpressionParseError(f"{path}: {exc}") from exc

    raise ExpressionParseError(f"{path}: unsupported expression type {kind!r}")


def expression_from_json(text: str) -> Expression:
    """Parse a JSON string into an expression node."""

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExpressionParseError(f"invalid JSON: {exc}") from exc
    return expression_from_dict(data)


def load_expression(path: Path) -> Expression:
    """Load an expression JSON file."""

    try:
        return expression_from_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ExpressionParseError(str(exc)) from exc


def walk_expression(root: Expression) -> tuple[Expression, ...]:
    """Return a deterministic pre-order traversal."""

    nodes: list[Expression] = []

    def visit(node: Expression) -> None:
        nodes.append(node)
        for child in node.children:
            visit(child)

    visit(root)
    return tuple(nodes)


def expression_depth(root: Expression) -> int:
    """Return one for a leaf and otherwise one plus maximum child depth."""

    if not root.children:
        return 1
    return 1 + max(expression_depth(child) for child in root.children)


def _require_expression(value: object, description: str) -> None:
    if not isinstance(value, Expression):
        raise TypeError(f"{description} must be an Expression")


def _check_keys(
    data: dict[str, Any], required: set[str], optional: set[str], path: str
) -> None:
    missing = required - data.keys()
    if missing:
        raise ExpressionParseError(f"{path}: missing fields {', '.join(sorted(missing))}")
    unknown = data.keys() - required - optional
    if unknown:
        raise ExpressionParseError(f"{path}: unknown fields {', '.join(sorted(unknown))}")


def _string_field(data: dict[str, Any], name: str, path: str) -> str:
    value = data[name]
    if not isinstance(value, str):
        raise ExpressionParseError(f"{path}.{name}: expected a string")
    return value


def _optional_string_field(data: dict[str, Any], name: str, path: str) -> str | None:
    value = data.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ExpressionParseError(f"{path}.{name}: expected a string or null")
    return value


def _parse_expression_array(value: Any, path: str) -> tuple[Expression, ...]:
    if not isinstance(value, list):
        raise ExpressionParseError(f"{path}: expected an array")
    return tuple(
        expression_from_dict(item, path=f"{path}[{index}]") for index, item in enumerate(value)
    )
