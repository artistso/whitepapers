# Phase-Space Identity Validator

A reproducible research package for representing and checking proposed identities in classical and quantum phase space.

The initial motivating example is the invalid ansatz

```text
nabla_x cross nabla_p = hbar^2 / (2 pi)
```

The metadata validator rejects it because the two sides differ in tensor rank, physical dimensions, operator/value type, domain, and coordinate-invariance status.

> **Scope:** this toolkit is a consistency checker, not a theorem prover. Parsing or passing validation does not establish that an equation is mathematically or physically true.

## Capabilities in v0.2.0

- strict controlled expression AST;
- JSON round-trip normalization;
- path-aware errors for malformed expression trees;
- deterministic traversal, node counts, and tree depth;
- tensor rank checks from declared metadata;
- dimension exponent-map checks from declared metadata;
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
psiv examples/canonical-commutator.json --json
psiv-ast examples/ast/invalid-cross-gradient-expression.json --summary
pytest
```

Expected invalid metadata result:

```text
[FAIL] Mixed cross-gradient equals hbar squared over two pi
- ERROR TYPE_RANK_MISMATCH: ...
- ERROR DIMENSION_MISMATCH: ...
- ERROR OPERATOR_VALUE_MISMATCH: ...
- ERROR NONINTRINSIC_CONSTRUCTION: ...
- ERROR DOMAIN_MISMATCH: ...
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

Example:

```json
{
  "type": "equality",
  "left": {
    "type": "cross_product",
    "left": {"type": "gradient", "space": "x"},
    "right": {"type": "gradient", "space": "p"}
  },
  "right": {
    "type": "power",
    "base": {"type": "symbol", "name": "hbar"},
    "exponent": 2
  }
}
```

The complete grammar is documented in `docs/EXPRESSION_AST.md`.

## Metadata identity specification

The existing validator accepts explicitly declared metadata:

```json
{
  "name": "Canonical commutation relation",
  "lhs": {
    "label": "[x_i, p_j]",
    "rank": 2,
    "dimensions": {"A": 1},
    "is_operator": true,
    "intrinsic": true,
    "domain": "Hilbert-space operators"
  },
  "rhs": {
    "label": "i hbar delta_ij I",
    "rank": 2,
    "dimensions": {"A": 1},
    "is_operator": true,
    "intrinsic": true,
    "domain": "Hilbert-space operators"
  }
}
```

`A` denotes action. Zero exponents are removed during normalization.

## Repository layout

```text
phase-space-identity-validator/
├── src/phase_space_validator/   # AST, validation library, and CLIs
├── tests/                       # unit tests
├── examples/                    # metadata and AST examples
├── docs/                        # grammar, scope, and roadmap
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

The next research phases are automatic dimension inference over the AST, tensor-index validation, symbolic counterexample generation, Jacobi identity checks, and catalogs for magnetic and Berry-curved phase spaces.
