# Mathematical scope

The validator is a **structural consistency checker**, not a theorem prover.

It can currently detect declared mismatches in:

1. tensor rank;
2. physical dimensions;
3. operator-versus-value type;
4. differential order;
5. coordinate covariance/intrinsic status;
6. mathematical domain;
7. distributional qualification.

It does not yet parse arbitrary LaTeX, infer metadata automatically, establish operator domains, test Jacobi identities, or prove equality. A passing report means only that the supplied metadata is structurally compatible.

## Canonical dimension symbols

The examples use `A` for action. Future releases may support a configurable basis such as mass `M`, length `L`, time `T`, charge `Q`, and temperature `Theta`.

## Research roadmap

- LaTeX-to-AST parsing for a controlled expression grammar.
- Dimension inference and simplification.
- Tensor-index variance and contraction checks.
- Poisson/Jacobi identity verification.
- SymPy integration for symbolic counterexamples.
- Distributional equality annotations.
- Canonical versus mechanical momentum profiles.
- Magnetic and Berry-curved phase-space catalogs.
