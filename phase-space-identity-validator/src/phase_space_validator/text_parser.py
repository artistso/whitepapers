"""Controlled text parser for phase-space expressions.

The parser intentionally accepts a bounded, explicit notation. It converts text
into the existing strict expression AST without guessing ambiguous syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .expressions import (
    Commutator,
    Constant,
    CrossProduct,
    Derivative,
    Equality,
    Expression,
    Gradient,
    PoissonBracket,
    Power,
    Product,
    Sum,
    Symbol,
    TensorProduct,
    WedgeProduct,
)


class TokenKind(StrEnum):
    IDENTIFIER = "identifier"
    NUMBER = "number"
    PUNCTUATION = "punctuation"
    END = "end"


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
    offset: int
    line: int
    column: int


class TextParseError(ValueError):
    """Position-aware failure produced by text tokenization or parsing."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        offset: int,
        line: int,
        column: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.offset = offset
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"{self.code} at line {self.line}, column {self.column}: {self.message}"

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "offset": self.offset,
            "line": self.line,
            "column": self.column,
        }


_RELATIONS = {"=", "≈", "≡"}
_VECTOR_OPERATORS = {"cross", "wedge", "tensor"}
_CONSTANT_NAMES = {"i", "pi"}
_PUNCTUATION = set("+-*/^_()[]{},=≈≡")


