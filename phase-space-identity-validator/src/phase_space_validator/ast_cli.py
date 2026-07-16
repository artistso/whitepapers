"""Command-line inspection for controlled expression trees."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .expressions import (
    ExpressionParseError,
    expression_depth,
    load_expression,
    walk_expression,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-ast",
        description="Parse and normalize a controlled phase-space expression AST.",
    )
    parser.add_argument("expression", type=Path, help="Path to expression JSON")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Include root type, node count, and tree depth",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        expression = load_expression(args.expression)
    except ExpressionParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload: dict[str, object]
    if args.summary:
        payload = {
            "expression": expression.to_dict(),
            "summary": {
                "root_type": expression.kind,
                "node_count": len(walk_expression(expression)),
                "depth": expression_depth(expression),
            },
        }
    else:
        payload = expression.to_dict()

    if args.compact:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
