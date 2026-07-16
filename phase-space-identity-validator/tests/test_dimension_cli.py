from __future__ import annotations

from pathlib import Path

from phase_space_validator.dimension_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_dimension_cli_rejects_motivating_ansatz(capsys) -> None:
    result = main(
        [
            str(ROOT / "examples/ast/invalid-cross-gradient-expression.json"),
            "--compact",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert '"code":"DIMENSION_MISMATCH"' in captured.out
    assert '"formatted":"M^-1 L^-2 T"' in captured.out
    assert '"formatted":"M^2 L^4 T^-2"' in captured.out


def test_dimension_cli_accepts_canonical_commutator(capsys) -> None:
    result = main(
        [
            str(ROOT / "examples/ast/canonical-commutator-expression.json"),
            "--compact",
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert '"consistent":true' in captured.out
    assert captured.err == ""


def test_dimension_cli_requires_equality(tmp_path, capsys) -> None:
    expression = tmp_path / "symbol.json"
    expression.write_text('{"type":"symbol","name":"x"}', encoding="utf-8")
    result = main([str(expression)])
    captured = capsys.readouterr()
    assert result == 2
    assert "root expression must be an equality" in captured.err
