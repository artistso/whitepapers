from __future__ import annotations

from phase_space_validator.falsify_cli import main


def test_falsify_cli_returns_failure_for_disproved_claim() -> None:
    assert main(["examples/ast/cross-gradient-zero-expression.json"]) == 1


def test_falsify_cli_emits_json() -> None:
    assert main(["examples/ast/cross-gradient-zero-expression.json", "--json"]) == 1


def test_falsify_cli_rejects_unsupported_claim() -> None:
    assert main(["examples/ast/canonical-commutator-expression.json"]) == 2
