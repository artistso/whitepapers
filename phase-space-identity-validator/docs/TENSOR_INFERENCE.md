# Tensor and index inference

Version 0.4.0 adds a best-effort tensor-analysis pass over the controlled expression AST.

The pass is deliberately separate from physical-dimension inference. Matching dimensions do not imply matching tensor type, and matching tensor type does not prove an identity.

## Index notation

Symbol indices use compact string tokens:

```text
_i   covariant index i
^i   contravariant index i
i    covariant index i for backward compatibility
```

Examples:

```json
{"type": "symbol", "name": "x", "indices": ["_i"]}
{"type": "symbol", "name": "delta", "indices": ["^i", "_j"]}
```

An index contracts only when the same name appears exactly twice in the same vector space with opposite variance.

## Default tensor registry

| Symbol | Rank | Space |
|---|---:|---|
| `x` | 1 | spatial |
| `p` | 1 | spatial |
| `hbar` | 0 | scalar |
| `delta` | 2 | spatial |
| `epsilon` | 3 | spatial |
| `I` | 0 | scalar |

Position and momentum gradient operators are assigned to distinct coordinate spaces named `position` and `momentum`. This allows the checker to identify that a formal cross product between `nabla_x` and `nabla_p` combines objects from different spaces.

## Supported operations

- symbols and constants;
- derivatives and gradients;
- products with Einstein contraction;
- tensor and wedge products;
- commutators and Poisson brackets;
- sums with free-index compatibility checks;
- scalar powers;
- three-dimensional cross products;
- equality rank and free-index comparison.

## Kronecker contraction

The expression

```text
delta^i_j x^j = x^i
```

is represented by `examples/ast/kronecker-contraction-expression.json`. The repeated index `j` contracts because it appears once covariantly and once contravariantly. The resulting signature has one free upper index `i`.

## Cross-product restrictions

A cross product must satisfy all of the following in the current model:

1. both operands are rank-one tensors;
2. both operands belong to the same vector space;
3. that vector space is configured as three-dimensional.

The motivating expression fails the second condition because `nabla_x` and `nabla_p` belong to different coordinate spaces. Its result is still assigned a best-effort rank-one signature so the enclosing equality can also report `TYPE_RANK_MISMATCH` against the scalar right-hand side.

## Stable diagnostics

- `TYPE_RANK_MISMATCH`
- `FREE_INDEX_MISMATCH`
- `INDEX_COUNT_MISMATCH`
- `INVALID_INDEX_TOKEN`
- `UNKNOWN_TENSOR_SYMBOL`
- `SAME_VARIANCE_CONTRACTION`
- `INDEX_MULTIPLICITY`
- `TENSOR_SUM_MISMATCH`
- `TENSOR_POWER_UNDEFINED`
- `CROSS_PRODUCT_REQUIRES_VECTORS`
- `CROSS_PRODUCT_REQUIRES_3D`
- `CROSS_PRODUCT_SPACE_MISMATCH`
- `UNSUPPORTED_TENSOR_NODE`

## Commands

```bash
psiv-tensor examples/ast/invalid-cross-gradient-expression.json
psiv-tensor examples/ast/kronecker-contraction-expression.json --json
psiv-check examples/ast/invalid-cross-gradient-expression.json
```

`psiv-check` combines the dimension and tensor passes. For the motivating ansatz it reports at least:

```text
DIMENSION_MISMATCH
TYPE_RANK_MISMATCH
CROSS_PRODUCT_SPACE_MISMATCH
```

## Limits

The implementation does not yet model metrics, raising and lowering operations, Young symmetries, trace-free constraints, spinor indices, density weights, curved-bundle connections, or non-Euclidean cross-product analogues. Anonymous indices introduced by gradients and cross products act as name wildcards during equality comparison, but variance and vector-space identity remain enforced.
