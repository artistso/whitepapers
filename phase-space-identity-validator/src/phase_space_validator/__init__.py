"""Phase-Space Identity Validator public API."""

from .models import IdentitySpec, MathematicalObject, ValidationIssue, ValidationReport
from .validator import validate_identity

__all__ = [
    "IdentitySpec",
    "MathematicalObject",
    "ValidationIssue",
    "ValidationReport",
    "validate_identity",
]

__version__ = "0.1.0"
