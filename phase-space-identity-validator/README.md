# Phase-Space Identity Validator

A reproducible research package for representing and checking proposed identities in classical and quantum phase space.

The initial motivating example is the invalid ansatz

```text
nabla_x cross nabla_p = hbar^2 / (2 pi)
```

The toolkit rejects this identity through independent metadata, dimensional, and tensor-index analyses:

1. the metadata validator detects declared rank, operator/value, domain, covariance, and dimension mismatches;
2. the AST dimension engine derives inverse action on the left and action squared on the right;
3. the tensor engine derives a rank-one left side and scalar right side and identifies that `nabla_x` and `nabla_p` belong to different coordinate spaces.

It also symbolically disproves the related universal claim

```text
nabla_x cross nabla_p = 0
```

by finding the witness `x1*p2`, for which the operator returns `(0, 0, 1)`.

> **Scope:** this toolkit is a consistency checker and counterexample search system, not a theorem prover. Parsing, passing validation, or failing to find a counterexample does not establish that an equation is mathematically or physically true.

## Capabilities in v0.5.0

- strict controlled expression AST;
- recursive physical-dimension inference;
- tensor-rank and free-index inference;
- variance-aware Einstein contraction;
- Kronecker-delta contraction support;
- cross-product rank, vector-space, and 3D restrictions;
- combined dimension and tensor reports;
- exact symbolic differentiation and simplification with SymPy;
- deterministic low-degree counterexample search;
- explicit evidence levels distinguishing falsification from inconclusive search;
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
psiv-falsify examples/ast/cross-gradient-zero-expression.json
pytest
```

The combined checker reports at least:

```text
DIMENSION_MISMATCH
TYPE_RANK_MISMATCH
CROSS_PRODUCT_SPACE_MISMATCH
```

The falsifier reports:

```text
[COUNTEREXAMPLE] universal claim falsified
- witness:      p2*x1
- left action:  ('0', '0', '1')
- right action: ('0', '0', '0')
- residual:     ('0', '0', '1')
- tested:       2 candidate(s)
```

The canonical commutator passes dimension and tensor checks:

```bash
psiv-check examples/ast/canonical-commutator-expression.json
```

The Kronecker example verifies

```text
delta^i_j x^j = x^i
```

with:

```bash
psiv-check examples/ast/kronecker-contraction-expression.json
```

## Controlled expression language

The expression layer represents syntax without silently assigning physical meaning. Supported nodes include symbols, constants, derivatives, gradients, cross products, tensor products, wedge products, commutators, Poisson brackets, powers, products, sums, and equalities.

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

The complete rules are documented in `docs/DIMENSION_INFERENCE.md`.

## Tensor and index inference

Indices use compact tokens:

```text
_i   covariant
^i   contravariant
i    covariant legacy form
```

A repeated index contracts only when it appears exactly twice in the same vector space with opposite variance. The complete rules are documented in `docs/TENSOR_INFERENCE.md`.

## Symbolic counterexamples

The v0.5 falsifier supports universal mixed cross-gradient claims against zero. It searches the nine deterministic bilinear witnesses `x_i p_j` and uses exact symbolic differentiation. A found witness disproves the claim; `NO_COUNTEREXAMPLE_FOUND` means only that the configured finite search space was exhausted.

The full scope and evidence semantics are documented in `docs/SYMBOLIC_COUNTEREXAMPLES.md`.

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
├── src/phase_space_validator/   # AST, inference, falsification, validation, and CLIs
├── tests/                       # unit tests
├── examples/                    # metadata and AST examples
├── docs/                        # grammar, inference, falsification, scope, and roadmap
├── manuscript/                  # modular technical-note source
│   ├── sections/
│   ├── phase_space_clarification.tex
│   ├── references.bib
│   └── Makefile
├── pyproject.toml
├── CITATION.cff
└── LICENSE.md
```

The validator workflow runs Ruff and pytest under Python 3.11 and 3.12 and retains Ruff and JUnit artifacts for diagnostics.

## Technical note

The accompanying paper is:

> **Mixed Derivatives in Phase Space: Poisson Geometry, Quantum Commutators, and Quantized Circulation**

It formalizes the distinction between commuting mixed derivatives, the generally nonzero formal mixed cross-gradient, Poisson geometry, quantum commutators, and quantized circulation.

Build it locally with:

```bash
cd manuscript
make
```

The manuscript workflow compiles and verifies the PDF on GitHub Actions and uploads `phase-space-clarification-pdf` as a workflow artifact.

## Roadmap

The next research phases are a controlled text/LaTeX front end, broader polynomial witness generation, metric-aware index operations, Jacobi identity checks, and catalogs for magnetic and Berry-curved phase spaces.
