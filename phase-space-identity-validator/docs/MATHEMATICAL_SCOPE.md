# Mathematical scope

The validator is a **controlled parser, structural consistency checker, and finite counterexample search system**, not a theorem prover.

## Implemented layers

The text layer tokenizes and parses a bounded mathematical notation into the strict expression AST. It supports explicit arithmetic, powers, indexed symbols, gradients, partial derivatives, cross/wedge/tensor products, commutators, Poisson brackets, parentheses, and one equality relation. Every failure includes a stable code, offset, line, and column.

The controlled expression layer represents and normalizes symbols, constants, derivatives, gradients, products, sums, powers, commutators, Poisson brackets, wedge products, tensor products, cross products, and equalities.

The metadata validator detects declared mismatches in tensor rank, physical dimensions, operator/value type, differential order, covariance status, mathematical domain, and distributional qualification.

The dimension layer recursively infers base-dimension exponent vectors for the controlled AST. It supports configurable symbol and coordinate registries, canonical Poisson scaling, equality comparisons, and path-aware failures.

The tensor layer recursively infers rank and free indices. It supports explicit covariant and contravariant index tokens, Einstein contraction, Kronecker-delta contraction, free-index comparison, tensor-sum compatibility, and three-dimensional cross-product restrictions.

The symbolic layer uses exact differentiation and simplification to search a finite witness class for counterexamples to supported universal operator claims. The initial search covers mixed cross-gradient equalities against zero and deterministic bilinear witnesses `x_i p_j`.

A successfully parsed, dimensionally consistent, tensorially consistent, or unsuccessfully searched expression is not proved.

## Evidence semantics

```text
COUNTEREXAMPLE
```

means a concrete witness with nonzero residual was found. One counterexample disproves a universal identity.

```text
NO_COUNTEREXAMPLE_FOUND
```

means only that no witness was found in the configured finite search space. It is not positive evidence strong enough to establish the identity.

## Text-parser boundary

The v0.6 text grammar is intentionally smaller than LaTeX. It requires explicit multiplication and rejects ambiguous notation. It does not support arbitrary macros, prose interpretation, implicit multiplication, integrals, limits, summation binders, matrix literals, fractional powers, or user-defined functions.

The parser emits explicit variance tokens. Legacy AST files with unprefixed covariant indices remain accepted by the tensor layer.

## Current limits

The toolkit does not infer operator domains, manipulate metrics, raise or lower indices automatically, model spinor or density indices, search arbitrary function spaces, test Jacobi identities, or prove equality. Dimension and tensor compatibility are necessary but not sufficient for a valid physical identity.

## Canonical dimension basis

The default registry uses mass `M`, length `L`, and time `T`:

```text
x    -> L
p    -> M L T^-1
hbar -> M L^2 T^-1
```

Additional registries may introduce charge `Q`, temperature `Theta`, or system-specific dimensions.

## Default tensor conventions

```text
_i   covariant index
^i   contravariant index
i    covariant legacy index
```

A contraction occurs only when an index appears exactly twice, in the same vector space, with opposite variance. The default cross product is defined only for rank-one operands in the same configured three-dimensional vector space.

## Research roadmap

- A unified and versioned diagnostic/evidence report.
- A reviewed benchmark corpus with provenance and assumptions.
- Broader configurable polynomial witness generation.
- Metric-aware raising, lowering, and trace operations.
- Poisson/Jacobi identity verification.
- Distributional equality annotations.
- Canonical versus mechanical momentum profiles.
- Magnetic and Berry-curved phase-space catalogs.
