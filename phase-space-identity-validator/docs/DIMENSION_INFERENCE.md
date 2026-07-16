# Dimension inference

Version 0.3.0 adds recursive physical-dimension inference over the controlled expression AST.

## Base representation

Dimensions are immutable sparse exponent vectors over a configurable basis. The default canonical registry uses:

```text
M      mass
L      length
T      time
```

Derived defaults include:

```text
x       -> L
p       -> M L T^-1
hbar    -> M L^2 T^-1
nabla_x -> L^-1
nabla_p -> M^-1 L^-1 T
```

Kronecker delta, the identity operator, numeric constants, `i`, and `pi` are dimensionless in the default examples.

## Recursive rules

| Node | Inference rule |
|---|---|
| `symbol` | Registry lookup |
| `constant` | Dimensionless |
| `derivative` | Operand divided by coordinate dimension to the declared order |
| `gradient` | Inverse coordinate dimension, multiplied by the operand when applied |
| `product` | Product of factor dimensions |
| `power` | Multiply every base exponent by the integer power |
| `sum` | All terms must have identical dimensions |
| `cross_product` | Product of operand dimensions |
| `tensor_product` | Product of operand dimensions |
| `wedge_product` | Product of operand dimensions |
| `commutator` | Product of operand dimensions |
| `poisson_bracket` | Product of operand dimensions times the configured Poisson scale |
| `equality` | Infer both sides and compare |

For canonical phase space, the Poisson scale is inverse action.

## Motivating ansatz

Run:

```bash
psiv-dim examples/ast/invalid-cross-gradient-expression.json
```

The engine derives:

```text
left:  M^-1 L^-2 T
right: M^2 L^4 T^-2
code:  DIMENSION_MISMATCH
```

The left side is inverse action. The right side is action squared.

The canonical commutator example returns consistent action dimensions on both sides:

```bash
psiv-dim examples/ast/canonical-commutator-expression.json
```

## Failure modes

Dimension inference uses explicit stable errors:

- `UNKNOWN_SYMBOL`
- `UNKNOWN_COORDINATE`
- `INCOMPATIBLE_SUM`
- `DIMENSION_MISMATCH`
- `UNSUPPORTED_NODE`

Each error records the AST path at which inference failed.

## Boundary

Dimension compatibility is necessary but not sufficient for a valid identity. A dimensionally consistent expression may still fail tensor, domain, covariance, operator-ordering, regularity, or physical-assumption checks.
