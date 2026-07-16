"""Versioned, end-to-end analysis reports for controlled mathematical identities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any

from .dimension_inference import DimensionInferenceError, check_equality_dimensions
from .expressions import Equality
from .models import Severity
from .symbolic_counterexample import EvidenceLevel as SymbolicEvidenceLevel
from .symbolic_counterexample import SymbolicCounterexampleError, falsify_equality
from .tensor_inference import check_equality_tensors
from .text_parser import TextParseError, parse_text_expression

REPORT_SCHEMA_VERSION = "1.0"
REPORT_TOOL_VERSION = "0.7.0"

REPORT_DIAGNOSTIC_CODES_V1 = (
    "ANALYSIS_REQUIRES_EQUALITY",
    "DIMENSION_MISMATCH",
    "SYMBOLIC_COUNTEREXAMPLE",
    "SYMBOLIC_NO_COUNTEREXAMPLE_FOUND",
)


class DiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class ReportEvidenceLevel(StrEnum):
    DECLARED = "declared"
    INFERRED = "inferred"
    COMPUTED = "computed"
    COUNTEREXAMPLE = "counterexample"
    INCONCLUSIVE = "inconclusive"


class OverallStatus(StrEnum):
    INPUT_ERROR = "input_error"
    INVALID = "invalid"
    NO_INCONSISTENCY_FOUND = "no_inconsistency_found"
    INCONCLUSIVE = "inconclusive"


class AnalysisExitCode(IntEnum):
    NO_INCONSISTENCY_FOUND = 0
    INVALID_IDENTITY = 1
    INPUT_ERROR = 2
    ANALYSIS_INCONCLUSIVE = 3
    INTERNAL_ERROR = 4


@dataclass(frozen=True)
class SourcePosition:
    offset: int
    line: int
    column: int

    def to_dict(self) -> dict[str, int]:
        return {"offset": self.offset, "line": self.line, "column": self.column}


@dataclass(frozen=True)
class SourceSpan:
    start: SourcePosition
    end: SourcePosition

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}


@dataclass(frozen=True)
class AnalysisDiagnostic:
    code: str
    severity: DiagnosticSeverity
    message: str
    stage: str
    evidence: ReportEvidenceLevel
    path: str
    span: SourceSpan

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "stage": self.stage,
            "evidence": self.evidence.value,
            "path": self.path,
            "span": self.span.to_dict(),
        }


@dataclass(frozen=True)
class AnalysisReport:
    schema_version: str
    tool_version: str
    input: dict[str, Any]
    parse: dict[str, Any]
    ast: dict[str, Any] | None
    dimensions: dict[str, Any]
    tensor_analysis: dict[str, Any]
    symbolic_evidence: dict[str, Any]
    metadata: dict[str, Any]
    diagnostics: tuple[AnalysisDiagnostic, ...]
    assumptions: tuple[str, ...]
    overall_status: OverallStatus
    exit_code: AnalysisExitCode

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool_version": self.tool_version,
            "input": self.input,
            "parse": self.parse,
            "ast": self.ast,
            "dimensions": self.dimensions,
            "tensor_analysis": self.tensor_analysis,
            "symbolic_evidence": self.symbolic_evidence,
            "metadata": self.metadata,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "assumptions": list(self.assumptions),
            "overall_status": self.overall_status.value,
            "exit_code": int(self.exit_code),
        }


_DEFAULT_ASSUMPTIONS = (
    "Input uses the controlled PSIV text grammar; implicit multiplication is not inferred.",
    "Dimension analysis uses the default symbol and coordinate registry.",
    "Tensor analysis uses the default three-dimensional position and momentum contexts.",
    "Symbolic falsification uses a deterministic, bounded bilinear witness search.",
    "No inconsistency found is not a proof that an identity is universally true.",
)


def analyze_text_identity(text: str, *, source_name: str = "<text>") -> AnalysisReport:
    """Parse and analyze one controlled mathematical identity."""

    full_span = _full_span(text)
    diagnostics: list[AnalysisDiagnostic] = []
    input_payload = {
        "kind": "text",
        "source_name": source_name,
        "text": text,
        "character_count": len(text),
    }
    metadata_payload: dict[str, Any] = {"status": "not_provided"}

    try:
        expression = parse_text_expression(text)
    except TextParseError as exc:
        diagnostics.append(
            AnalysisDiagnostic(
                code=exc.code,
                severity=DiagnosticSeverity.ERROR,
                message=exc.message,
                stage="parse",
                evidence=ReportEvidenceLevel.DECLARED,
                path="$",
                span=_parse_error_span(text, exc),
            )
        )
        return AnalysisReport(
            schema_version=REPORT_SCHEMA_VERSION,
            tool_version=REPORT_TOOL_VERSION,
            input=input_payload,
            parse={"status": "failed", "error": exc.to_dict()},
            ast=None,
            dimensions={"status": "not_run", "report": None},
            tensor_analysis={"status": "not_run", "report": None},
            symbolic_evidence={"status": "not_run", "report": None},
            metadata=metadata_payload,
            diagnostics=tuple(diagnostics),
            assumptions=_DEFAULT_ASSUMPTIONS,
            overall_status=OverallStatus.INPUT_ERROR,
            exit_code=AnalysisExitCode.INPUT_ERROR,
        )

    parse_payload = {
        "status": "passed",
        "root_type": expression.kind,
        "relation": expression.relation if isinstance(expression, Equality) else None,
    }
    ast_payload = expression.to_dict()

    if not isinstance(expression, Equality):
        diagnostics.append(
            AnalysisDiagnostic(
                code="ANALYSIS_REQUIRES_EQUALITY",
                severity=DiagnosticSeverity.ERROR,
                message="End-to-end identity analysis requires one equality relation.",
                stage="contract",
                evidence=ReportEvidenceLevel.DECLARED,
                path="$",
                span=full_span,
            )
        )
        return AnalysisReport(
            schema_version=REPORT_SCHEMA_VERSION,
            tool_version=REPORT_TOOL_VERSION,
            input=input_payload,
            parse=parse_payload,
            ast=ast_payload,
            dimensions={"status": "not_run", "report": None},
            tensor_analysis={"status": "not_run", "report": None},
            symbolic_evidence={"status": "not_run", "report": None},
            metadata=metadata_payload,
            diagnostics=tuple(diagnostics),
            assumptions=_DEFAULT_ASSUMPTIONS,
            overall_status=OverallStatus.INPUT_ERROR,
            exit_code=AnalysisExitCode.INPUT_ERROR,
        )

    dimensions_payload = _analyze_dimensions(expression, diagnostics, full_span)
    tensor_payload = _analyze_tensors(expression, diagnostics, full_span)
    symbolic_payload = _analyze_symbolically(expression, diagnostics, full_span)
    overall_status, exit_code = _classify_result(diagnostics)

    return AnalysisReport(
        schema_version=REPORT_SCHEMA_VERSION,
        tool_version=REPORT_TOOL_VERSION,
        input=input_payload,
        parse=parse_payload,
        ast=ast_payload,
        dimensions=dimensions_payload,
        tensor_analysis=tensor_payload,
        symbolic_evidence=symbolic_payload,
        metadata=metadata_payload,
        diagnostics=tuple(diagnostics),
        assumptions=_DEFAULT_ASSUMPTIONS,
        overall_status=overall_status,
        exit_code=exit_code,
    )


def format_analysis_report(report: AnalysisReport) -> str:
    """Render a compact human-readable representation of a report."""

    lines = [
        f"PSIV analysis report {report.schema_version}",
        f"overall status: {report.overall_status.value}",
        f"exit code: {int(report.exit_code)}",
        f"parse: {report.parse['status']}",
        f"dimensions: {report.dimensions['status']}",
        f"tensor analysis: {report.tensor_analysis['status']}",
        f"symbolic evidence: {report.symbolic_evidence['status']}",
    ]
    if report.diagnostics:
        lines.append("diagnostics:")
        for diagnostic in report.diagnostics:
            lines.append(
                f"  {diagnostic.severity.value.upper()} {diagnostic.code} "
                f"[{diagnostic.stage}] {diagnostic.message}"
            )
    else:
        lines.append("diagnostics: none")
    lines.append("disclaimer: no inconsistency found is not a proof.")
    return "\n".join(lines)


def _analyze_dimensions(
    equality: Equality,
    diagnostics: list[AnalysisDiagnostic],
    span: SourceSpan,
) -> dict[str, Any]:
    try:
        report = check_equality_dimensions(equality)
    except DimensionInferenceError as exc:
        diagnostics.append(
            AnalysisDiagnostic(
                code=exc.code,
                severity=DiagnosticSeverity.WARNING,
                message=exc.message,
                stage="dimensions",
                evidence=ReportEvidenceLevel.INCONCLUSIVE,
                path=exc.path,
                span=span,
            )
        )
        return {
            "status": "inconclusive",
            "report": None,
            "error": {"code": exc.code, "path": exc.path, "message": exc.message},
        }

    if not report.consistent:
        diagnostics.append(
            AnalysisDiagnostic(
                code=report.code or "DIMENSION_MISMATCH",
                severity=DiagnosticSeverity.ERROR,
                message=(
                    f"Left side has dimension {report.left.format()}, "
                    f"right side has {report.right.format()}."
                ),
                stage="dimensions",
                evidence=ReportEvidenceLevel.COMPUTED,
                path="$",
                span=span,
            )
        )
    return {
        "status": "passed" if report.consistent else "failed",
        "report": report.to_dict(),
        "error": None,
    }


def _analyze_tensors(
    equality: Equality,
    diagnostics: list[AnalysisDiagnostic],
    span: SourceSpan,
) -> dict[str, Any]:
    report = check_equality_tensors(equality)
    for issue in report.issues:
        severity = _map_tensor_severity(issue.code, issue.severity)
        evidence = (
            ReportEvidenceLevel.INCONCLUSIVE
            if severity is DiagnosticSeverity.WARNING
            else ReportEvidenceLevel.INFERRED
        )
        diagnostics.append(
            AnalysisDiagnostic(
                code=issue.code,
                severity=severity,
                message=issue.message,
                stage="tensor",
                evidence=evidence,
                path=issue.path,
                span=span,
            )
        )
    tensor_diagnostics = [diagnostic for diagnostic in diagnostics if diagnostic.stage == "tensor"]
    status = "passed"
    if any(diagnostic.severity is DiagnosticSeverity.ERROR for diagnostic in tensor_diagnostics):
        status = "failed"
    elif any(
        diagnostic.evidence is ReportEvidenceLevel.INCONCLUSIVE
        for diagnostic in tensor_diagnostics
    ):
        status = "inconclusive"
    return {"status": status, "report": report.to_dict(), "error": None}


def _analyze_symbolically(
    equality: Equality,
    diagnostics: list[AnalysisDiagnostic],
    span: SourceSpan,
) -> dict[str, Any]:
    try:
        result = falsify_equality(equality)
    except SymbolicCounterexampleError as exc:
        diagnostics.append(
            AnalysisDiagnostic(
                code=exc.code,
                severity=DiagnosticSeverity.WARNING,
                message=exc.message,
                stage="symbolic",
                evidence=ReportEvidenceLevel.INCONCLUSIVE,
                path=exc.path,
                span=span,
            )
        )
        return {
            "status": "inconclusive",
            "report": None,
            "error": {"code": exc.code, "path": exc.path, "message": exc.message},
        }

    if result.evidence_level is SymbolicEvidenceLevel.COUNTEREXAMPLE:
        diagnostics.append(
            AnalysisDiagnostic(
                code="SYMBOLIC_COUNTEREXAMPLE",
                severity=DiagnosticSeverity.ERROR,
                message=f"Bounded symbolic search found witness {result.witness!r}.",
                stage="symbolic",
                evidence=ReportEvidenceLevel.COUNTEREXAMPLE,
                path="$",
                span=span,
            )
        )
        status = "counterexample"
    else:
        diagnostics.append(
            AnalysisDiagnostic(
                code="SYMBOLIC_NO_COUNTEREXAMPLE_FOUND",
                severity=DiagnosticSeverity.INFORMATION,
                message=(
                    "No counterexample was found in the configured bounded search space; "
                    "this is not a proof."
                ),
                stage="symbolic",
                evidence=ReportEvidenceLevel.COMPUTED,
                path="$",
                span=span,
            )
        )
        status = "no_counterexample_found"

    return {"status": status, "report": result.to_dict(), "error": None}


def _classify_result(
    diagnostics: list[AnalysisDiagnostic],
) -> tuple[OverallStatus, AnalysisExitCode]:
    if any(diagnostic.severity is DiagnosticSeverity.ERROR for diagnostic in diagnostics):
        return OverallStatus.INVALID, AnalysisExitCode.INVALID_IDENTITY
    if any(diagnostic.evidence is ReportEvidenceLevel.INCONCLUSIVE for diagnostic in diagnostics):
        return OverallStatus.INCONCLUSIVE, AnalysisExitCode.ANALYSIS_INCONCLUSIVE
    return OverallStatus.NO_INCONSISTENCY_FOUND, AnalysisExitCode.NO_INCONSISTENCY_FOUND


def _map_tensor_severity(code: str, severity: Severity) -> DiagnosticSeverity:
    if code in {"UNKNOWN_TENSOR_SYMBOL", "UNSUPPORTED_TENSOR_NODE"}:
        return DiagnosticSeverity.WARNING
    if severity is Severity.ERROR:
        return DiagnosticSeverity.ERROR
    if severity is Severity.WARNING:
        return DiagnosticSeverity.WARNING
    return DiagnosticSeverity.INFORMATION


def _full_span(text: str) -> SourceSpan:
    return SourceSpan(
        start=SourcePosition(offset=0, line=1, column=1),
        end=_position_at(text, len(text)),
    )


def _parse_error_span(text: str, error: TextParseError) -> SourceSpan:
    end_offset = min(error.offset + 1, len(text))
    return SourceSpan(
        start=SourcePosition(offset=error.offset, line=error.line, column=error.column),
        end=_position_at(text, end_offset),
    )


def _position_at(text: str, offset: int) -> SourcePosition:
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    last_break = prefix.rfind("\n")
    column = offset + 1 if last_break < 0 else offset - last_break
    return SourcePosition(offset=offset, line=line, column=column)
