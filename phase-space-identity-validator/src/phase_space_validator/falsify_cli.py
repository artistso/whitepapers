"""Command-line interface for symbolic counterexample search."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .expressions import Equality, ExpressionParseError, load_expression
from .symbolic_counterexample import SymbolicCounterexampleError, falsify_equality


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-falsify",
        description="Search for a symbolic counterexample to a supported universal claim.",
    )
    parser.add_argument("expression", type=Path, help="Path to an equality-expression JSON file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        expression = load_expression(args.expression)
    except ExpressionParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not isinstance(expression, Equality):
        print("error: psiv-falsify requires an equality expression", file=sys.stderr)
        return 2

    try:
        result = falsify_equality(expression)
    except SymbolicCounterexampleError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "evidence_level": "UNSUPPORTED_CLAIM",
                        "counterexample_found": False,
                        "error": {
                            "code": exc.code,
                            "path": exc.path,
                            "message": exc.message,
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    elif result.counterexample_found:
        print("[COUNTEREXAMPLE] universal claim falsified")
        print(f"- witness:      {result.witness}")
        print(f"- left action:  {result.left_action}")
        print(f"- right action: {result.right_action}")
        print(f"- residual:     {result.residual}")
        print(f"- tested:       {result.candidates_tested} candidate(s)")
    else:
        print("[NO COUNTEREXAMPLE FOUND] within the configured search space")
        print(f"- tested: {result.candidates_tested} candidate(s)")
        print("- status: not a proof")

    return 1 if result.counterexample_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
