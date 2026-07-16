# Symbolic counterexample search

Version 0.5.0 adds a narrowly scoped symbolic falsifier for universal mixed cross-gradient claims.

The feature uses SymPy for exact symbolic differentiation and simplification. Its purpose is to find a single witness that disproves a universal identity. It is not a theorem prover.

## Supported claim

The initial supported form is

```text
nabla_x cross nabla_p = 0
```

or the same equality with the zero and operator sides reversed.

The operator acts on a scalar test function `f` as

```text
component 1 = d_x2 d_p3 f - d_x3 d_p2 f
component 2 = d_x3 d_p1 f - d_x1 d_p3 f
component 3 = d_x1 d_p2 f - d_x2 d_p1 f
```

## Deterministic search space

The default search enumerates the nine bilinear monomials

```text
x1 p1, x1 p2, x1 p3,
x2 p1, x2 p2, x2 p3,
x3 p1, x3 p2, x3 p3
```

in that order.

The first candidate `x1 p1` is annihilated. The second candidate `x1 p2` gives

```text
(nabla_x cross nabla_p)(x1 p2) = (0, 0, 1)
```

and therefore disproves the universal zero identity.

## Evidence levels

The output uses one of two evidence classifications:

- `COUNTEREXAMPLE`: a witness with nonzero residual was found;
- `NO_COUNTEREXAMPLE_FOUND`: no witness was found in the configured finite search space.

`NO_COUNTEREXAMPLE_FOUND` is explicitly not a proof.

## Command

```bash
psiv-falsify examples/ast/cross-gradient-zero-expression.json
```

Expected result:

```text
[COUNTEREXAMPLE] universal claim falsified
- witness:      p2*x1
- left action:  ('0', '0', '1')
- right action: ('0', '0', '0')
- residual:     ('0', '0', '1')
- tested:       2 candidate(s)
```

Machine-readable output is available with `--json`.

## Stable errors

- `UNSUPPORTED_SYMBOLIC_CLAIM`
- `UNSUPPORTED_SYMBOLIC_OPERATOR`
- `UNSUPPORTED_SYMBOLIC_EXPRESSION`
- `UNKNOWN_SYMBOLIC_COORDINATE`
- `SYMBOLIC_CROSS_PRODUCT_REQUIRES_3D`

## Current limits

The v0.5 engine supports scalar constants, symbols, sums, products, and integer powers as witness expressions. It does not yet search arbitrary function classes, prove identities, establish convergence, reason about distributions, or evaluate general operator algebras. Future releases may add mixed-derivative commutator verification, user-configurable polynomial degree, simplification budgets, and symbolic Jacobi checks.
