"""Bounded exact arithmetic for numeric answers containing the imaginary unit."""
from fractions import Fraction
import re

NUMBER = re.compile(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')
UNIT = re.compile(r'(?<![A-Za-z_])[ij](?![A-Za-z_])', re.IGNORECASE)


def has_imaginary_unit(text):
    return len(str(text)) <= 256 and UNIT.search(str(text)) is not None


def parse_rational_complex(text):
    """Return a pair of Fractions, or None; never evaluate Python expressions.

    Only decimal/rational constants, i/j, parentheses and + - * / are accepted.
    Input length, token count, nesting, decimal exponent and rational bit sizes
    are limited before expensive arithmetic. Implicit products allow 2i and
    (-1/2)i, without accepting adjacent bare numbers or arbitrary identifiers.
    """
    text = str(text).replace('−', '-').lower()
    if not text or len(text) > 256:
        return None
    tokens = []
    pos = 0
    try:
        while pos < len(text):
            char = text[pos]
            if char.isspace():
                pos += 1
                continue
            match = NUMBER.match(text, pos)
            if match:
                value = match.group()
                mantissa, _, exponent = value.partition('e')
                if sum(c.isdigit() for c in mantissa) > 24 or (exponent and abs(int(exponent)) > 12):
                    return None
                tokens.append(Fraction(value))
                pos = match.end()
            elif char in '+-*/()ij':
                if char in 'ij' and pos + 1 < len(text) and text[pos + 1].isalpha():
                    return None
                tokens.append('i' if char == 'j' else char)
                pos += 1
            else:
                return None
            if len(tokens) > 64:
                return None
        index = 0

        def bounded(value):
            if any(abs(x.numerator).bit_length() > 320 or x.denominator.bit_length() > 320 for x in value):
                raise ValueError('Rational answer too large')
            return value

        def factor(depth):
            nonlocal index
            if depth > 16 or index >= len(tokens):
                raise ValueError('Missing or deeply nested operand')
            token = tokens[index]
            index += 1
            if isinstance(token, Fraction):
                return token, Fraction(0)
            if token == 'i':
                return Fraction(0), Fraction(1)
            if token in ('+', '-'):
                value = factor(depth + 1)
                return value if token == '+' else (-value[0], -value[1])
            if token == '(':
                value = expression(depth + 1)
                if index >= len(tokens) or tokens[index] != ')':
                    raise ValueError('Unclosed parenthesis')
                index += 1
                return value
            raise ValueError('Unsupported operand')

        def term(depth):
            nonlocal index
            value = factor(depth)
            while index < len(tokens):
                token = tokens[index]
                previous = tokens[index - 1]
                implicit = ((token == 'i' and (isinstance(previous, Fraction) or previous == ')'))
                            or (token == '(' and (isinstance(previous, Fraction) or previous in ('i', ')'))))
                if token not in ('*', '/') and not implicit:
                    break
                if not implicit:
                    index += 1
                other = factor(depth)
                a, b = value
                c, d = other
                if token == '/':
                    divisor = c*c + d*d
                    value = ((a*c + b*d)/divisor, (b*c - a*d)/divisor)
                else:
                    value = (a*c - b*d, a*d + b*c)
                value = bounded(value)
            return value

        def expression(depth):
            nonlocal index
            value = term(depth)
            while index < len(tokens) and tokens[index] in ('+', '-'):
                sign = 1 if tokens[index] == '+' else -1
                index += 1
                other = term(depth)
                value = bounded((value[0] + sign*other[0], value[1] + sign*other[1]))
            return value

        value = expression(0)
        return value if index == len(tokens) else None
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
