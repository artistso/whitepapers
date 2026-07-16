"""Command-line interface for the validator."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .models import IdentitySpec
from .validator import validate_identity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv",
        description="Validate declared metadata for a proposed phase-space identity.",
    )
    parser.add_argument("spec", type=Path, help="Path to an identity JSON specification")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = json.loads(args.spec.read_text(encoding="utf-8"))
        spec = IdentitySpec.from_dict(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = validate_identity(spec)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if report.valid else "FAIL"
        print(f"[{status}] {report.identity}")
        for issue in report.issues:
            print(f"- {issue.severity.value.upper()} {issue.code}: {issue.message}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
