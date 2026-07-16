"""Typed data model for proposed mathematical identities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class MathematicalObject:
    """Metadata describing one side of an identity.

    Dimensions are sparse exponent maps. For example, inverse action is
    ``{"A": -1}``, while action squared is ``{"A": 2}``.
    """

    label: str
    rank: int
    dimensions: dict[str, int] = field(default_factory=dict)
    is_operator: bool = False
    differential_order: int = 0
    intrinsic: bool = True
    distributional: bool = False
    domain: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MathematicalObject:
        required = {"label", "rank"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing object fields: {', '.join(sorted(missing))}")
        rank = int(data["rank"])
        if rank < 0:
            raise ValueError("rank must be non-negative")
        differential_order = int(data.get("differential_order", 0))
        if differential_order < 0:
            raise ValueError("differential_order must be non-negative")
        dimensions = {
            str(symbol): int(exponent)
            for symbol, exponent in dict(data.get("dimensions", {})).items()
            if int(exponent) != 0
        }
        return cls(
            label=str(data["label"]),
            rank=rank,
            dimensions=dimensions,
            is_operator=bool(data.get("is_operator", False)),
            differential_order=differential_order,
            intrinsic=bool(data.get("intrinsic", True)),
            distributional=bool(data.get("distributional", False)),
            domain=str(data["domain"]) if data.get("domain") is not None else None,
        )


@dataclass(frozen=True)
class ValidationContext:
    require_intrinsic: bool = True
    allow_operator_eigenvalue_equation: bool = False
    allow_rank_coercion: bool = False
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ValidationContext:
        data = data or {}
        return cls(
            require_intrinsic=bool(data.get("require_intrinsic", True)),
            allow_operator_eigenvalue_equation=bool(
                data.get("allow_operator_eigenvalue_equation", False)
            ),
            allow_rank_coercion=bool(data.get("allow_rank_coercion", False)),
            notes=tuple(str(note) for note in data.get("notes", [])),
        )


@dataclass(frozen=True)
class IdentitySpec:
    name: str
    lhs: MathematicalObject
    rhs: MathematicalObject
    relation: str = "="
    context: ValidationContext = field(default_factory=ValidationContext)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IdentitySpec:
        missing = {"name", "lhs", "rhs"} - data.keys()
        if missing:
            raise ValueError(f"Missing identity fields: {', '.join(sorted(missing))}")
        return cls(
            name=str(data["name"]),
            lhs=MathematicalObject.from_dict(dict(data["lhs"])),
            rhs=MathematicalObject.from_dict(dict(data["rhs"])),
            relation=str(data.get("relation", "=")),
            context=ValidationContext.from_dict(data.get("context")),
        )


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: Severity
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass(frozen=True)
class ValidationReport:
    identity: str
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(issue.severity is Severity.ERROR for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }
