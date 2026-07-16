# Controlled mathematical text parser

The v0.6 parser converts a deliberately bounded human-readable notation into the strict expression AST. It is not a general TeX parser and does not guess implicit operations.

## Command

```bash
psiv-parse --text "nabla_x cross nabla_p = hbar^2/(2*pi)"
psiv-parse --file examples/text/canonical-commutator.txt --summary
```

Successful output is canonical AST JSON. Failures include a stable diagnostic code, byte offset, line, and column.

## Grammar

```text
expression      := equality

equality        := sum (relation sum)?
relation        := "=" | "≈" | "≡"

sum             := vector_product (("+" | "-") vector_product)*
vector_product  := product (("cross" | "wedge" | "tensor") product)*
product         := unary (("*" | "/") unary)*
unary           := ("+" | "-") unary | power
power           := primary ("^" signed_integer)*

primary         := number
                 | indexed_symbol
                 | gradient
                 | derivative
                 | "(" expression ")"
                 | "[" expression "," expression "]"
                 | "{" expression "," expression "}"

gradient        := "nabla" "_" identifier ("(" expression ")")?
derivative      := "partial" "(" expression "," identifier ("," integer)? ")"
indexed_symbol  := identifier index_suffix*
index_suffix    := ("_" | "^") (identifier | "{" identifier "}")
```

## Examples

```text
nabla_x cross nabla_p = hbar^2/(2*pi)
[x_i,p_j] = i*hbar*delta_ij*I
delta^i_j*x^j = x^i
{x_i,p_j} = delta_ij
partial(x^3,x,2)
nabla_x(x^2)
```

`i` and `pi` are parsed as dimensionless constants. Other identifiers are symbols.

## Index rules

- `_i` is covariant.
- `^i` is contravariant.
- compact unbraced indices are split into characters: `delta_ij` becomes `_i`, `_j`;
- braces preserve a multi-character name: `T^{mu}_{nu}` becomes `^mu`, `_nu`;
- numeric superscripts are powers, not indices: `hbar^2` becomes a `Power` node.

## Explicitness requirements

Multiplication must be explicit:

```text
2*pi       valid
2 pi       EXPLICIT_MULTIPLICATION_REQUIRED
```

Division is lowered to multiplication by an integer power of `-1`. Subtraction is lowered to addition of a factor `-1`.

## Error model

Representative codes include:

```text
EMPTY_EXPRESSION
UNEXPECTED_CHARACTER
UNEXPECTED_TOKEN
EXPECTED_EXPRESSION
EXPLICIT_MULTIPLICATION_REQUIRED
MULTIPLE_RELATIONS
NONINTEGER_EXPONENT
EXPECTED_INDEX
EXPECTED_GRADIENT_SPACE
EXPECTED_DERIVATIVE_CALL
INVALID_DERIVATIVE_ORDER
```

The parser rejects malformed or unsupported input instead of silently choosing an interpretation.

## Deliberate exclusions

v0.6 does not support:

- arbitrary LaTeX commands or macros;
- implicit multiplication;
- function application other than `nabla` and `partial` forms;
- fractional or symbolic exponents;
- matrix literals;
- integrals, limits, summation binders, or distributions;
- automatic interpretation of prose;
- semantic proof of the parsed expression.

These exclusions keep the text layer deterministic and protect all downstream dimension, tensor, and symbolic analyses.
