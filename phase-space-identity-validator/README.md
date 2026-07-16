# Phase-Space Identity Validator

A reproducible research package for parsing, representing, and checking proposed identities in classical and quantum phase space.

The motivating invalid ansatz is

```text
nabla_x cross nabla_p = hbar^2 / (2*pi)
```

The toolkit rejects it independently through:

1. declared metadata checks;
2. automatic physical-dimension inference;
3. tensor-rank and vector-space inference.

It also disproves the related universal claim

```text
nabla_x cross nabla_p = 0
```

by finding the witness `x1*p2`, for which the operator returns `(0, 0, 1)`.

> **Scope:** this toolkit is a parser, consistency checker, and finite counterexample search system—not a theorem prover. Successful parsing, structural consistency, or failure to find a witness does not prove an identity.

## Capabilities in v0.6.0

- bounded human-readable mathematical text parser;
- position-aware tokenization and parse errors;
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

psiv-parse --text "nabla_x cross nabla_p = hbar^2/(2*pi)" --summary
psiv-parse --file examples/text/canonical-commutator.txt
psiv-check examples/ast/invalid-cross-gradient-expression.json
psiv-falsify examples/ast/cross-gradient-zero-expression.json
pytest
```

The parser emits canonical AST JSON. The same text fixture can then be compared with the version-controlled AST examples.

## Controlled text examples

```text
nabla_x cross nabla_p = hbar^2/(2*pi)
[x_i,p_j] = i*hbar*delta_ij*I
delta^i_j*x^j = x^i
{x_i,p_j} = delta_ij
partial(x^3,x,2)
nabla_x(x^2)
```

The text layer requires explicit multiplication. For example, `2*pi` is valid while `2 pi` returns `EXPLICIT_MULTIPLICATION_REQUIRED`.

Compact index syntax is supported:

```text
_i       covariant
^i       contravariant
delta_ij two compact covariant indices
T^{mu}   one multi-character contravariant index
```

Numeric superscripts are powers, so `hbar^2` becomes a `Power` node rather than an index.

The complete grammar and exclusions are documented in `docs/TEXT_PARSER.md`.

## Structural diagnostics

The motivating ansatz produces at least:

```text
DIMENSION_MISMATCH
TYPE_RANK_MISMATCH
CROSS_PRODUCT_SPACE_MISMATCH
```

The canonical commutator passes dimension and tensor checks:

```bash
psiv-check examples/ast/canonical-commutator-expression.json
```

The Kronecker example verifies

```text
delta^i_j*x^j = x^i
```

with:

```bash
psiv-check examples/ast/kronecker-contraction-expression.json
```

## Symbolic counterexamples

The falsifier searches deterministic bilinear witnesses `x_i p_j` using exact differentiation. A found witness disproves a universal claim; `NO_COUNTEREXAMPLE_FOUND` means only that the configured finite search space was exhausted.

```bash
psiv-falsify examples/ast/cross-gradient-zero-expression.json
```

Expected evidence:

```text
[COUNTEREXAMPLE] universal claim falsified
- witness:      p2*x1
- left action:  ('0', '0', '1')
- right action: ('0', '0', '0')
- residual:     ('0', '0', '1')
- tested:       2 candidate(s)
```

The evidence model is documented in `docs/SYMBOLIC_COUNTEREXAMPLES.md`.

## Commands

| Command | Purpose |
|---|---|
| `psiv` | Validate explicitly declared metadata |
| `psiv-parse` | Parse controlled text into canonical AST JSON |
| `psiv-ast` | Normalize and inspect AST JSON |
| `psiv-dim` | Infer and compare physical dimensions |
| `psiv-tensor` | Infer rank and free indices |
| `psiv-check` | Combine dimension and tensor checks |
| `psiv-falsify` | Search for symbolic counterexamples |

## Repository layout

```text
phase-space-identity-validator/
├── src/phase_space_validator/   # parser, AST, inference, falsification, validation, CLIs
├── tests/                       # unit and command-line tests
├── examples/
│   ├── ast/                     # canonical JSON fixtures
│   └── text/                    # human-readable equivalents
├── docs/                        # grammar, inference, evidence, scope, roadmap
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

It distinguishes commuting mixed derivatives, the generally nonzero formal mixed cross-gradient, Poisson geometry, quantum commutators, and quantized circulation.

Build it locally with:

```bash
cd manuscript
make
```

The manuscript workflow compiles and verifies the PDF on GitHub Actions and uploads `phase-space-clarification-pdf` as a workflow artifact.

## Roadmap

The next research phase is a unified, versioned diagnostic and evidence report. Later milestones include a benchmark corpus, broader witness generation, metric-aware index operations, Jacobi checks, and magnetic and Berry-curved phase-space profiles.
