# Phase-Space Identity Validator

A reproducible research package for representing and checking proposed identities in classical and quantum phase space.

The initial motivating example is the invalid ansatz

```text
nabla_x cross nabla_p = hbar^2 / (2 pi)
```

The toolkit now rejects this identity in two independent ways:

1. the metadata validator detects tensor, operator/value, domain, covariance, and declared-dimension mismatches;
2. the AST dimension engine derives inverse action on the left and action squared on the right.

> **Scope:** this toolkit is a consistency checker, not a theorem prover. Parsing or passing validation does not establish that an equation is mathematically or physically true.

## Capabilities in v0.3.0

- strict controlled expression AST;
- JSON round-trip normalization;
- path-aware errors for malformed expression trees;
- deterministic traversal, node counts, and tree depth;
- recursive physical-dimension inference;
- configurable symbol and coordinate registries;
- equality dimension reports with stable diagnostic codes;
- tensor rank checks from declared metadata;
- operator-versus-value checks;
- differential-order diagnostics;
- intrinsic/covariant status checks;
- domain compatibility checks;
- distributional qualification warnings.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

psiv examples/invalid-cross-gradient.json
psiv-ast examples/ast/invalid-cross-gradient-expression.json --summary
psiv-dim examples/ast/invalid-cross-gradient-expression.json
psiv-dim examples/ast/canonical-commutator-expression.json
pytest
```

The motivating AST produces:

```text
left:  M^-1 L^-2 T
right: M^2 L^4 T^-2
code:  DIMENSION_MISMATCH
```

The canonical commutator produces action dimensions on both sides:

```text
M L^2 T^-1
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

Stable dimension errors include:

```text
UNKNOWN_SYMBOL
UNKNOWN_COORDINATE
INCOMPATIBLE_SUM
DIMENSION_MISMATCH
UNSUPPORTED_NODE
```

The complete inference rules are documented in `docs/DIMENSION_INFERENCE.md`.

## Metadata validation

The original metadata validator remains available for properties that cannot yet be inferred from syntax alone:

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

The validator workflow runs Ruff and pytest under Python 3.11 and 3.12.

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

The next research phases are tensor-index validation, symbolic counterexample generation, a controlled text/LaTeX front end, Jacobi identity checks, and catalogs for magnetic and Berry-curved phase spaces.
