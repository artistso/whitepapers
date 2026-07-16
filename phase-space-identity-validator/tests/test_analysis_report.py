from __future__ import annotations

from jsonschema import Draft202012Validator

from phase_space_validator.analysis_report import (
    REPORT_DIAGNOSTIC_CODES_V1,
    AnalysisExitCode,
    OverallStatus,
    analyze_text_identity,
)
from phase_space_validator.report_schema import load_analysis_report_schema


def test_invalid_cross_gradient_report_combines_all_engines() -> None:
    text = "nabla_x cross nabla_p = hbar^2/(2*pi)"
    report = analyze_text_identity(text)
    codes = {diagnostic.code for diagnostic in report.diagnostics}

    assert report.overall_status is OverallStatus.INVALID
    assert report.exit_code is AnalysisExitCode.INVALID_IDENTITY
    assert report.parse["status"] == "passed"
    assert report.dimensions["status"] == "failed"
    assert report.tensor_analysis["status"] == "failed"
    assert "DIMENSION_MISMATCH" in codes
    assert "TYPE_RANK_MISMATCH" in codes
    assert all(diagnostic.span.end.offset == len(text) for diagnostic in report.diagnostics)


def test_zero_claim_contains_symbolic_counterexample() -> None:
    report = analyze_text_identity("nabla_x cross nabla_p = 0")

    assert report.symbolic_evidence["status"] == "counterexample"
    assert report.symbolic_evidence["report"]["witness"] == "p2*x1"
    assert "SYMBOLIC_COUNTEREXAMPLE" in {
        diagnostic.code for diagnostic in report.diagnostics
    }


def test_parse_error_is_a_versioned_input_error_report() -> None:
    report = analyze_text_identity("2 pi")
    diagnostic = report.diagnostics[0]

    assert report.overall_status is OverallStatus.INPUT_ERROR
    assert report.exit_code is AnalysisExitCode.INPUT_ERROR
    assert report.ast is None
    assert report.parse["status"] == "failed"
    assert diagnostic.code == "EXPLICIT_MULTIPLICATION_REQUIRED"
    assert diagnostic.span.start.offset == 2
    assert diagnostic.span.start.column == 3


def test_non_equality_is_rejected_by_analysis_contract() -> None:
    report = analyze_text_identity("x+p")

    assert report.overall_status is OverallStatus.INPUT_ERROR
    assert report.diagnostics[0].code == "ANALYSIS_REQUIRES_EQUALITY"
    assert report.dimensions["status"] == "not_run"


def test_unsupported_symbolic_analysis_is_inconclusive_not_valid() -> None:
    report = analyze_text_identity("[x_i,p_j]=i*hbar*delta_ij*I")

    assert report.overall_status is OverallStatus.INCONCLUSIVE
    assert report.exit_code is AnalysisExitCode.ANALYSIS_INCONCLUSIVE
    assert report.dimensions["status"] == "passed"
    assert report.symbolic_evidence["status"] == "inconclusive"


def test_report_matches_committed_json_schema() -> None:
    schema = load_analysis_report_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(
        analyze_text_identity("nabla_x cross nabla_p = 0").to_dict()
    )
    Draft202012Validator(schema).validate(analyze_text_identity("2 pi").to_dict())


def test_report_owned_diagnostic_codes_are_frozen_for_v1() -> None:
    assert REPORT_DIAGNOSTIC_CODES_V1 == (
        "ANALYSIS_REQUIRES_EQUALITY",
        "DIMENSION_MISMATCH",
        "SYMBOLIC_COUNTEREXAMPLE",
        "SYMBOLIC_NO_COUNTEREXAMPLE_FOUND",
    )
