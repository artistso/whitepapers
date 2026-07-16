# Controlled expression AST

Version 0.2.0 introduces a strict JSON expression grammar. This layer represents mathematical syntax only; it does not yet infer dimensions, tensor rank, or truth.

## Node types

| JSON `type` | Required fields | Purpose |
|---|---|---|
| `symbol` | `name` | Named mathematical object, with optional `indices` and `space` |
| `constant` | `value` | Numeric or named dimensionless constant |
| `derivative` | `variable`, `operand` | Ordinary or partial derivative, with optional positive `order` |
| `gradient` | `space` | Gradient operator, optionally applied to an `operand` |
| `cross_product` | `left`, `right` | Ordered cross-product syntax |
| `tensor_product` | `left`, `right` | Tensor product |
| `wedge_product` | `left`, `right` | Antisymmetric wedge product |
| `commutator` | `left`, `right` | Operator commutator |
| `poisson_bracket` | `left`, `right` | Poisson bracket |
| `power` | `base`, `exponent` | Integer power |
| `product` | `factors` | Product of at least two expressions |
| `sum` | `terms` | Sum of at least two expressions |
| `equality` | `left`, `right` | Equality or explicitly supported equivalent relation |

Unknown fields and unknown node types are rejected. Parse errors include a JSON-path-style location such as `$.right.factors[1]`.

## Example

The motivating ansatz is represented structurally as:

```json
{
  "type": "equality",
  "left": {
    "type": "cross_product",
    "left": {"type": "gradient", "space": "x"},
    "right": {"type": "gradient", "space": "p"}
  },
  "right": {
    "type": "product",
    "factors": [
      {
        "type": "power",
        "base": {"type": "symbol", "name": "hbar"},
        "exponent": 2
      },
      {
        "type": "power",
        "base": {
          "type": "product",
          "factors": [
            {"type": "constant", "value": 2},
            {"type": "constant", "value": "pi"}
          ]
        },
        "exponent": -1
      }
    ]
  }
}
```

Normalize and inspect a tree with:

```bash
psiv-ast examples/ast/invalid-cross-gradient-expression.json --summary
```

The summary reports the root node type, pre-order node count, and tree depth.

## Current boundary

The AST records syntax but deliberately does not assign physical meaning. Dimension inference, index variance, operator-domain inference, and symbolic evaluation are separate later passes. This separation prevents the parser from silently smuggling physical assumptions into the syntax layer.
