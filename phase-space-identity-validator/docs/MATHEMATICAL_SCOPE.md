# Mathematical scope

The validator is a **structural consistency checker**, not a theorem prover.

## Implemented layers

The metadata validator can detect declared mismatches in:

1. tensor rank;
2. physical dimensions;
3. operator-versus-value type;
4. differential order;
5. coordinate covariance/intrinsic status;
6. mathematical domain;
7. distributional qualification.

The controlled expression layer can represent and normalize a strict grammar containing symbols, constants, derivatives, gradients, products, sums, powers, commutators, Poisson brackets, wedge products, tensor products, cross products, and equalities.

A parsed expression is syntax, not a proof and not yet a physical interpretation.

## Current limits

The toolkit does not yet parse arbitrary LaTeX, infer dimensions or tensor metadata automatically, establish operator domains, test Jacobi identities, or prove equality. A passing metadata report means only that the supplied declarations are structurally compatible.

## Canonical dimension symbols

The metadata examples use `A` for action. The dimension-inference release will use a configurable basis such as mass `M`, length `L`, time `T`, charge `Q`, and temperature `Theta`.

## Research roadmap

- Dimension inference and simplification over the controlled AST.
- Tensor-index variance and contraction checks.
- A controlled text or LaTeX front end that emits the AST.
- Poisson/Jacobi identity verification.
- SymPy integration for symbolic counterexamples.
- Distributional equality annotations.
- Canonical versus mechanical momentum profiles.
- Magnetic and Berry-curved phase-space catalogs.
