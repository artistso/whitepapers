# Phase-Space Identity Validator

A reproducible research package for representing and checking proposed identities in classical and quantum phase space.

The initial motivating example is the invalid ansatz

```text
nabla_x cross nabla_p = hbar^2 / (2 pi)
```

The toolkit now rejects this identity through independent metadata, dimensional, and tensor-index analyses:

1. the metadata validator detects declared rank, operator/value, domain, covariance, and dimension mismatches;
2. the AST dimension engine derives inverse action on the left and action squared on the right;
3. the tensor engine derives a rank-one left side and scalar right side, while also identifying that `nabla_x` and `nabla_p` belong to different coordinate spaces.

> **Scope:** this toolkit is a consistency checker, not a theorem prover. Parsing or passing validation does not establish that an equation is mathematically or physically true.

## Capabilities in v0.4.0

- strict controlled expression AST;
- JSON round-trip normalization;
- path-aware errors for malformed expression trees;
- recursive physical-dimension inference;
- tensor-rank and free-index inference;
- covariant and contravariant index tokens;
- Einstein contraction checks;
- Kronecker-delta contraction support;
- cross-product rank, vector-space, and 3D restrictions;
- combined dimension and tensor reports;
- configurable symbol, coordinate, and tensor registries;
- metadata checks for properties not yet inferable from syntax.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

psiv examples/invalid-cross-gradient.json
psiv-ast examples/ast/invalid-cross-gradient-expression.json --summary
psiv-dim examples/ast/invalid-cross-gradient-expression.json
psiv-tensor examples/ast/invalid-cross-gradient-expression.json
psiv-check examples/ast/invalid-cross-gradient-expression.json
pytest
```

The combined checker reports at least:

```text
DIMENSION_MISMATCH
TYPE_RANK_MISMATCH
CROSS_PRODUCT_SPACE_MISMATCH
```

The canonical commutator passes both dimension and tensor checks:

```bash
psiv-check examples/ast/canonical-commutator-expression.json
```

The Kronecker example verifies an explicit contraction:

```bash
psiv-check examples/ast/kronecker-contraction-expression.json
```

representing

```text
delta^i_j x^j = x^i
```

## Controlled expression language

The expression layer represents syntax without silently assigning physical meaning. Supported nodes include:

```text
Symbol
Constant
Derivative
Gradient
CrossProduct
TensorProduct
WedgeProduct
Commutator
PoissonBracket
Power
Product
Sum
Equality
```

The complete grammar is documented in `docs/EXPRESSION_AST.md`.

## Dimension inference

The default registry assigns:

```text
x       -> L
p       -> M L T^-1
hbar    -> M L^2 T^-1
nabla_x -> L^-1
nabla_p -> M^-1 L^-1 T
```

Inference is recursive across derivatives, gradients, products, integer powers, sums, cross products, tensor products, wedge products, commutators, Poisson brackets, and equalities.

The complete rules are documented in `docs/DIMENSION_INFERENCE.md`.

## Tensor and index inference

Indices use compact tokens:

```text
_i   covariant
^i   contravariant
i    covariant legacy form
```

A repeated index contracts only when it appears exactly twice in the same vector space with opposite variance. The checker detects same-variance repetition, excessive multiplicity, free-index mismatch, invalid tensor powers, incompatible tensor sums, and invalid cross products.

The complete rules are documented in `docs/TENSOR_INFERENCE.md`.

## Metadata validation

The original metadata validator remains available for properties not yet inferred from syntax alone:

```text
TYPE_RANK_MISMATCH
DIMENSION_MISMATCH
OPERATOR_VALUE_MISMATCH
DIFFERENTIAL_ORDER_MISMATCH
NONINTRINSIC_CONSTRUCTION
DOMAIN_MISMATCH
DISTRIBUTIONAL_QUALIFICATION
```

## Repository layout

```text
phase-space-identity-validator/
├── src/phase_space_validator/   # AST, inference, validation, and CLIs
├── tests/                       # unit tests
├── examples/                    # metadata and AST examples
├── docs/                        # grammar, inference, scope, and roadmap
├── manuscript/                  # modular technical-note source
│   ├── sections/
│   ├── phase_space_clarification.tex
│   ├── references.bib
│   └── Makefile
├── pyproject.toml
├── CITATION.cff
└── LICENSE.md
```

The validator workflow runs Ruff and pytest under Python 3.11 and 3.12 and retains JUnit artifacts for diagnostics.

## Technical note

The accompanying paper is:

> **Mixed Derivatives in Phase Space: Poisson Geometry, Quantum Commutators, and Quantized Circulation**

It formalizes the distinction between commuting mixed derivatives, the generally nonzero formal mixed cross-gradient, Poisson geometry, quantum commutators, and quantized circulation. A dedicated table maps the motivating ansatz to the validator's stable diagnostic codes.

Build it locally with:

```bash
cd manuscript
make
```

The manuscript workflow compiles and verifies the PDF on GitHub Actions and uploads `phase-space-clarification-pdf` as a workflow artifact. Generated PDFs are not committed to the repository.

## Roadmap

The next research phases are symbolic counterexample generation, a controlled text/LaTeX front end, metric-aware index operations, Jacobi identity checks, and catalogs for magnetic and Berry-curved phase spaces.
