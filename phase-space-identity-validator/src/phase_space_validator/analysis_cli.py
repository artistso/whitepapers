"""Unified command-line analysis for controlled mathematical identities."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .analysis_report import (
    AnalysisExitCode,
    analyze_text_identity,
    format_analysis_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psiv-analyze",
        description=(
            "Parse a controlled mathematical identity and emit one versioned report "
            "covering dimensions, tensors, and symbolic evidence."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Identity text to analyze")
    source.add_argument("--file", type=Path, help="Path to a UTF-8 identity text file")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.text is not None:
            text = args.text
            source_name = "<text>"
        else:
            text = args.file.read_text(encoding="utf-8")
            source_name = str(args.file)
    except (OSError, UnicodeError) as exc:
        payload = {
            "error": {
                "code": "INPUT_READ_ERROR",
                "message": str(exc),
                "source_name": str(args.file),
            }
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return int(AnalysisExitCode.INPUT_ERROR)

    try:
        report = analyze_text_identity(text, source_name=source_name)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        payload = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "source_name": source_name,
            }
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return int(AnalysisExitCode.INTERNAL_ERROR)

    if args.format == "text":
        print(format_analysis_report(report))
    elif args.compact:
        print(json.dumps(report.to_dict(), separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return int(report.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
