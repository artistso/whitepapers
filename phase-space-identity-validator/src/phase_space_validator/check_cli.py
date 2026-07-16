"""Combined structural checker for controlled equality expressions."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .dimension_inference import (
    DimensionInferenceError,
    check_equality_dimensions,
)
from .expressions import Equality, ExpressionParseError, load_expression
from .tensor_inference import check_equality_tensors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-check",
        description="Run dimension and tensor checks over a controlled equality expression.",
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
        print("error: psiv-check requires an equality expression", file=sys.stderr)
        return 2

    dimension_payload: dict[str, Any]
    dimension_consistent = False
    dimension_issues: list[dict[str, str]] = []
    try:
        dimension_report = check_equality_dimensions(expression)
        dimension_payload = dimension_report.to_dict()
        dimension_consistent = dimension_report.consistent
        if not dimension_report.consistent:
            dimension_issues.append(
                {
                    "code": dimension_report.code or "DIMENSION_MISMATCH",
                    "path": "$",
                    "message": (
                        f"left side is {dimension_report.left.format()}, "
                        f"right side is {dimension_report.right.format()}"
                    ),
                    "severity": "error",
                }
            )
    except DimensionInferenceError as exc:
        dimension_payload = {"consistent": False, "error": str(exc)}
        dimension_issues.append(
            {
                "code": exc.code,
                "path": exc.path,
                "message": exc.message,
                "severity": "error",
            }
        )

    tensor_report = check_equality_tensors(expression)
    tensor_payload = tensor_report.to_dict()
    issues = dimension_issues + [issue.to_dict() for issue in tensor_report.issues]
    valid = dimension_consistent and tensor_report.consistent

    payload = {
        "consistent": valid,
        "dimension": dimension_payload,
        "tensor": tensor_payload,
        "issues": issues,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASS" if valid else "FAIL"
        print(f"[{status}] combined structural check")
        if "left" in dimension_payload and "right" in dimension_payload:
            print(f"- dimensions left:  {dimension_payload['left']['formatted']}")
            print(f"- dimensions right: {dimension_payload['right']['formatted']}")
        print(f"- tensor left:      {tensor_report.left.format()}")
        print(f"- tensor right:     {tensor_report.right.format()}")
        for issue in issues:
            print(
                f"- {issue['severity'].upper()} {issue['code']} "
                f"at {issue['path']}: {issue['message']}"
            )

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
