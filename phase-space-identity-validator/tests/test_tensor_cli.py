from __future__ import annotations

from phase_space_validator.check_cli import main as check_main
from phase_space_validator.tensor_cli import main as tensor_main


def test_tensor_cli_rejects_motivating_ansatz() -> None:
    assert tensor_main(["examples/ast/invalid-cross-gradient-expression.json"]) == 1


def test_tensor_cli_accepts_canonical_commutator() -> None:
    assert tensor_main(["examples/ast/canonical-commutator-expression.json", "--json"]) == 0


def test_tensor_cli_accepts_kronecker_contraction() -> None:
    assert tensor_main(["examples/ast/kronecker-contraction-expression.json"]) == 0


def test_tensor_cli_rejects_cross_product_in_two_dimensions() -> None:
    assert (
        tensor_main(
            [
                "examples/ast/invalid-cross-gradient-expression.json",
                "--spatial-dimension",
                "2",
            ]
        )
        == 1
    )


def test_combined_checker_reports_invalid_ansatz() -> None:
    assert check_main(["examples/ast/invalid-cross-gradient-expression.json"]) == 1


def test_combined_checker_accepts_canonical_commutator() -> None:
    assert check_main(["examples/ast/canonical-commutator-expression.json", "--json"]) == 0


def test_combined_checker_accepts_kronecker_contraction() -> None:
    assert check_main(["examples/ast/kronecker-contraction-expression.json"]) == 0
