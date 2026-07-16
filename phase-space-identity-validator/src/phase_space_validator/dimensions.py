"""Dimension normalization and formatting helpers."""

from __future__ import annotations

from collections.abc import Mapping


def normalize_dimensions(dimensions: Mapping[str, int]) -> dict[str, int]:
    """Return a canonical sparse exponent map."""
    return {
        str(symbol): int(exponent)
        for symbol, exponent in sorted(dimensions.items())
        if int(exponent) != 0
    }


def dimensions_equal(left: Mapping[str, int], right: Mapping[str, int]) -> bool:
    return normalize_dimensions(left) == normalize_dimensions(right)


def format_dimensions(dimensions: Mapping[str, int]) -> str:
    normalized = normalize_dimensions(dimensions)
    if not normalized:
        return "1 (dimensionless)"
    return " ".join(
        symbol if exponent == 1 else f"{symbol}^{exponent}"
        for symbol, exponent in normalized.items()
    )
