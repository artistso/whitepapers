from __future__ import annotations

from phase_space_validator.cli import main


def test_cli_returns_failure_for_invalid_identity() -> None:
    assert main(["examples/invalid-cross-gradient.json"]) == 1


def test_cli_returns_success_for_consistent_identity() -> None:
    assert main(["examples/canonical-commutator.json", "--json"]) == 0
