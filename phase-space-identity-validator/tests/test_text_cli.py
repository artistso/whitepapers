from __future__ import annotations

import json

from phase_space_validator.text_cli import main


def test_text_cli_emits_canonical_json(capsys) -> None:
    exit_code = main(["--text", "[x_i,p_j]=i*hbar*delta_ij*I", "--summary"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"]["root_type"] == "equality"
    assert payload["expression"]["left"]["type"] == "commutator"


def test_text_cli_reports_position_aware_error(capsys) -> None:
    exit_code = main(["--text", "2 pi"])
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert exit_code == 2
    assert payload["error"]["code"] == "EXPLICIT_MULTIPLICATION_REQUIRED"
    assert payload["error"]["column"] == 3
