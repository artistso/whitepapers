"""Command-line interface for tensor and free-index inference."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .expressions import Equality, ExpressionParseError, load_expression
from .tensor_inference import (
    DEFAULT_TENSOR_CONTEXT,
    TensorContext,
    analyze_tensor,
    check_equality_tensors,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-tensor",
        description="Infer tensor rank and free-index structure from a controlled expression.",
    )
    parser.add_argument("expression", type=Path, help="Path to an expression JSON file")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--spatial-dimension",
        type=int,
        default=3,
        help="Dimension used for spatial, position, and momentum vector spaces",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.spatial_dimension < 1:
        print("error: --spatial-dimension must be positive", file=sys.stderr)
        return 2

    try:
        expression = load_expression(args.expression)
    except ExpressionParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    context = TensorContext(
        space_dimensions={
            **DEFAULT_TENSOR_CONTEXT.space_dimensions,
            "spatial": args.spatial_dimension,
            "position": args.spatial_dimension,
            "momentum": args.spatial_dimension,
        }
    )

    if isinstance(expression, Equality):
        report = check_equality_tensors(expression, context=context)
        payload = report.to_dict()
        valid = report.consistent
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            status = "PASS" if valid else "FAIL"
            print(f"[{status}] tensor consistency")
            print(f"- left:  {report.left.format()}")
            print(f"- right: {report.right.format()}")
            for issue in report.issues:
                print(
                    f"- {issue.severity.value.upper()} {issue.code} "
                    f"at {issue.path}: {issue.message}"
                )
        return 0 if valid else 1

    analysis = analyze_tensor(expression, context=context)
    valid = not analysis.issues
    payload = {
        "consistent": valid,
        "signature": analysis.signature.to_dict(),
        "issues": [issue.to_dict() for issue in analysis.issues],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASS" if valid else "FAIL"
        print(f"[{status}] {analysis.signature.format()}")
        for issue in analysis.issues:
            print(
                f"- {issue.severity.value.upper()} {issue.code} "
                f"at {issue.path}: {issue.message}"
            )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
