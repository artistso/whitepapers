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

The controlled expression layer represents and normalizes symbols, constants, derivatives, gradients, products, sums, powers, commutators, Poisson brackets, wedge products, tensor products, cross products, and equalities.

The dimension layer recursively infers base-dimension exponent vectors for the controlled AST. It supports configurable symbol and coordinate registries, canonical Poisson scaling, equality comparisons, and path-aware failures for unknown symbols, unknown coordinates, and incompatible sums.

A parsed or dimensionally consistent expression is not a proof.

## Current limits

The toolkit does not yet parse arbitrary LaTeX, infer tensor index variance, establish operator domains, test Jacobi identities, or prove equality. Dimension compatibility is necessary but not sufficient for a valid physical identity.

## Canonical dimension basis

The default registry uses mass `M`, length `L`, and time `T`:

```text
x    -> L
p    -> M L T^-1
hbar -> M L^2 T^-1
```

Additional registries may introduce charge `Q`, temperature `Theta`, or system-specific dimensions.

## Research roadmap

- Tensor-index variance and contraction checks.
- A controlled text or LaTeX front end that emits the AST.
- Poisson/Jacobi identity verification.
- SymPy integration for symbolic counterexamples.
- Distributional equality annotations.
- Canonical versus mechanical momentum profiles.
- Magnetic and Berry-curved phase-space catalogs.
