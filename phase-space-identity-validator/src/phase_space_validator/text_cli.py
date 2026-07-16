"""Command-line parser for controlled mathematical text."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .expressions import expression_depth, walk_expression
from .text_parser import TextParseError, load_text_expression, parse_text_expression


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-parse",
        description="Parse controlled mathematical text into the canonical expression AST.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Expression text to parse")
    source.add_argument("--file", type=Path, help="Path to a UTF-8 expression text file")
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
        expression = (
            parse_text_expression(args.text)
            if args.text is not None
            else load_text_expression(args.file)
        )
    except TextParseError as exc:
        print(json.dumps({"error": exc.to_dict()}, indent=2, sort_keys=True), file=sys.stderr)
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
