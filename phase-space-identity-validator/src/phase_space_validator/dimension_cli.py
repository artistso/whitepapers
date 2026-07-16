"""Command-line dimension inference for controlled expression trees."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .dimension_inference import DimensionInferenceError, check_equality_dimensions
from .expressions import Equality, ExpressionParseError, load_expression


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-dim",
        description="Infer and compare physical dimensions in an equality AST.",
    )
    parser.add_argument("expression", type=Path, help="Path to equality expression JSON")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        expression = load_expression(args.expression)
        if not isinstance(expression, Equality):
            print("error: root expression must be an equality", file=sys.stderr)
            return 2
        report = check_equality_dimensions(expression)
    except (ExpressionParseError, DimensionInferenceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = report.to_dict()
    if args.compact:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.consistent else 1


if __name__ == "__main__":
    raise SystemExit(main())