def tokenize_text(text: str) -> tuple[Token, ...]:
    """Tokenize controlled mathematical text with source positions."""

    tokens: list[Token] = []
    offset = 0
    line = 1
    column = 1

    while offset < len(text):
        char = text[offset]
        if char.isspace():
            if char == "\n":
                line += 1
                column = 1
            else:
                column += 1
            offset += 1
            continue

        start = offset
        start_line = line
        start_column = column

        if char.isalpha():
            offset += 1
            column += 1
            while offset < len(text) and text[offset].isalnum():
                offset += 1
                column += 1
            tokens.append(
                Token(
                    TokenKind.IDENTIFIER,
                    text[start:offset],
                    start,
                    start_line,
                    start_column,
                )
            )
            continue

        if char.isdigit() or (char == "." and offset + 1 < len(text) and text[offset + 1].isdigit()):
            seen_dot = char == "."
            offset += 1
            column += 1
            while offset < len(text):
                current = text[offset]
                if current.isdigit():
                    offset += 1
                    column += 1
                    continue
                if current == "." and not seen_dot:
                    seen_dot = True
                    offset += 1
                    column += 1
                    continue
                break
            tokens.append(
                Token(TokenKind.NUMBER, text[start:offset], start, start_line, start_column)
            )
            continue

        if char in _PUNCTUATION:
            tokens.append(Token(TokenKind.PUNCTUATION, char, start, start_line, start_column))
            offset += 1
            column += 1
            continue

        raise TextParseError(
            "UNEXPECTED_CHARACTER",
            f"unsupported character {char!r}",
            offset=start,
            line=start_line,
            column=start_column,
        )

    tokens.append(Token(TokenKind.END, "", len(text), line, column))
    return tuple(tokens)


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.tokens = tokenize_text(text)
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def advance(self) -> Token:
        token = self.current
        if token.kind is not TokenKind.END:
            self.position += 1
        return token

    def match(self, value: str) -> bool:
        if self.current.value == value:
            self.advance()
            return True
        return False

    def expect(self, value: str, message: str | None = None) -> Token:
        if self.current.value != value:
            self.fail(
                "UNEXPECTED_TOKEN",
                message or f"expected {value!r}, found {self.current.value!r}",
            )
        return self.advance()

    def fail(self, code: str, message: str, token: Token | None = None) -> None:
        target = token or self.current
        raise TextParseError(
            code,
            message,
            offset=target.offset,
            line=target.line,
            column=target.column,
        )

    def parse(self) -> Expression:
        if self.current.kind is TokenKind.END:
            self.fail("EMPTY_EXPRESSION", "expression must not be empty")
        expression = self.parse_equality()
        if self.current.kind is not TokenKind.END:
            if self._starts_primary(self.current):
                self.fail(
                    "EXPLICIT_MULTIPLICATION_REQUIRED",
                    "adjacent expressions require an explicit '*' operator",
                )
            self.fail("UNEXPECTED_TOKEN", f"unexpected token {self.current.value!r}")
        return expression

    def parse_equality(self) -> Expression:
        left = self.parse_sum()
        if self.current.value not in _RELATIONS:
            return left
        relation = self.advance().value
        right = self.parse_sum()
        if self.current.value in _RELATIONS:
            self.fail("MULTIPLE_RELATIONS", "only one equality relation is supported")
        return Equality(left=left, right=right, relation=relation)

    def parse_sum(self) -> Expression:
        terms = [self.parse_vector_product()]
        while self.current.value in {"+", "-"}:
            operator = self.advance().value
            term = self.parse_vector_product()
            if operator == "-":
                term = _make_product((Constant(-1), term))
            terms.append(term)
        return _make_sum(tuple(terms))

    def parse_vector_product(self) -> Expression:
        expression = self.parse_product()
        while self.current.kind is TokenKind.IDENTIFIER and self.current.value in _VECTOR_OPERATORS:
            operator = self.advance().value
            right = self.parse_product()
            if operator == "cross":
                expression = CrossProduct(expression, right)
            elif operator == "wedge":
                expression = WedgeProduct(expression, right)
            else:
                expression = TensorProduct(expression, right)
        return expression

    def parse_product(self) -> Expression:
        factors = [self.parse_unary()]
        while self.current.value in {"*", "/"}:
            operator = self.advance().value
            factor = self.parse_unary()
            if operator == "/":
                factor = Power(factor, -1)
            factors.append(factor)
        return _make_product(tuple(factors))

    def parse_unary(self) -> Expression:
        if self.match("+"):
            return self.parse_unary()
        if self.match("-"):
            return _make_product((Constant(-1), self.parse_unary()))
        return self.parse_power()

    def parse_power(self) -> Expression:
        expression = self.parse_primary()
        while self.current.value == "^" and self._power_follows():
            self.advance()
            sign = -1 if self.match("-") else 1
            token = self.current
            if token.kind is not TokenKind.NUMBER or "." in token.value:
                self.fail("NONINTEGER_EXPONENT", "power exponent must be an integer", token)
            self.advance()
            expression = Power(expression, sign * int(token.value))
        return expression

    def parse_primary(self) -> Expression:
        token = self.current
        if token.kind is TokenKind.NUMBER:
            self.advance()
            value: int | float
            value = float(token.value) if "." in token.value else int(token.value)
            return Constant(value)

        if token.kind is TokenKind.IDENTIFIER:
            self.advance()
            if token.value == "nabla":
                return self.parse_gradient(token)
            if token.value == "partial":
                return self.parse_derivative(token)
            if token.value in _VECTOR_OPERATORS:
                self.fail("EXPECTED_EXPRESSION", f"operator {token.value!r} lacks a left operand", token)
            if token.value in _CONSTANT_NAMES:
                return Constant(token.value)
            return self.parse_symbol(token.value)

        if self.match("("):
            expression = self.parse_equality()
            self.expect(")", "expected ')' to close parenthesized expression")
            return expression

        if self.match("["):
            left = self.parse_equality()
            self.expect(",", "commutator requires two comma-separated operands")
            right = self.parse_equality()
            self.expect("]", "expected ']' to close commutator")
            return Commutator(left, right)

        if self.match("{"):
            left = self.parse_equality()
            self.expect(",", "Poisson bracket requires two comma-separated operands")
            right = self.parse_equality()
            self.expect("}", "expected '}' to close Poisson bracket")
            return PoissonBracket(left, right)

        self.fail("EXPECTED_EXPRESSION", f"expected an expression, found {token.value!r}", token)

    def parse_gradient(self, token: Token) -> Gradient:
        if not self.match("_"):
            self.fail("EXPECTED_GRADIENT_SPACE", "'nabla' must be followed by '_<space>'", token)
        space = self.parse_index_name(preserve_compact=True)
        operand: Expression | None = None
        if self.match("("):
            operand = self.parse_equality()
            self.expect(")", "expected ')' to close gradient operand")
        return Gradient(space=space, operand=operand)

    def parse_derivative(self, token: Token) -> Derivative:
        if not self.match("("):
            self.fail(
                "EXPECTED_DERIVATIVE_CALL",
                "partial derivatives use partial(expression, variable[, order])",
                token,
            )
        operand = self.parse_equality()
        self.expect(",", "partial derivative requires a variable argument")
        variable_token = self.current
        if variable_token.kind is not TokenKind.IDENTIFIER:
            self.fail("EXPECTED_VARIABLE", "derivative variable must be an identifier")
        variable = self.advance().value
        order = 1
        if self.match(","):
            order_token = self.current
            if order_token.kind is not TokenKind.NUMBER or "." in order_token.value:
                self.fail("INVALID_DERIVATIVE_ORDER", "derivative order must be an integer")
            order = int(self.advance().value)
            if order < 1:
                self.fail(
                    "INVALID_DERIVATIVE_ORDER",
                    "derivative order must be positive",
                    order_token,
                )
        self.expect(")", "expected ')' to close partial derivative")
        return Derivative(variable=variable, operand=operand, order=order)

    def parse_symbol(self, name: str) -> Symbol:
        indices: list[str] = []
        while self.current.value in {"_", "^"} and not self._power_follows():
            variance = self.advance().value
            names = self.parse_index_names()
            indices.extend(f"{variance}{index}" for index in names)
        return Symbol(name=name, indices=tuple(indices))

    def parse_index_names(self) -> tuple[str, ...]:
        if self.match("{"):
            name = self.parse_index_name(preserve_compact=True)
            self.expect("}", "expected '}' to close index name")
            return (name,)
        compact = self.parse_index_name(preserve_compact=False)
        return tuple(compact) if len(compact) > 1 else (compact,)

    def parse_index_name(self, *, preserve_compact: bool) -> str:
        token = self.current
        if token.kind is not TokenKind.IDENTIFIER:
            self.fail("EXPECTED_INDEX", "index or coordinate-space name must be an identifier", token)
        self.advance()
        if not preserve_compact and not token.value.isalpha():
            self.fail("INVALID_INDEX", "unbraced compact indices must contain letters only", token)
        return token.value

    def _power_follows(self) -> bool:
        if self.current.value != "^":
            return False
        next_position = self.position + 1
        if next_position >= len(self.tokens):
            return False
        next_token = self.tokens[next_position]
        if next_token.value == "-":
            next_position += 1
            if next_position >= len(self.tokens):
                return False
            next_token = self.tokens[next_position]
        return next_token.kind is TokenKind.NUMBER

    @staticmethod
    def _starts_primary(token: Token) -> bool:
        return token.kind in {TokenKind.IDENTIFIER, TokenKind.NUMBER} or token.value in {"(", "[", "{"}


def parse_text_expression(text: str) -> Expression:
    """Parse one controlled mathematical expression into the strict AST."""

    return _Parser(text).parse()


def load_text_expression(path: Path) -> Expression:
    """Load and parse a UTF-8 controlled-expression text file."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TextParseError(
            "FILE_READ_ERROR",
            str(exc),
            offset=0,
            line=1,
            column=1,
        ) from exc
    return parse_text_expression(text)


def _make_product(factors: tuple[Expression, ...]) -> Expression:
    flattened: list[Expression] = []
    for factor in factors:
        if isinstance(factor, Product):
            flattened.extend(factor.factors)
        else:
            flattened.append(factor)
    if len(flattened) == 1:
        return flattened[0]
    return Product(tuple(flattened))


def _make_sum(terms: tuple[Expression, ...]) -> Expression:
    flattened: list[Expression] = []
    for term in terms:
        if isinstance(term, Sum):
            flattened.extend(term.terms)
        else:
            flattened.append(term)
    if len(flattened) == 1:
        return flattened[0]
    return Sum(tuple(flattened))
