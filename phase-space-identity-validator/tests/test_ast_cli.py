from __future__ import annotations

from pathlib import Path

from phase_space_validator.ast_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_ast_cli_prints_summary(capsys) -> None:
    result = main(
        [
            str(ROOT / "examples/ast/invalid-cross-gradient-expression.json"),
            "--summary",
            "--compact",
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert '"node_count":11' in captured.out
    assert '"root_type":"equality"' in captured.out


def test_ast_cli_reports_parse_error(tmp_path, capsys) -> None:
    malformed = tmp_path / "bad.json"
    malformed.write_text('{"type":"product","factors":[]}', encoding="utf-8")
    result = main([str(malformed)])
    captured = capsys.readouterr()
    assert result == 2
    assert "product requires at least two factors" in captured.err
