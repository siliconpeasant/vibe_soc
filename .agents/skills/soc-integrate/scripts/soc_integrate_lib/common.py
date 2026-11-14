"""Text, dimensions, constants and file I/O."""
import ast
import json
import operator
import re
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path

UNSUPPORTED_PREFIX = re.compile('^(?:unsupported\\s+)+')
BASED_INTEGER = re.compile("(\\d+)?'[sS]?([bBoOdDhH])([0-9a-fA-F_]+)")
DIMENSION = re.compile('\\[([^\\]]+)\\]')
BOUND_SEPARATOR = re.compile('(?<!:):(?!:)')
QUOTED_STRING = re.compile('"(?:\\\\.|[^"\\\\])*"')
NEWLINE = re.compile('\n')


IDENT = r'[A-Za-z_][\w$]*'
COMMENTS = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.S)
NON_NEWLINE = re.compile(r'[^\n]')
INSTANCE_OPEN = re.compile(r'\s*(' + IDENT + r')\s*\(')
INTERFACE_OPEN = re.compile(r'\s*(' + IDENT + r')\s*((?:\[[^\]]+\]\s*)*)\(')
INSTANCE_ARRAY = re.compile(r'\s*' + IDENT + r'\s*\[')
SEMICOLON = re.compile(r'\s*;')


@lru_cache(maxsize=8)
def line_offsets(text):
    return tuple(m.start() for m in NEWLINE.finditer(text))


def line_number(text, pos):
    return bisect_right(line_offsets(text), pos - 1) + 1


def uncomment(text):
    """Mask comments, preserving offsets/newlines and quoted strings."""
    return COMMENTS.sub(lambda m: m[0] if m[0].startswith('"') else
                        NON_NEWLINE.sub(' ', m[0]), text)


def fail(file, text, pos, construct):
    construct = UNSUPPORTED_PREFIX.sub('', construct)
    raise ValueError(f'{file}:{line_number(text, pos)}: unsupported {construct}')


def balanced(text, pos, file='<text>'):
    """Return contents and end offset of a balanced (), [] or {} group."""
    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = [pairs[text[pos]]]
    start = pos + 1
    pos += 1
    quoted = False
    while pos < len(text):
        char = text[pos]
        if char == '"' and (pos == 0 or text[pos - 1] != '\\'):
            quoted = not quoted
        if not quoted:
            if char in pairs:
                stack.append(pairs[char])
            elif char in ')]}':
                if char != stack.pop():
                    fail(file, text, pos, 'unbalanced delimiters')
                if not stack:
                    return text[start:pos], pos + 1
        pos += 1
    fail(file, text, start - 1, 'unterminated delimiter')


def split_port_items(text, separator=','):
    clean = uncomment(text)
    items, start, pos = [], 0, 0
    while pos < len(text):
        if clean[pos] in '([{':
            _, pos = balanced(clean, pos)
            continue
        if clean[pos] == '"':
            match = QUOTED_STRING.match(clean[pos:])
            if match:
                pos += match.end()
                continue
        if clean[pos] == separator:
            items.append(text[start:pos])
            start = pos + 1
        pos += 1
    if clean[start:].strip():
        items.append(text[start:])
    return items


def constant(expr, values=None):
    return constant_cached(expr, tuple(sorted((values or {}).items())))


@lru_cache(maxsize=8192)
def constant_cached(expr, assignments):
    """Evaluate a deliberately small integer expression grammar, without eval."""
    values = dict(assignments)
    expr = expr.replace('$clog2', 'clog2')
    expr = BASED_INTEGER.sub(lambda m: str(int(m[3].replace('_', ''), {'b': 2, 'o': 8, 'd': 10, 'h': 16}[m[2].lower()])), expr)
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.FloorDiv: operator.floordiv, ast.Div: operator.floordiv,
           ast.Mod: operator.mod, ast.LShift: operator.lshift, ast.RShift: operator.rshift,
           ast.BitOr: operator.or_, ast.BitAnd: operator.and_, ast.BitXor: operator.xor}

    def walk(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'clog2' and len(node.args) == 1:
            value = walk(node.args[0])
            return (value - 1).bit_length() if value > 0 else 0
        if isinstance(node, ast.Name) and node.id in values:
            return int(values[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, (ast.LShift, ast.RShift)) and not 0 <= right <= 4096:
                raise ValueError('shift out of range')
            return ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Invert)):
            return {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Invert: operator.invert}[type(node.op)](walk(node.operand))
        raise ValueError('symbolic expression')
    try:
        return walk(ast.parse(expr.strip(), mode='eval').body)
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError, OverflowError):
        return None


def resolve_param_width(width, params=()):
    return resolved_width(width, tuple(tuple(p) for p in params))


@lru_cache(maxsize=8192)
def resolved_width(width, params):
    values = {}
    for name, default, _ in params:
        value = constant(default, values)
        if value is not None:
            values[name] = value

    def dimension(match):
        parts = BOUND_SEPARATOR.split(match[1])
        output = []
        for part in parts:
            value = constant(part, values)
            output.append(str(value) if value is not None else part.strip())
        return '[' + ':'.join(output) + ']'
    return DIMENSION.sub(dimension, width)


@lru_cache(maxsize=8192)
def bit_width(width, unpacked=''):
    """Count packed bits and unpacked elements; only unpacked arrays allow [N]."""
    result = 1
    for dimensions, is_unpacked in ((width, False), (unpacked, True)):
        for dim in DIMENSION.findall(dimensions):
            bounds = [constant(part) for part in BOUND_SEPARATOR.split(dim)]
            if None in bounds:
                return None
            if len(bounds) == 2:
                result *= abs(bounds[0] - bounds[1]) + 1
            elif is_unpacked and len(bounds) == 1 and bounds[0] > 0:
                result *= bounds[0]
            else:
                return None
    return result


def write_text(file, text):
    Path(file).write_text(text.rstrip('\n') + '\n', encoding='utf-8')


def write_json(file, data):
    write_text(file, json.dumps(data, indent=2, ensure_ascii=False))


def read_json_object(file, kind, hint=''):
    message = f'{file}: not a valid {kind} JSON (expected a JSON object)'
    if hint:
        message += '; ' + hint
    try:
        data = json.loads(Path(file).read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError(message) from None
    if not isinstance(data, dict):
        raise ValueError(message)
    return data
