# Phase-Space Identity Validator

A reproducible research package for checking the declared structural consistency of proposed identities in classical and quantum phase space.

The initial motivating example is the invalid ansatz

```text
nabla_x cross nabla_p = hbar^2 / (2 pi)
```

The validator rejects it because the two sides differ in tensor rank, physical dimensions, operator/value type, domain, and coordinate-invariance status.

> **Scope:** this tool is a consistency checker, not a theorem prover. Passing validation does not establish that an equation is mathematically or physically true.

## Checks in v0.1.0

- tensor rank;
- dimension exponent maps;
- operator versus value;
- differential order;
- intrinsic/covariant status;
- domain compatibility;
- distributional qualification.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

psiv examples/invalid-cross-gradient.json
psiv examples/canonical-commutator.json --json
pytest
```

Expected invalid-example result:

```text
[FAIL] Mixed cross-gradient equals hbar squared over two pi
- ERROR TYPE_RANK_MISMATCH: ...
- ERROR DIMENSION_MISMATCH: ...
- ERROR OPERATOR_VALUE_MISMATCH: ...
- ERROR NONINTRINSIC_CONSTRUCTION: ...
- ERROR DOMAIN_MISMATCH: ...
```

## Identity specification

Each side declares metadata explicitly:

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
├── src/phase_space_validator/   # validation library and CLI
├── tests/                       # unit tests
├── examples/                    # valid and invalid identity specifications
├── docs/                        # mathematical scope and roadmap
├── manuscript/                  # technical-note source
├── pyproject.toml
├── CITATION.cff
└── LICENSE.md
```

The repository-level GitHub Actions workflow runs Ruff and pytest under Python 3.11 and 3.12.

## Mathematical foundation

The accompanying research program distinguishes:

- commuting mixed derivatives, `[partial_xi, partial_pj] = 0`;
- the generally nonzero formal mixed cross-gradient;
- the canonical Poisson bivector;
- canonical operator and Moyal star commutators;
- physical-space quantized circulation;
- angular-momentum operator algebra.

## Roadmap

The next research phases are controlled LaTeX parsing, automatic dimension inference, tensor-index validation, symbolic counterexample generation, Jacobi identity checks, and catalogs for magnetic and Berry-curved phase spaces.
