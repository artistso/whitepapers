from __future__ import annotations

import json

from phase_space_validator.analysis_cli import main


def test_analysis_cli_emits_versioned_json_and_invalid_exit_code(capsys) -> None:
    exit_code = main(["--text", "nabla_x cross nabla_p = hbar^2/(2*pi)"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["schema_version"] == "1.0"
    assert payload["overall_status"] == "invalid"
    assert payload["dimensions"]["status"] == "failed"


def test_analysis_cli_emits_human_readable_report(capsys) -> None:
    exit_code = main(
        ["--text", "nabla_x cross nabla_p = 0", "--format", "text"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "PSIV analysis report 1.0" in captured.out
    assert "SYMBOLIC_COUNTEREXAMPLE" in captured.out


def test_analysis_cli_preserves_parse_error_exit_code(capsys) -> None:
    exit_code = main(["--text", "2 pi", "--compact"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 2
    assert payload["overall_status"] == "input_error"
    assert payload["diagnostics"][0]["code"] == "EXPLICIT_MULTIPLICATION_REQUIRED"


def test_analysis_cli_reads_utf8_file(tmp_path, capsys) -> None:
    identity = tmp_path / "identity.txt"
    identity.write_text("nabla_x cross nabla_p = 0", encoding="utf-8")

    exit_code = main(["--file", str(identity)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["input"]["source_name"] == str(identity)
