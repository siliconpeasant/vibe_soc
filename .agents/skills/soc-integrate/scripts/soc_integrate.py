#!/usr/bin/env python3
"""Small, conservative RTL interface parser and SoC connection generator (stdlib only).

This is an interface parser, not an elaborator. Balanced lists are parsed rather
than split with regular expressions; unsupported interface syntax is an error.
"""
import argparse
import copy
import ast
import csv
import json
import operator
import re
import sys
import shutil
import shlex
import subprocess
import tempfile
import os
from bisect import bisect_right
from functools import lru_cache
import xml.etree.ElementTree as ET
from pathlib import Path


IDENT = r'[A-Za-z_][\w$]*'
COMMENTS = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.S)
NON_NEWLINE = re.compile(r'[^\n]')
INSTANCE_OPEN = re.compile(r'\s*(' + IDENT + r')\s*\(')
INTERFACE_OPEN = re.compile(r'\s*(' + IDENT + r')\s*((?:\[[^\]]+\]\s*)*)\(')
INSTANCE_ARRAY = re.compile(r'\s*' + IDENT + r'\s*\[')
SEMICOLON = re.compile(r'\s*;')


@lru_cache(maxsize=8)
def line_offsets(text):
    return tuple(m.start() for m in re.finditer('\n', text))


def line_number(text, pos):
    return bisect_right(line_offsets(text), pos - 1) + 1


def uncomment(text):
    """Mask comments, preserving offsets/newlines and quoted strings."""
    return COMMENTS.sub(lambda m: m[0] if m[0].startswith('"') else
                        NON_NEWLINE.sub(' ', m[0]), text)


def fail(file, text, pos, construct):
    construct = re.sub(r'^(?:unsupported\s+)+', '', construct)
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
            match = re.match(r'"(?:\\.|[^"\\])*"', clean[pos:])
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


class Preprocessor:
    def __init__(self, include_dirs=(), defines=()):
        self.dirs = [Path(p) for p in include_dirs]
        self.macros = {}
        for define in defines:
            name, sep, value = define.partition('=')
            self.macros[name] = value if sep else '1'
        self.active_files = []
        self.locations = []
        self.functions = set()

    def read(self, file):
        file = Path(file).resolve()
        if file in self.active_files:
            raise ValueError(f'{file}:1: recursive include')
        self.active_files.append(file)
        result, stack, active = [], [], True
        text = uncomment(file.read_text(encoding='utf-8'))
        skip_define = False
        for number, line in enumerate(text.splitlines(keepends=True), 1):
            if skip_define:
                skip_define = line.rstrip().endswith('\\')
                result.append('\n')
                self.locations.append((str(file), number))
                continue
            directive = re.match(r'\s*`(include|define|undef|ifdef|ifndef|elsif|else|endif)\b(.*)', line)
            if directive:
                kind, arg = directive.groups()
                arg = arg.strip()
                if kind in ('ifdef', 'ifndef'):
                    cond = arg in self.macros
                    if kind == 'ifndef':
                        cond = not cond
                    stack.append([active, cond, False])
                    active = active and cond
                elif kind in ('elsif', 'else', 'endif'):
                    if not stack:
                        raise ValueError(f'{file}:{number}: unmatched `{kind}')
                    parent, taken, seen_else = stack[-1]
                    if seen_else and kind != 'endif':
                        raise ValueError(f'{file}:{number}: `{kind} after `else')
                    if kind == 'endif':
                        active = parent
                        stack.pop()
                    else:
                        cond = kind == 'else' or arg in self.macros
                        active = parent and not taken and cond
                        stack[-1] = [parent, taken or cond, kind == 'else']
                elif active and kind == 'define':
                    match = re.fullmatch(r'(' + IDENT + r')(?:\s+(.*))?', arg)
                    if re.match(IDENT + r'\(', arg):
                        name = re.match(IDENT, arg)[0]
                        self.functions.add(name)
                        skip_define = line.rstrip().endswith('\\')
                        self.macros[name] = ''
                        result.append('\n')
                        self.locations.append((str(file), number))
                        continue
                    if not match:
                        raise ValueError(f'{file}:{number}: malformed macro define: {arg}')
                    self.functions.discard(match[1])
                    self.macros[match[1]] = match[2] or ''
                elif active and kind == 'undef':
                    self.macros.pop(arg, None)
                    self.functions.discard(arg)
                elif active and kind == 'include':
                    match = re.fullmatch(r'"([^"]+)"', arg)
                    if not match:
                        raise ValueError(f'{file}:{number}: unsupported include: {arg}')
                    path = next((d / match[1] for d in [file.parent] + self.dirs
                                 if (d / match[1]).is_file()), None)
                    if path is None:
                        raise ValueError(f'{file}:{number}: missing include "{match[1]}"')
                    result.append(self.read(path))
                    continue
                result.append('\n')
            elif active:
                # Non-semantic standard directives need not affect port extraction.
                if re.match(r'\s*`(?:timescale|default_nettype|celldefine|endcelldefine)\b', line):
                    result.append('\n')
                else:
                    for name in re.findall(r'`(' + IDENT + r')\s*\(', line):
                        if name not in self.macros:
                            self.functions.add(name)
                    for _ in range(32):
                        names = [n for n in re.findall(r'`(' + IDENT + ')', line) if n not in self.functions]
                        if not names:
                            break
                        for name in names:
                            if name not in self.macros:
                                raise ValueError(f'{file}:{number}: undefined macro `{name}')
                        line = re.sub(r'`(' + IDENT + ')', lambda m: m[0] if m[1] in self.functions else self.macros[m[1]], line)
                    else:
                        raise ValueError(f'{file}:{number}: recursive macro expansion')
                    result.append(line if line.endswith('\n') else line + '\n')
            else:
                result.append('\n')
            self.locations.append((str(file), number))
        if stack:
            raise ValueError(f'{file}:{len(text.splitlines())}: unterminated `ifdef')
        self.active_files.pop()
        return ''.join(result)


def parameter_value(value):
    """Convert JSON overrides to HDL, checking bool before int (a Python subtype)."""
    if isinstance(value, bool):
        return "1'b1" if value else "1'b0"
    if isinstance(value, (int, str)):
        return str(value)
    raise ValueError(f'parameter value must be int, str or bool, got {type(value).__name__}')


def constant(expr, values=None):
    return constant_cached(expr, tuple(sorted((values or {}).items())))


@lru_cache(maxsize=8192)
def constant_cached(expr, assignments):
    """Evaluate a deliberately small integer expression grammar, without eval."""
    values = dict(assignments)
    expr = parameter_value(expr).replace('$clog2', 'clog2')
    expr = re.sub(r"(\d+)?'[sS]?([bBoOdDhH])([0-9a-fA-F_]+)",
                  lambda m: str(int(m[3].replace('_', ''), {'b': 2, 'o': 8, 'd': 10, 'h': 16}[m[2].lower()])), expr)
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
        parts = re.split(r'(?<!:):(?!:)', match[1])
        output = []
        for part in parts:
            value = constant(part, values)
            output.append(str(value) if value is not None else part.strip())
        return '[' + ':'.join(output) + ']'
    return re.sub(r'\[([^\]]+)\]', dimension, width)


@lru_cache(maxsize=8192)
def bit_width(width, unpacked=''):
    """Count packed bits and unpacked elements; only unpacked arrays allow [N]."""
    result = 1
    for dimensions, is_unpacked in ((width, False), (unpacked, True)):
        for dim in re.findall(r'\[([^\]]+)\]', dimensions):
            bounds = [constant(part) for part in re.split(r'(?<!:):(?!:)', dim)]
            if None in bounds:
                return None
            if len(bounds) == 2:
                result *= abs(bounds[0] - bounds[1]) + 1
            elif is_unpacked and len(bounds) == 1 and bounds[0] > 0:
                result *= bounds[0]
            else:
                return None
    return result


class VerilogModule:
    def __init__(self, name=''):
        self.name = name
        self.params = []             # Public parameters, backward-compatible tuples
        self.localparams = []
        self.ports = []              # Backward-compatible (direction, packed width, name)
        self.details = {}            # Type text, unpacked dimensions and source location
        self.file = ''
        self.imports = ''
        self.param_dims = {}
        self.kind = 'module'
        self.interfaces = {}
        self.modports = {}

    def metadata(self):
        return {'module_name': self.name, 'file': self.file, 'kind': self.kind,
                'interfaces': self.interfaces,
                'modports': self.modports,
                'params': self.params, 'localparams': self.localparams,
                'imports': self.imports, 'param_dims': self.param_dims,
                'ports': [dict(direction=d, width=w, name=n, **self.details.get(n, {}))
                          for d, w, n in self.ports]}


def parse_parameters(section, module, local=False):
    inherited = ''
    for item in split_port_items(section):
        kind = re.match(r'\s*(parameter|localparam)\b', item)
        if kind:
            local = kind[1] == 'localparam'
        item = re.sub(r'^\s*(?:parameter|localparam)\b\s*', '', item).strip()
        match = re.fullmatch(r'(.*?)\b(' + IDENT + r')\s*((?:\[[^\]]+\]\s*)*)=\s*(.+)', item, re.S)
        if not match:
            raise ValueError(f'unsupported parameter declaration: {item}')
        type_text, name, dims, value = match.groups()
        module.param_dims[name] = dims.strip()
        inherited = type_text.strip() or inherited
        if any(p[0] == name for p in module.params + module.localparams):
            raise ValueError(f'duplicate parameter: {name}')
        if re.search(r'\btype\b', inherited):
            raise ValueError(f'unsupported type parameter: {item}')
        (module.localparams if local else module.params).append((name, value.strip(), inherited))


def parse_port(item, inherited=None):
    item = item.strip()
    direction = re.match(r'(input|output|inout)\b\s*', item)
    if direction:
        kind = direction[1]
        rest = item[direction.end():]
    elif inherited and re.fullmatch(IDENT + r'\s*(?:\[[^\]]+\]\s*)*', item):
        kind, type_text, width = inherited
        rest = item
        match = re.fullmatch(r'(' + IDENT + r')\s*((?:\[[^\]]+\]\s*)*)', rest)
        return (kind, width, match[1]), {'type': type_text, 'unpacked': match[2].strip()}, inherited
    else:
        kind, rest = 'interface', item
    match = re.fullmatch(r'(.*?)\b(' + IDENT + r')\s*((?:\[[^\]]+\]\s*)*)', rest, re.S)
    if not match:
        raise ValueError(f'unsupported port declaration: {item}')
    prefix, name, unpacked = match.groups()
    width = resolve_param_width(''.join(re.findall(r'\[[^\]]+\]', prefix)))
    type_text = re.sub(r'\[[^\]]+\]', '', prefix).strip()
    if kind == 'interface' and ('::' in type_text or type_text.endswith('_t')):
        kind = 'input'  # Implicit direction on a clearly identified value type.
    if kind == 'interface':
        if not re.fullmatch(IDENT + r'(?:\.' + IDENT + ')?', type_text):
            raise ValueError(f'unsupported interface port: {item}')
    elif type_text and not re.fullmatch(
            r'(?:(?:wire|reg|logic|var)\s*)?(?:(?:signed|unsigned)\s*)?|' +
            r'(?:(?:wire|var)\s+)?' + IDENT + r'(?:::' + IDENT + r')*(?:\s+(?:signed|unsigned))?', type_text):
        raise ValueError(f'unsupported port type: {item}')
    detail = {'type': type_text, 'unpacked': resolve_param_width(unpacked.strip())}
    return (kind, width, name), detail, (kind, type_text, width)


def check_header_macros(section, file, text, start):
    scan = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: ' ' * len(m[0]), section)
    macro = re.search(r'`(' + IDENT + ')', scan)
    if macro:
        if re.match(r'\s*\(', scan[macro.end():]):
            construct = f'function-like macro `{macro[1]} in port/parameter header; install verilator'
        else:
            construct = f'undefined macro `{macro[1]} in port/parameter header; supply -D or an include'
        fail(file, text, start + macro.start(), construct)


def parse_module(name, content, file='<text>'):
    module = VerilogModule(name)
    module.file = str(file)
    text = uncomment(content)
    match = re.match(r'\s*(module|interface)\s+' + re.escape(name) + r'\b\s*', text)
    if not match:
        fail(file, text, 0, 'module header')
    module.kind = match[1]
    pos = match.end()
    try:
        import_start = pos
        while re.match(r'import\b', text[pos:]):
            pos = text.index(';', pos) + 1
            while text[pos].isspace():
                pos += 1
        module.imports = text[import_start:pos].strip()
        if text[pos:pos + 1] == '#':
            pos += 1
            while text[pos].isspace():
                pos += 1
            section, pos = balanced(text, pos, file)
            check_header_macros(section, file, text, pos - len(section) - 1)
            parse_parameters(section, module)
        while text[pos].isspace():
            pos += 1
        if text[pos] == ';':
            section = ''
        elif text[pos] == '(':
            header_start = pos + 1
            module.port_prefix = text[:header_start]
            section, pos = balanced(text, pos, file)
            check_header_macros(section, file, text, header_start)
        else:
            fail(file, text, pos, 'module port list')
        while text[pos].isspace():
            pos += 1
        if text[pos] != ';':
            fail(file, text, pos, 'module header terminator')
        module.header = text[:pos + 1]
        body = text[pos + 1:]
        if module.kind == 'interface':
            for decl in re.finditer(r'\bmodport\s+([^;]+);', body):
                for item in split_port_items(decl[1]):
                    modport = re.fullmatch(r'\s*(' + IDENT + r')\s*\((.*)\)\s*', item, re.S)
                    if modport:
                        module.modports[modport[1]] = sorted(set(re.findall(r'\b(input|output|inout)\b', modport[2])))
        for param in re.finditer(r'\b(parameter|localparam)\s+([^;]+);', body):
            parse_parameters(param[2], module, param[1] == 'localparam')
        items = split_port_items(section)
        non_ansi = bool(items) and all(re.fullmatch(IDENT, p.strip()) for p in items)
        inherited = None
        if non_ansi:
            declared = {}
            for decl in re.finditer(r'\b(input|output|inout)\b([^;]*);', body):
                inherited = None
                for item in split_port_items(decl[0][:-1]):
                    port, detail, inherited = parse_port(item, inherited)
                    if port[2] in declared:
                        raise ValueError(f'duplicate port declaration: {port[2]}')
                    name_match = re.search(r'\b' + re.escape(port[2]) + r'\b(?=\s*(?:\[|$))', item)
                    detail['line'] = line_number(text, pos + 1 + decl.start() + decl[0].find(item) + name_match.start())
                    declared[port[2]] = (port, detail)
            for item in items:
                name = item.strip()
                if name not in declared:
                    raise ValueError(f'non-ANSI port without direction declaration: {name}')
                port, detail = declared.pop(name)
                # Merge later storage declarations without changing header order.
                for redecl in re.finditer(r'\b(reg|logic)\s+([^;]+);', body):
                    storage = None
                    for entry in split_port_items(redecl[0][:-1]):
                        declaration_text = 'output ' + entry if storage is None else entry
                        candidate, info, storage = parse_port(declaration_text, storage)
                        if candidate[2] == name:
                            detail['type'] = info['type']
                            detail['unpacked'] = info['unpacked'] or detail['unpacked']
                            if candidate[1]:
                                port = (port[0], candidate[1], name)
                module.ports.append(port)
                module.details[name] = detail
            if declared:
                raise ValueError('body ports absent from header: ' + ', '.join(declared))
        else:
            cursor = header_start if items else 0
            for item in items:
                pos = cursor + len(item) - len(item.lstrip())
                cursor += len(item) + 1
                port, detail, inherited = parse_port(item, inherited)
                if port[2] in module.details:
                    raise ValueError(f'duplicate port: {port[2]}')
                module.ports.append(port)
                detail['line'] = line_number(text, pos)
                module.details[port[2]] = detail
        imports = re.findall(r'\bimport\s+([^;]+);', module.imports)
        imported = [entry.strip() for group in imports for entry in group.split(',')]
        wildcards = [entry[:-3] for entry in imported if entry.endswith('::*')]
        for direction, _, name in module.ports:
            if direction == 'interface':
                continue
            detail = module.details[name]
            type_text = detail['type']
            named = re.fullmatch(r'((?:(?:wire|var)\s+)?)(' + IDENT + r')(\s+(?:signed|unsigned))?', type_text)
            if not named or not bus_like('', type_text):
                continue
            explicit = [entry for entry in imported if entry.endswith('::' + named[2])]
            qualified = explicit[0] if len(explicit) == 1 else (wildcards[0] + '::' + named[2] if len(wildcards) == 1 else None)
            if qualified:
                detail['declaration_type'] = (named[1] or '') + qualified + (named[3] or '')
        return module
    except (ValueError, IndexError) as exc:
        if re.match(r'^.*?:\d+: ', str(exc), re.S):
            raise
        fail(file, text, min(pos, len(text)), str(exc))


def bus_like(name, type_text):
    value_type = re.sub(r'\b(?:wire|var|reg|logic|bit|signed|unsigned)\b', '', type_text).strip()
    return bool(value_type and '.' not in value_type or re.search(
        r'^(?:tl_|axi_|apb_|ahb_)|_(?:req|rsp)(?:_|$)|h2d|d2h', name))


def selection_interval(expr):
    match = re.fullmatch(r'\s*' + IDENT + r'\s*\[([^\[\]]+)\]\s*', uncomment(expr))
    if not match:
        return None
    selection = match[1]
    indexed = re.fullmatch(r'(.+?)\s*([+-]):\s*(.+)', selection)
    if indexed:
        base, width = constant(indexed[1]), constant(indexed[3])
        if base is None or width is None:
            return None
        if width <= 0:
            raise ValueError(f'invalid indexed part-select width: {expr}')
        low, high = (base, base + width - 1) if indexed[2] == '+' else (base - width + 1, base)
    else:
        parts = re.split(r'(?<!:):(?!:)', selection)
        values = [constant(p) for p in parts]
        if len(values) not in (1, 2) or None in values:
            return None
        low, high = min(values), max(values)
    if low < 0:
        raise ValueError(f'negative part-select index: {expr}')
    return low, high


@lru_cache(maxsize=1)
def verilator_version():
    result = subprocess.run(['verilator', '--version'], capture_output=True, text=True, timeout=10)
    match = re.search(r'Verilator (\d+)\.(\d+)', result.stdout)
    return tuple(map(int, match.groups())) if match else (0, 0)


def ast_constants(tree, module_name, json_format):
    """Read compiler-folded probes; JSON's pre-width dtype links are incomplete.

    $bits probes also cover packed structs/unions and unpacked arrays without
    depending on unstable AST pointer fields or reproducing HDL elaboration.
    """
    if json_format:
        module = next(m for m in tree['modulesp'] if m.get('origName', m.get('name')) == module_name)
        return {v['name']: constant(v['valuep'][0]['name']) for v in module['stmtsp']
                if v.get('type') == 'VAR' and v.get('valuep') and v['valuep'][0].get('type') == 'CONST'}
    module = next(m for m in tree.findall('.//module') if m.get('origName', m.get('name')) == module_name)
    return {v.get('name'): constant(v.find('.//const').get('name', ''))
            for v in module.findall('var') if v.find('.//const') is not None}


def typedef_names(text):
    names = set()
    for typedef in re.finditer(r'\btypedef\b', uncomment(text)):
        statement = split_port_items(text[typedef.end():], ';')[0]
        match = re.search(r'\b(' + IDENT + r')\s*(?:\[[^\]]+\]\s*)*$', statement)
        if match:
            names.add(match[1])
    return names


def qualify_imports(module, prepared):
    """Find a typedef in every imported package rather than guessing the first."""
    symbols = {}
    for text, _ in prepared.values():
        for package in re.finditer(r'\bpackage\s+(' + IDENT + r')\s*;(.*?)\bendpackage\b', uncomment(text), re.S):
            symbols.setdefault(package[1], set()).update(typedef_names(package[2]))
    text, _, start, end = module.full_source
    local_types = typedef_names(text[start:end])
    module.local_port_types = set()
    imported = [e.strip() for group in re.findall(r'\bimport\s+([^;]+);', module.imports)
                for e in group.split(',')]
    wildcards = [entry[:-3] for entry in imported if entry.endswith('::*')]
    for direction, _, name in module.ports:
        detail = module.details[name]
        named = re.fullmatch(r'((?:(?:wire|var)\s+)?)(' + IDENT + r')(\s+(?:signed|unsigned))?', detail['type'])
        if direction == 'interface' or not named or not bus_like('', detail['type']):
            continue
        if named[2] in local_types:
            detail.pop('declaration_type', None)
            module.local_port_types.add(name)
            continue
        explicit = [e for e in imported if e.endswith('::' + named[2])]
        candidates = explicit or [pkg + '::' + named[2] for pkg in wildcards if named[2] in symbols.get(pkg, ())]
        if len(candidates) > 1:
            raise ValueError(f'{detail["file"]}:{detail["line"]}: {module.name}.{name}: ambiguous type {named[2]}: {", ".join(candidates)}')
        if candidates:
            detail['declaration_type'] = (named[1] or '') + candidates[0] + (named[3] or '')
        elif imported:
            # Let full elaboration handle module-body typedefs. Unresolved types
            # remain unqualified so the compiler can issue the real diagnostic.
            detail.pop('declaration_type', None)


def resolve_instance(instance):
    """Resolve one configuration without changing the shared default interface."""
    overrides = {k: parameter_value(v) for k, v in instance['parameters'].items()}
    module = instance['module']
    unknown = overrides.keys() - {p[0] for p in module.params}
    if unknown:
        raise ValueError(f'{module.file}:1: unknown parameter overrides on {instance["instance"]}: {sorted(unknown)}')
    if not overrides:
        return instance
    cache = getattr(module, '_instance_cache', {})
    key = tuple(overrides.items())
    if key not in cache:
        resolved = copy.copy(module)
        resolved.details = copy.deepcopy(module.details)
        params = [(n, overrides.get(n, v), t) for n, v, t in module.params] + module.localparams
        unresolved = False
        for direction, width, name in module.ports:
            detail = resolved.details[name]
            detail['resolved_width'] = resolve_param_width(width, params)
            detail['resolved_unpacked'] = resolve_param_width(detail.get('unpacked', ''), params)
            unresolved |= bit_width(detail['resolved_width'], detail['resolved_unpacked']) is None
            detail.pop('bits', None)
        named = any(d != 'interface' and bus_like('', resolved.details[n]['type']) for d, _, n in module.ports)
        if (unresolved or named) and shutil.which('verilator') and hasattr(module, 'elaboration'):
            try:
                resolve_types(resolved, **module.elaboration, overrides=overrides)
            except ValueError as exc:
                expressions = '; '.join(f'port {n} expression {resolved.details[n]["resolved_width"]} {resolved.details[n]["resolved_unpacked"]}'
                                        for d, _, n in module.ports if d != 'interface')
                raise ValueError(f'instance {instance["instance"]} ({module.name}), parameters {overrides}, {expressions}: {exc}') from None
        for direction, width, name in module.ports:
            if direction == 'interface':
                continue
            detail = resolved.details[name]
            for field in ('resolved_width', 'resolved_unpacked'):
                expr = detail[field]
                if (bit_width(expr) if field == 'resolved_width' else bit_width('', expr)) is None:
                    raise ValueError(f'instance {instance["instance"]}, port {name}: cannot evaluate expression {expr!r}; supply packages/dependencies and Verilator')
        cache[key] = resolved
        module._instance_cache = cache
    return dict(instance, module=cache[key], parameters=overrides)


def full_elaboration_source(module, probes):
    """Instrument disposable preprocessed source; preserve every original location."""
    text, locations, start, end = module.full_source
    insert = text.rfind('endmodule', start, end)
    offset, result = 0, []
    for line, (file, number) in zip(text.splitlines(keepends=True), locations):
        result.append(f'`line {number} {json.dumps(file)} 0\n')
        if offset <= insert < offset + len(line):
            cut = insert - offset
            line = line[:cut] + '\n' + probes + '\n' + line[cut:]
        result.append(line)
        offset += len(line)
    return ''.join(result)


def ast_ports(tree, module_name, json_format):
    if json_format:
        module = next(m for m in tree['modulesp'] if m.get('origName', m.get('name')) == module_name)
        return [(v.get('direction', '').lower(), v['name']) for v in module['stmtsp']
                if v.get('type') == 'VAR' and v.get('direction') in ('INPUT', 'OUTPUT', 'INOUT')]
    module = next(m for m in tree.findall('.//module') if m.get('origName', m.get('name')) == module_name)
    return [(v.get('dir'), v.get('name')) for v in module.findall('var') if v.get('dir') in ('input', 'output', 'inout')]


def resolve_types(module, packages, include_dirs, defines, library_dirs=(), source_files=(), overrides=None, full=False):
    """Resolve public-header probes with JSON, legacy XML, then symbolic text.

    Header failures retry the full module with dependencies. Actual module
    errors remain fatal; unsupported AST formats try the legacy schema. Scratch
    is disposable and never changes the source RTL.
    """
    full = full or bool(getattr(module, 'local_port_types', ()))
    with tempfile.TemporaryDirectory(prefix='soc-integrate-') as directory:
        root = Path(directory)
        header = root / (module.name + '.sv')
        dimension_names, bit_names = {}, {}
        # Header localparams are already in module.header. Body localparams
        # retain unpacked dimensions when reproduced in the isolated probe.
        header_params = set(re.findall(r'\b(' + IDENT + r')\s*(?:\[[^\]]+\]\s*)*=', module.header))
        localparams = ''.join(f'localparam {t} {n} {module.param_dims.get(n, "")} = {v};\n'
                              for n, v, t in module.localparams if n not in header_params)
        probes = ''
        for direction, width, name in module.ports:
            if direction == 'interface':
                continue
            bit_names[name] = f'__soc_integrate_bits_{len(bit_names)}'
            probes += f'localparam integer {bit_names[name]} = $bits({name});\n'
            for field, dims in (('resolved_width', width), ('resolved_unpacked', module.details[name].get('unpacked', ''))):
                names = []
                for expr in re.findall(r'\[([^\]]+)\]', dims):
                    pair = []
                    for bound in re.split(r'(?<!:):(?!:)', expr):
                        identifier = f'__soc_integrate_dim_{len(dimension_names)}_{len(names)}_{len(pair)}'
                        probes += f'localparam integer {identifier} = {bound};\n'
                        pair.append(identifier)
                    names.append(pair)
                dimension_names[(name, field)] = names
        source_file = getattr(module, 'source_file', module.file)
        source_line = getattr(module, 'source_line', 1)
        value_ports = []
        for d, w, n in module.ports:
            if d == 'interface':
                continue
            detail = module.details[n]
            location = f'`line {detail.get("line", source_line)} {json.dumps(detail.get("file", source_file))} 0\n'
            value_ports.append(location + declaration(d, w, n, detail))
        public_header = module.port_prefix + '\n' + ',\n'.join(value_ports) + '\n);' if hasattr(module, 'port_prefix') else module.header
        origin = f'`line {source_line} {json.dumps(source_file)} 0\n'
        header.write_text(full_elaboration_source(module, probes) if full else
                          origin + public_header + '\n' + localparams + probes + 'endmodule\n')
        formats = ['json', 'xml'] if verilator_version() >= (5, 32) else ['xml']
        for format_name in formats:
            json_format = format_name == 'json'
            command = ['verilator', '--' + format_name + '-only', '--prefix', 'Vports',
                       '--Mdir', str(root / 'obj'), '--top-module', module.name, '-Wno-fatal']
            if not json_format:
                command += ['--xml-output', str(root / 'ports.xml')]
            command += ['-I' + str(d) for d in include_dirs] + ['-D' + d for d in defines]
            # -G on Verilator 5.032 accepts literals, not arithmetic. Fold our
            # supported integer grammar while retaining the original expression
            # in the generated instance. Unsupported expressions fail clearly.
            command += [f'-G{k}={constant(v) if constant(v) is not None else parameter_value(v)}'
                        for k, v in (overrides or {}).items()]
            if full:
                for d in dict.fromkeys([str(Path(module.file).parent)] + list(library_dirs)):
                    command += ['-y', str(d)]
                for source in source_files:
                    if Path(source).resolve() != Path(module.file).resolve():
                        command += ['-v', str(source)]
            result = subprocess.run(command + [str(p) for p in packages] + [str(header)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                if re.search(r'(?:Invalid|Unknown|Unrecognized|Unsupported) (?:option|argument)', result.stderr, re.I):
                    continue
                if not full and hasattr(module, 'full_source'):
                    return resolve_types(module, packages, include_dirs, defines, library_dirs, source_files, overrides, full=True)
                errors = result.stderr.strip().replace(str(header), source_file).replace(str(root), '<elaboration>')
                first = errors.find('%Error')
                errors = errors[first:] if first >= 0 else errors
                phase = 'full-module elaboration' if full else 'header type resolution'
                raise ValueError(f'{source_file}:{source_line}: Verilator {phase} failed for module {module.name}:\n' + '\n'.join(errors.splitlines()[:24]))
            try:
                tree = json.loads((root / 'obj/Vports.tree.json').read_text()) if json_format else ET.parse(root / 'ports.xml')
                values = ast_constants(tree, module.name, json_format)
                if full:
                    ports = ast_ports(tree, module.name, json_format)
                    expected = [(d, n) for d, _, n in module.ports if d != 'interface']
                    if set(ports) != set(expected):
                        raise ValueError(f'elaborated ports disagree with parsed interface: {ports!r}')
                if any(identifier not in values for identifier in bit_names.values()):
                    continue
            except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError):
                continue
            for name, identifier in bit_names.items():
                module.details[name]['bits'] = values[identifier]
            module.resolution = 'full' if full else 'header'
            for (name, field), dimensions in dimension_names.items():
                if dimensions and all(values.get(n) is not None for pair in dimensions for n in pair):
                    module.details[name][field] = ''.join('[' + ':'.join(str(values[n]) for n in pair) + ']' for pair in dimensions)
            if full:
                # A module-local typedef has no name in the parent's scope.
                # Preserve its original spelling in metadata, but expose its
                # concrete packed representation in generated declarations.
                for direction, _, name in module.ports:
                    detail = module.details[name]
                    if direction != 'interface' and bus_like('', detail['type']) and '::' not in detail['type'] and not detail.get('declaration_type'):
                        count = bit_width('', detail.get('resolved_unpacked', detail.get('unpacked', '')))
                        bits = detail.get('bits')
                        if count and bits:
                            detail['declaration_type'] = 'logic'
                            width = bits // count
                            detail['resolved_width'] = f'[{width-1}:0]' if width > 1 else ''
            return
        if full:
            raise ValueError(f'{module.file}: Verilator full-module AST unsupported for module {module.name}')
        # The text parser has already retained symbolic dimensions and type names.
        # Callers report width-unknown rather than inventing a typedef bit count.


def preprocess_sources(files, include_dirs=(), defines=(), packages=()):
    """One ordered compilation unit, with per-root text and real-source locations."""
    roots = list(dict.fromkeys(str(Path(p).resolve()) for p in list(packages) + list(files)))
    for source in roots:
        if not Path(source).is_file():
            raise ValueError(f'{source}: source file not found')
    if not roots:
        return {}
    if not shutil.which('verilator'):
        pp = Preprocessor(include_dirs, defines)
        result = {}
        for source in roots:
            pp.locations = []
            result[source] = (pp.read(source), list(pp.locations))
        return result
    command = ['verilator', '-E', '--relative-includes']
    command += ['-I' + str(d) for d in include_dirs] + ['-D' + d for d in defines]
    result = subprocess.run(command + roots, capture_output=True, text=True, timeout=60)
    if result.returncode:
        error = result.stderr.strip()
        match = re.search(r"%Error: (.*?):(\d+):\d+: Cannot find include file: '([^']+)'", error)
        if match:
            error = f'{match[1]}:{match[2]}: missing include "{match[3]}"'
        if 'Define or directive not defined' in error:
            error = 'undefined macro: ' + error
        raise ValueError(error)
    chunks = {source: ([], []) for source in roots}
    root, source, number = roots[0], roots[0], 1
    for line in result.stdout.splitlines(keepends=True):
        directive = re.match(r'\s*`line\s+(\d+)\s+"([^"\n]+)"\s+(\d+)', line)
        if directive:
            number, source, level = int(directive[1]), str(Path(directive[2]).resolve()), int(directive[3])
            # Level 1 enters files; root sources enter in command-line order.
            if level == 1 and source in chunks:
                root = source
            continue
        chunks[root][0].append(line)
        chunks[root][1].append((source, number))
        number += 1
    return {root: (''.join(lines), locations) for root, (lines, locations) in chunks.items()}


def order_packages(packages, include_dirs=(), defines=(), files=()):
    """Stable dependency order, using preprocessed text and original locations."""
    if not packages:
        return []
    prepared = preprocess_sources(files, include_dirs, defines, packages)
    paths = list(dict.fromkeys(str(Path(p).resolve()) for p in packages))
    declarations, references, package_edges = {}, {}, {}
    for path, (text, locations) in prepared.items():
        scan = uncomment(text)
        scan = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: ' ' * len(m[0]), scan)
        scopes = []
        for match in re.finditer(r'\bpackage\s+(?:(?:automatic|static)\s+)?(' + IDENT + r')\s*;', scan):
            location = locations[line_number(text, match.start()) - 1]
            if match[1] in declarations:
                source, line = location
                raise ValueError(f'{source}:{line}: duplicate package {match[1]}')
            declarations[match[1]] = (path, location)
            ending = re.search(r'\bendpackage\b', scan[match.end():])
            scopes.append((match.start(), match.end() + ending.end() if ending else len(scan), match[1]))
            package_edges[match[1]] = {}
        # Classes and typedefs can also qualify names; they are not packages.
        local_types = set(re.findall(r'\bclass\s+(' + IDENT + ')', scan))
        local_types.update(re.findall(r'\btypedef\b[^;]*?\b(' + IDENT + r')\s*;', scan))
        references[path] = [(m[1], locations[line_number(text, m.start()) - 1],
                             next((name for a, b, name in scopes if a <= m.start() < b), None))
                            for m in re.finditer(r'(?<![\w$:])(' + IDENT + r')\s*::', scan)
                            if m[1] not in local_types and m[1] not in ('std', '$unit')]
    edges = {path: {} for path in paths}
    for path, refs in references.items():
        for name, (source, line), owner in refs:
            if name not in declarations:
                raise ValueError(f'{source}:{line}: missing package {name}; supply its source with --package')
            dependency = declarations[name][0]
            if owner and owner != name:
                package_edges[owner][name] = (source, line)
            if dependency != path and path in edges:
                if dependency not in edges:
                    raise ValueError(f'{source}:{line}: package {name} is not a --package source')
                edges[path][dependency] = (name, source, line)
    active, done = [], set()

    def check_cycle(name):
        active.append(name)
        for dependency, (source, line) in sorted(package_edges[name].items()):
            if dependency in active:
                raise ValueError(f'{source}:{line}: package dependency cycle: {" -> ".join(active + [dependency])}')
            if dependency not in done:
                check_cycle(dependency)
        active.pop()
        done.add(name)

    for name in sorted(package_edges):
        if name not in done:
            check_cycle(name)
    ordered, visiting, visited = [], [], set()

    def visit(path):
        visiting.append(path)
        for dependency, (name, source, line) in sorted(edges[path].items()):
            if dependency in visiting:
                cycle = ' -> '.join(Path(p).name for p in visiting + [dependency])
                raise ValueError(f'{source}:{line}: package dependency cycle via {name}: {cycle}')
            if dependency not in visited:
                visit(dependency)
        visiting.pop()
        visited.add(path)
        ordered.append(path)

    for path in sorted(paths):
        if path not in visited:
            visit(path)
    return ordered


def extract_sources(files, include_dirs=(), defines=(), packages=(), library_dirs=()):
    packages = order_packages(packages, include_dirs, defines, files)
    prepared = preprocess_sources(files, include_dirs, defines, packages)
    return {str(file): extract_modules(file, include_dirs, defines, packages, prepared, library_dirs, files) for file in files}


def extract_modules(filepath, include_dirs=(), defines=(), packages=(), prepared=None, library_dirs=(), source_files=()):
    standalone = prepared is None
    if standalone:
        packages = order_packages(packages, include_dirs, defines, [filepath])
    prepared = prepared if prepared is not None else preprocess_sources([filepath], include_dirs, defines, packages)
    text, locations = prepared[str(Path(filepath).resolve())]
    modules = []
    scan = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: re.sub(r'[^\n]', ' ', m[0]), text)
    definition_end = 0
    for match in re.finditer(r'\b(module|interface)\s+(' + IDENT + ')', scan):
        if match.start() < definition_end:
            continue
        end = re.search(r'\bend' + match[1] + r'\b', scan[match.end():])
        if not end:
            source, number = locations[(line_number(text, match.start()) - 1)]
            raise ValueError(f'{source}:{number}: unsupported missing end{match[1]}')
        definition_end = match.end() + end.end()
        line = (line_number(text, match.start()) - 1)
        file, number = locations[line] if line < len(locations) else (str(filepath), line + 1)
        try:
            module = parse_module(match[2], text[match.start():match.end() + end.end()], file)
        except ValueError as exc:
            # Translate module-relative diagnostics back to preprocessed source.
            loc = re.match(r'^(.*?):(\d+): (.*)', str(exc), re.S)
            if loc:
                offset = line + int(loc[2]) - 1
                source, lineno = locations[offset] if offset < len(locations) else (file, number)
                raise ValueError(f'{source}:{lineno}: {loc[3]}') from None
            raise
        for detail in module.details.values():
            offset = line + detail['line'] - 1
            source, lineno = locations[offset]
            detail.update(file=source, line=lineno)
        module.file = str(Path(filepath).resolve())
        module.source_file = file
        module.source_line = number
        module.elaboration = dict(packages=list(packages), include_dirs=list(include_dirs),
                                  defines=list(defines), library_dirs=list(library_dirs),
                                  source_files=list(source_files or [filepath]))
        module.full_source = (text, locations, match.start(), definition_end)
        qualify_imports(module, prepared)
        if (packages or re.search(r'\btypedef\b', text[match.start():definition_end])) and module.kind == 'module' and shutil.which('verilator'):
            resolve_types(module, **module.elaboration)
        modules.append(module)
    definitions = {m.name: m.metadata() for m in modules if m.kind == 'interface'}
    for module in modules:
        module.interfaces = definitions
    if not modules and standalone:
        raise ValueError(f'{filepath}:1: no module definition found')
    return modules


def select_module(file, name=None, **options):
    modules = extract_modules(file, **options)
    if name:
        selected = next((m for m in modules if m.name == name), None)
        if selected is None:
            raise ValueError(f'{file}:1: module {name} not found')
        return selected
    return next((m for m in modules if m.name == Path(file).stem), modules[0])


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


def declaration(direction, width, name, detail=None):
    detail = detail or {}
    type_text = detail.get('declaration_type', detail.get('type', ''))
    # Storage in the child does not imply variable storage in the parent.
    type_text = re.sub(r'\b(?:reg|var)\b', 'wire', type_text)
    if not type_text:
        type_text = 'wire'
    suffix = detail.get('unpacked', '')
    return ' '.join(p for p in [direction, type_text, width, name, suffix] if p)


def generate_instance(module, instance_name=None, signal_prefix=None, show_width=True):
    del show_width  # Connections are whole expressions; never add implicit slices.
    instance_name = instance_name or f'u_{module.name.lower()}'
    params = ''
    if module.params:
        params = ' #(\n' + ',\n'.join(f'        .{n}({v})' for n, v, _ in module.params) + '\n    )'
    ports = ',\n'.join(f'        .{n}({signal_prefix or ""}{n})' for _, _, n in module.ports)
    return f'    {module.name}{params} {instance_name} (\n{ports}\n    );\n'


def generate_port_declarations(module):
    return ',\n'.join('    ' + declaration(d, w, n, module.details[n]) for d, w, n in module.ports) + '\n'


def generate_signal_declarations(module, signal_prefix=None):
    return '\n'.join('    ' + declaration('', resolve_param_width(w, module.params + module.localparams),
                                         (signal_prefix or '') + n, module.details[n]) + ';'
                     for _, w, n in module.ports) + '\n'


def generate_wrapper(module, wrapper_name=None, top_file=None):
    name = wrapper_name or module.name + '_wrap'
    params = ''
    if module.params:
        params = ' #(\n' + ',\n'.join(f'    parameter {t} {n}{module.param_dims.get(n, "")} = {v}' for n, v, t in module.params) + '\n)'
    ports = []
    for d, w, n in module.ports:
        if d == 'interface':
            ports.append('    ' + module.details[n]['type'] + ' ' + n + (' ' + module.details[n]['unpacked'] if module.details[n]['unpacked'] else ''))
        else:
            ports.append('    ' + declaration(d, resolve_param_width(w), n, module.details[n]))
    instance = generate_instance(module)
    if module.params:
        for n, v, _ in module.params:
            instance = instance.replace(f'.{n}({v})', f'.{n}({n})', 1)
    locals_text = ''.join(f'    localparam {t} {n} = {v};\n' for n, v, t in module.localparams)
    metadata = dict(version=1, port_map={}, declarations=locals_text.splitlines(),
                    instances={f'u_{module.name.lower()}': module.metadata()})
    return '// soc-integrate: ' + json.dumps(compact_metadata(metadata, top_file), separators=(',', ':')) + '\n' + f'module {name} {module.imports}{params} (\n' + ',\n'.join(ports) + '\n);\n' + locals_text + instance + 'endmodule\n'


class PortMap:
    """Exact instance keys, legacy module keys, then ordered template rules."""
    def __init__(self, data=None):
        data = data or {}
        self.data = data if any(k in data for k in ('mappings', 'templates', 'domains', 'annotations', 'instances', 'synchronizers', 'interfaces')) else {'mappings': data}
        self.mappings = self.data.get('mappings', {})
        self.rules = []
        self.exact = {}
        for key, value in self.mappings.items():
            if key.startswith(('regex:', 'glob:')) or any(c in key for c in '*?()\\'):
                kind, pattern = key.split(':', 1) if key.startswith(('regex:', 'glob:')) else ('regex' if any(c in key for c in '()\\') else 'glob', key)
                self.rules.append((kind, pattern, value))
            else:
                self.exact[key] = value
        for rule in self.data.get('templates', []):
            kind = 'regex' if 'regex' in rule else 'glob'
            self.rules.append((kind, rule[kind], rule.get('value')))

        self.compiled = []
        for kind, pattern, value in self.rules:
            regex = ''.join('(.*)' if c == '*' else '(.)' if c == '?' else re.escape(c) for c in pattern) if kind == 'glob' else pattern
            try:
                self.compiled.append((re.compile(regex), pattern, value))
            except re.error as exc:
                raise ValueError(f'template {pattern!r}: invalid regex: {exc}') from None

    def lookup(self, instance, module, port):
        for key in (f'{instance}.{port}', f'{module}.{port}'):
            if key in self.exact:
                return True, self.exact[key]
        key = f'{instance}.{port}'
        for regex, pattern, value in self.compiled:
            match = regex.fullmatch(key)
            if match:
                def replace(text):
                    def capture(group):
                        number = int(group[1])
                        if number > len(match.groups()):
                            raise ValueError(f'template {pattern!r}: missing capture ${number}')
                        return match[number] or ''
                    return re.sub(r'\$(\d+)', capture, text)
                if isinstance(value, str):
                    value = replace(value)
                elif isinstance(value, dict):
                    value = {k: replace(v) if isinstance(v, str) else v for k, v in value.items()}
                return True, value
        return False, None


def named_connections(block, file='<top>'):
    result = {}
    for item in split_port_items(block):
        clean = uncomment(item)
        match = re.match(r'\s*\.(' + IDENT + r')\s*\(', clean)
        if not match:
            raise ValueError(f'{file}:1: unsupported positional/wildcard connection: {item.strip()}')
        _, end = balanced(clean, match.end() - 1, file)
        if clean[end:].strip():
            raise ValueError(f'{file}:1: unsupported connection tail: {item.strip()}')
        # Preserve the original expression, including comments and whitespace.
        if match[1] in result:
            fail(file, block, block.find(item), f'duplicate named connection {match[1]}')
        result[match[1]] = item[match.end():end - 1]
    return result


def user_regions(raw, file='<top>'):
    markers = list(re.finditer(r'(?m)^[ \t]*// soc-integrate:user (begin|end)[ \t]*\r?$', raw))
    regions, begin = [], None
    for marker in markers:
        if marker[1] == 'begin':
            if begin is not None:
                fail(file, raw, marker.start(), 'nested user region')
            begin = marker.start()
        else:
            if begin is None:
                fail(file, raw, marker.start(), 'user region end without begin')
            end = marker.end() + (1 if raw[marker.end():].startswith('\n') else 0)
            regions.append((begin, end, raw[begin:end]))
            begin = None
    if begin is not None:
        fail(file, raw, begin, 'unterminated user region')
    return regions


def top_level_mask(text, start):
    """Hide opaque nested scopes so user code is never mistaken for owned RTL."""
    scan = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: re.sub(r'[^\n]', ' ', m[0]), text)
    # Mask whole conditional branches before interpreting procedural scopes;
    # alternatives may contain different begin/end shapes.
    depth, begin = 0, 0
    for token in re.finditer(r'`(?:ifdef|ifndef|endif)\b', scan[start:]):
        if token[0] != '`endif':
            if not depth:
                begin = start + token.start()
            depth += 1
        elif depth:
            depth -= 1
            if not depth:
                end = start + token.end()
                scan = scan[:begin] + re.sub(r'[^\n]', ' ', scan[begin:end]) + scan[end:]
    tokens = re.compile(r'\b(?:generate|endgenerate|function|endfunction|task|endtask|begin|end)\b')
    stack, spans = [], []
    ends = {'generate': 'endgenerate', 'function': 'endfunction', 'task': 'endtask',
            'begin': 'end'}
    for token in tokens.finditer(scan, start):
        word = token[0]
        if word in ends:
            if not stack:
                begin = token.start()
            stack.append(ends[word])
        elif stack and word == stack[-1]:
            stack.pop()
            if not stack:
                spans.append((begin, token.end()))
    for begin, end in spans:
        scan = scan[:begin] + re.sub(r'[^\n]', ' ', scan[begin:end]) + scan[end:]
    return scan


def preserved_instances(raw, metadata):
    """Read owned instances hidden in opaque text, without rewriting their source."""
    text = uncomment(raw)
    text = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: re.sub(r'[^\n]', ' ', m[0]), text)
    result = []
    saved_instances = metadata.get('instances', {})
    modules = {saved['module_name'] for saved in saved_instances.values()}
    if not modules or not text.strip():
        return result
    pattern = re.compile(r'\b(' + '|'.join(re.escape(m) for m in sorted(modules)) + r')\s*(#\s*\()?')
    for match in pattern.finditer(text):
        pos, parameters, parameter_text = match.end(), {}, ''
        if match[2]:
            _, end = balanced(text, pos - 1)
            parameters = named_connections(raw[pos:end - 1])
            parameter_text = raw[match.start(2):end]
            pos = end
        inst = INSTANCE_OPEN.match(text, pos)
        if not inst or inst[1] not in saved_instances or saved_instances[inst[1]]['module_name'] != match[1]:
            continue
        open_pos = inst.end() - 1
        _, end = balanced(text, open_pos)
        tail = SEMICOLON.match(text, end)
        if not tail:
            continue
        result.append(dict(module=match[1], instance=inst[1], parameters=parameters,
                           parameter_text=parameter_text, ports=named_connections(raw[open_pos + 1:end - 1]),
                           preserved=True, span=(match.start(), tail.end())))
    return result


def prune_preserved(top, names, metadata):
    def prune(raw):
        spans = [i['span'] for i in preserved_instances(raw, metadata) if i['instance'] in names]
        for begin, end in sorted(spans, reverse=True):
            raw = raw[:begin] + raw[end:]
        return raw
    top.user_regions = [prune(region) for region in top.user_regions]
    top.unmanaged_text = prune(top.unmanaged_text)


def metadata_paths(value, base, reading=False):
    if isinstance(value, dict):
        return {k: (str((base / v).resolve()) if reading else Path(os.path.relpath(v, base)).as_posix())
                if k == 'file' and isinstance(v, str) and v and not v.startswith('<') else
                metadata_paths(v, base, reading) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [metadata_paths(v, base, reading) for v in value]
    return value


def compact_metadata(metadata, top_file=None):
    """v2 writes each module once; the public in-memory view remains v1-shaped."""
    modules, instances = {}, {}
    for name, saved in metadata.get('instances', {}).items():
        module_name = saved['module_name']
        if module_name not in modules:
            modules[module_name] = {k: v for k, v in saved.items() if k != 'overrides'}
        instances[name] = dict(module_name=module_name, overrides=saved.get('overrides', {}))
    result = dict(metadata, version=2, modules=modules, instances=instances)
    base = Path(top_file).resolve().parent if top_file else Path.cwd()
    return metadata_paths(result, base)


def read_metadata(raw, top_file):
    metadata = {}
    for line in raw.splitlines():
        if line.startswith('// soc-integrate: '):
            metadata = json.loads(line[len('// soc-integrate: '):])
            break
    if metadata.get('version') == 2:
        metadata = metadata_paths(metadata, Path(top_file).resolve().parent, reading=True)
        metadata['instances'] = {name: dict(metadata['modules'][saved['module_name']],
                                           overrides=saved.get('overrides', {}))
                                 for name, saved in metadata.get('instances', {}).items()}
    return metadata


def parse_top(top_file, module_names=None):
    # newline='' matters: custom CRLF text must survive byte for byte too.
    with open(top_file, newline='') as stream:
        raw = stream.read()
    text = uncomment(raw)
    regions = user_regions(raw, top_file)
    for begin, end, _ in regions:
        text = text[:begin] + re.sub(r'[^\n]', ' ', text[begin:end]) + text[end:]
    metadata = read_metadata(raw, top_file)
    if module_names is None and metadata.get('instances'):
        module_names = {i['module_name'] for i in metadata['instances'].values()}
    header = re.search(r'\bmodule\s+(' + IDENT + ')', text)
    if not header:
        fail(top_file, text, 0, 'missing top module')
    start = header.end()
    if text[start:].lstrip().startswith('#'):
        _, start = balanced(text, text.index('(', start), top_file)
    if text[start:].lstrip().startswith('('):
        _, start = balanced(text, text.index('(', start), top_file)
    start = text.index(';', start) + 1
    scan = top_level_mask(text, start)
    ending = re.search(r'\bendmodule\b', scan[start:])
    if not ending:
        fail(top_file, text, start, 'missing endmodule')
    stop = start + ending.start()
    instances, spans = [], []
    interface_specs = {}
    saved_interface_specs = metadata.get('interface_instances', {})
    interface_types = {p['type'].split('.')[0] for i in metadata.get('instances', {}).values()
                       for p in i['ports'] if p['direction'] == 'interface'}
    interface_types |= {spec['type'] for spec in saved_interface_specs.values()}
    for match in re.finditer(r'\b(' + IDENT + r')\s*(#\s*\()?', scan[start:stop]):
        if match[1] not in interface_types:
            continue
        begin, pos = start + match.start(), start + match.end()
        parameters = {}
        if match[2]:
            _, end = balanced(text, pos - 1, top_file)
            parameters = named_connections(raw[pos:end - 1], top_file)
            pos = end
        name = INTERFACE_OPEN.match(text, pos)
        if not name:
            continue
        if 'interface_instances' in metadata and name[1] not in saved_interface_specs:
            continue  # A separate user interface instance is not owned by refresh.
        open_pos = name.end() - 1
        _, end = balanced(text, open_pos, top_file)
        tail = SEMICOLON.match(text, end)
        if not tail:
            fail(top_file, text, end, 'multiple interface instances per statement')
        interface_specs[name[1]] = dict(type=match[1], parameters=parameters,
                                        unpacked=name[2].strip(),
                                        ports=named_connections(raw[open_pos + 1:end - 1], top_file))
        spans.append((begin, tail.end()))
        scan = scan[:begin] + re.sub(r'[^\n]', ' ', scan[begin:tail.end()]) + scan[tail.end():]
    pattern = re.compile(r'\b(' + IDENT + r')\s*(#\s*\()?')
    pos = start
    keywords = {'module', 'endmodule', 'input', 'output', 'inout', 'wire', 'reg', 'logic',
                'assign', 'parameter', 'localparam', 'always', 'initial', 'if', 'else', 'begin', 'end'}
    while pos < stop:
        match = pattern.search(scan, pos, stop)
        if not match:
            break
        pos = match.end()
        if match[1] in keywords or module_names is not None and match[1] not in module_names:
            continue
        parameters, parameter_text = {}, ''
        if match[2]:
            _, end = balanced(text, pos - 1, top_file)
            parameters = named_connections(raw[pos:end - 1], top_file)
            parameter_text = raw[match.start(2):end]
            pos = end
        inst = INSTANCE_OPEN.match(text, pos)
        if not inst:
            if INSTANCE_ARRAY.match(text, pos):
                fail(top_file, text, pos, 'instance arrays')
            continue
        open_pos = inst.end() - 1
        _, end = balanced(text, open_pos, top_file)
        tail = SEMICOLON.match(text, end)
        if not tail:
            fail(top_file, text, end, 'instance array or multiple instances per statement')
        block = raw[open_pos + 1:end - 1]
        ports = named_connections(block, top_file) if uncomment(block).strip() else {}
        instances.append(dict(module=match[1], instance=inst[1], parameters=parameters,
                              parameter_text=parameter_text, ports=ports))
        pos = tail.end()
        spans.append((match.start(), pos))
    top = parse_module(header[1], text[header.start():start] + '\nendmodule', str(top_file))
    top.user_regions = [region for a, b, region in regions if start <= a < stop]
    preamble = raw[:header.start()]
    preamble = re.sub(r'(?m)^// (?:Generated by soc_integrate.py; named connection expressions survive update\.|soc-integrate: [^\n]*)\r?\n', '', preamble)
    top.preamble = preamble if preamble.strip() else ''
    suffix = raw[start + ending.end():]
    top.suffix = suffix if suffix.strip() else ''
    spans += [(a, b) for a, b, _ in regions]
    # Exact ownership records avoid reclassifying a user's declaration merely
    # because it happens to name a connected net.
    owned = metadata.get('declarations')
    if owned is not None:
        remaining = set(owned)
        # Generated declarations occupy one line. Match by exact text, once,
        # rather than compiling one whole-body search per net.
        occupied = sorted(spans)
        ends = [b for _, b in occupied]
        cursor = start
        for line in raw[start:stop].splitlines(keepends=True):
            visible = scan[cursor:cursor + len(line)]
            declaration_text = visible.strip()
            if declaration_text in remaining:
                a = cursor + len(visible) - len(visible.lstrip())
                b = a + len(declaration_text)
                index = bisect_right(ends, a)
                overlaps = index < len(occupied) and occupied[index][0] < b
                if scan[a:b].strip() and not overlaps:
                    spans.append((a, b))
                    remaining.remove(declaration_text)
            cursor += len(line)
    # Older/manual tops have no declaration ownership record. Preserve those
    # declarations conservatively rather than guessing which text may be lost.
    # The only comments owned by generation are the empty-pin lint annotations;
    # they already reside within managed instance spans. All other raw text is
    # retained, including comments and preprocessor branches.
    residual, cursor, diagnostics = [], start, []
    for begin, end in sorted(spans) + [(stop, stop)]:
        if begin > cursor:
            chunk = raw[cursor:begin]
            if chunk.strip():
                residual.append(chunk)
                diagnostics += [(line_number(raw, cursor) + index, line.strip())
                                for index, line in enumerate(chunk.splitlines()) if line.strip()]
        cursor = max(cursor, end)
    retained = [expr for inst in instances for expr in inst['ports'].values()]
    retained += [inst['parameter_text'] for inst in instances]
    retained += [expr for spec in interface_specs.values() for field in ('ports', 'parameters') for expr in spec[field].values()]
    retained_comments = {m[0] for expr in retained for m in COMMENTS.finditer(expr) if m[0].startswith(('/',))}
    for begin, end in spans:
        if not (start <= begin < stop) or any(a <= begin < b for a, b, _ in regions):
            continue
        for comment in COMMENTS.finditer(raw[begin:end]):
            value = comment[0]
            if not value.startswith(('//', '/*')) or re.match(r'// verilator lint_(?:off|on) PINCONNECTEMPTY$', value):
                continue
            if value in retained_comments:
                continue
            residual.append(value + '\n')
            diagnostics.append((line_number(raw, begin + comment.start()), value))
    top.unmanaged = diagnostics
    top.unmanaged_text = ''.join(residual)
    top.custom_signals = {}
    custom = uncomment(''.join(top.user_regions) + top.unmanaged_text)
    custom = top_level_mask(custom, 0)
    for decl in re.finditer(r'\b(?:wire|logic|reg)\b[^;]*;', custom):
        inherited = None
        for item in split_port_items(decl[0][:-1]):
            try:
                declarator = split_port_items(item, '=')[0]
                port, detail, inherited = parse_port('output ' + declarator if inherited is None else declarator, inherited)
            except ValueError:
                continue
            _, width, name = port
            top.custom_signals[name] = dict(direction='', width=width, detail=detail, bits=bit_width(width, detail.get('unpacked', '')))
    opaque = ''.join(top.user_regions) + top.unmanaged_text
    for inst in preserved_instances(opaque, metadata):
        if not any(i['instance'] == inst['instance'] for i in instances):
            inst.pop('span')
            instances.append(inst)
    top.interface_instances = interface_specs
    return header[1], instances, metadata, top


def net_base(expr):
    match = re.fullmatch(r'\s*(' + IDENT + r')\s*(?:\[[^\]]+\]\s*)*', uncomment(expr))
    return match[1] if match else None


def literal_width(expr):
    match = re.fullmatch(r"(\d+)'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+", expr.strip())
    if match:
        return int(match[1])
    if re.fullmatch(r"'[01xXzZ]", expr.strip()):
        return 'fill'
    if re.fullmatch(r'\d+', expr.strip()):
        return 32
    return None


def expression_width(expr, signals):
    expr = uncomment(expr).strip()
    if expr.startswith('('):
        inside, end = balanced(expr, 0)
        if end == len(expr):
            return expression_width(inside, signals)
    width = literal_width(expr)
    if width is not None:
        return width
    base = net_base(expr)
    if base:
        dims = ''.join(re.findall(r'\[[^\]]+\]', expr))
        interval = selection_interval(expr)
        signal = signals.get(base, {})
        unpacked = re.findall(r'\[[^\]]+\]', signal.get('detail', {}).get('unpacked', ''))
        selections = re.findall(r'\[[^\]]+\]', dims)
        if unpacked and selections:
            # A single index consumes an unpacked dimension, retaining the packed
            # element's type/width. Never interpret it as a one-bit part-select.
            bits = signal.get('bits')
            for dimension, selected in zip(unpacked, selections):
                if not re.fullmatch(r'\[\s*[^:\[\]]+\s*\]', selected):
                    raise ValueError(f'unsupported unpacked array slice: {expr}')
                count = bit_width('', dimension)
                if bits is None or count is None:
                    return None
                bits //= count
            if len(selections) > len(unpacked):
                packed = selection_interval(base + ''.join(selections[len(unpacked):]))
                return packed[1] - packed[0] + 1 if packed else None
            return bits
        return interval[1] - interval[0] + 1 if interval else (None if dims else signal.get('bits'))
    if expr.startswith('{') and expr.endswith('}'):
        widths = [expression_width(x, signals) for x in split_port_items(expr[1:-1])]
        return sum(widths) if all(isinstance(w, int) for w in widths) else None
    return None


def default_instances(modules, data):
    modules = [m for m in modules if m.kind == 'module']
    specs = data.get('instances') if isinstance(data, dict) else None
    if specs:
        available = {m.name: m for m in modules}
        for spec in specs:
            if spec['module'] not in available:
                raise ValueError(f"port map references unknown module/instance '{spec['module']}' (known: {', '.join(sorted(available))})")
        return [dict(module=available[s['module']], instance=s['instance'],
                     parameters={k: parameter_value(v) for k, v in s.get('parameters', {}).items()}, parameter_text='', ports={}) for s in specs]
    return [dict(module=m, instance=f'u_{m.name.lower()}', parameters={}, parameter_text='', ports={}) for m in modules]


def port_signature(direction, width, detail, params):
    """Conservatively compare resolved dimensions and value types for auto-sharing.

    Implicit wires, wire/reg/logic storage and explicit unsigned logic have the
    same value type. Named types and signedness remain distinct. Modports on
    the same interface describe different views of one interface instance.
    """
    type_text = detail['type']
    if direction == 'interface':
        type_text = type_text.split('.')[0]
    else:
        type_text = re.sub(r'\b(?:wire|reg|var)\b', '', type_text)
        type_text = ' '.join(type_text.split())
        if type_text in ('', 'signed', 'unsigned'):
            type_text = 'logic ' + type_text
        if type_text.strip() in ('logic', 'logic unsigned'):
            type_text = 'logic'
    unpacked = detail.get('resolved_unpacked', resolve_param_width(detail.get('unpacked', ''), params))
    if direction == 'interface':
        unpacked = repr(interface_shape(unpacked))
    dimensions = (detail.get('resolved_width', resolve_param_width(width, params)), unpacked)
    return (direction == 'interface', ' '.join(type_text.split()),
            *(re.sub(r'\s+', '', dim) for dim in dimensions))


def interface_shape(dimensions):
    """Canonical bounds for equivalent size/range unpacked declarations."""
    shape = []
    for dimension in re.findall(r'\[([^\]]+)\]', dimensions):
        bounds = [constant(v) for v in re.split(r'(?<!:):(?!:)', dimension)]
        if None in bounds:
            shape.append(re.sub(r'\s+', '', dimension))
        else:
            shape.append((0, bounds[0] - 1) if len(bounds) == 1 else tuple(bounds))
    return tuple(shape)


def interface_signal(base, entries, specs, definitions):
    """Resolve one concrete interface instance, including whole/element arrays."""
    spec = dict(specs.get(base, {}))
    types = {r['detail']['type'].split('.')[0] for r in entries} - {'interface'}
    if spec.get('type'):
        types.add(spec['type'])
    if len(types) != 1:
        raise ValueError(f'interface {base}: supply one concrete type via interfaces.{base}.type')
    spec['type'] = next(iter(types))
    parameters = {k: str(v) for k, v in spec.get('parameters', {}).items()}
    definition = definitions.get(spec['type'], {})
    defaults = [(n, str(parameters.get(n, v)), t) for n, v, t in definition.get('params', [])]
    if definition and parameters.keys() - {p[0] for p in defaults}:
        raise ValueError(f'interface {base}: unknown parameter override')
    dimensions = list(dict.fromkeys(r['detail'].get('unpacked', '') for r in entries if r['signal'].strip() == base))
    if len({interface_shape(d) for d in dimensions}) > 1:
        raise ValueError(f'interface {base}: incompatible array dimensions')
    unpacked = spec.get('unpacked', next(iter(dimensions), ''))
    if dimensions and interface_shape(unpacked) != interface_shape(next(iter(dimensions))):
        raise ValueError(f'interface {base}: incompatible array dimensions')
    selections = [selection_interval(r['signal']) for r in entries if r['signal'].strip() != base]
    if selections:
        if any(selection is None for selection in selections):
            raise ValueError(f'interface {base}: array indices must be constant; specify concrete mappings')
        high = max(selection[1] for selection in selections)
        if not unpacked:
            unpacked = f'[0:{high}]'
        bounds = re.fullmatch(r'\[([^\]]+)\]', unpacked)
        interval = selection_interval(base + unpacked) if bounds and ':' in bounds[1] else None
        count = constant(bounds[1]) if bounds and ':' not in bounds[1] else None
        low, upper = interval if interval else (0, count - 1 if count is not None else -1)
        if any(a < low or b > upper for a, b in selections):
            raise ValueError(f'interface {base}: element outside array dimensions {unpacked}')
        if any(r['detail'].get('unpacked') for r in entries if r['signal'].strip() != base):
            raise ValueError(f'interface {base}: an array port requires a whole-array connection')
    spec['unpacked'] = unpacked
    spec['parameters'] = parameters
    spec['ports'] = dict(spec.get('ports', {}))
    for port in definition.get('ports', []):
        spec['ports'].setdefault(port['name'], port['name'])
    spec['definition'] = definition
    spec['defaults'] = defaults
    return {k: spec[k] for k in ('type', 'parameters', 'unpacked', 'ports', 'definition', 'defaults')}


def stale_map_checks(mapping, instances, refreshing=True):
    owners = {}
    for inst in instances:
        ports = {n for _, _, n in inst['module'].ports}
        owners.setdefault(inst['module'].name, set()).update(ports)
        owners[inst['instance']] = ports
    checks = []
    for key in mapping.exact:
        owner, _, port = key.partition('.')
        if owner not in owners and not refreshing:
            raise ValueError(f"port map references unknown module/instance '{owner}' (known: {', '.join(sorted(owners))})")
        if owner not in owners or port not in owners[owner]:
            checks.append(dict(code='stale-port-map', severity='warning', ports=[key],
                               message=f'{key}: port-map key references a non-existent port/instance; remove or correct the entry'))
    return checks


def interface_array_checks(base, entries, spec):
    """Check element coverage, without pretending to do modport signal signoff."""
    shape = interface_shape(spec['unpacked'])
    if len(shape) != 1 or not isinstance(shape[0], tuple):
        return []
    low, high = sorted(shape[0])
    connected, driven, unknown = [], [], []
    definition = spec.get('definition', {})
    for row in entries:
        interval = (low, high) if row['signal'].strip() == base else selection_interval(row['signal'])
        if interval is None:
            continue
        connected.append(interval)
        parts = row['detail']['type'].split('.')
        directions = definition.get('modports', {}).get(parts[-1]) if len(parts) == 2 else None
        if directions is None:
            unknown.append(interval)
        elif set(directions) & {'output', 'inout'}:
            driven.append(interval)

    def gaps(intervals):
        cursor = low
        for a, b in sorted(intervals):
            if a > cursor:
                yield cursor, a - 1
            cursor = max(cursor, b + 1)
        if cursor <= high:
            yield cursor, high

    checks = []
    # Unconnected elements are also undriven; issue one warning for those gaps.
    missing = list(gaps(connected))
    for code, intervals in [('interface-element-unconnected', missing),
                            ('interface-element-undriven', list(gaps(driven + unknown + missing)))]:
        for a, b in intervals:
            element = f'{base}[{a}]' if a == b else f'{base}[{a}:{b}]'
            checks.append(dict(code=code, severity='warning', ports=[r['key'] for r in entries],
                               message=f'{element}: interface array element(s) ' +
                               ('are not connected to any child port' if code.endswith('unconnected') else 'have no connected output/inout modport; review interface drivers')))
    return checks


def build_top(instances, top_name='soc_top', map_data=None, previous_top=None, top_file=None):
    """Resolve connections, declare actual nets, and check the resulting graph."""
    instances = [resolve_instance(i) for i in instances]
    mapping = PortMap(map_data)
    rows, groups, checks = [], {}, []
    checks += stale_map_checks(mapping, instances, previous_top is not None)
    known = {i['instance'] for i in instances} | {i['module'].name for i in instances}
    owners = list(mapping.data.get('annotations', {})) + list(mapping.data.get('domains', {})) + list(mapping.data.get('synchronizers', []))
    for key in owners:
        owner = key.split('.')[0]
        if owner not in known:
            raise ValueError(f"port map references unknown module/instance '{owner}' (known: {', '.join(sorted(known))})")

    def warn(code, message, endpoints=()):
        checks.append(dict(code=code, severity='warning', message=message, ports=list(endpoints)))

    named_ports = {}
    for inst in instances:
        module = inst['module']
        params = [(n, inst['parameters'].get(n, v), t) for n, v, t in module.params] + module.localparams
        for direction, width, name in module.ports:
            signature = port_signature(direction, width, module.details[name], params)
            named_ports.setdefault(name, []).append((direction, signature, f'{inst["instance"]}.{name}'))
    auto_shared, incompatible = set(), set()
    for name, entries in named_ports.items():
        directions = [entry[0] for entry in entries]
        candidate = len(entries) > 1 and (directions.count('output') <= 1 or 'interface' in directions)
        if candidate:
            if len({entry[1] for entry in entries}) == 1:
                if not any(d != 'interface' and (d == 'inout' or bus_like(name, signature[1])) for d, signature, _ in entries):
                    auto_shared.add(name)
            else:
                incompatible.add(name)
    reported_incompatible = set()
    explicit_targets = set()
    for inst in instances:
        for _, _, port in inst['module'].ports:
            found, value = mapping.lookup(inst['instance'], inst['module'].name, port)
            if isinstance(value, dict):
                value = value.get('signal', value.get('value'))
            if found and isinstance(value, str) and net_base(value):
                explicit_targets.add(net_base(value))
    module_counts = {}
    for inst in instances:
        name = inst['module'].name
        module_counts[name] = module_counts.get(name, 0) + 1
    for inst in instances:
        module, instance = inst['module'], inst['instance']
        unknown_params = inst['parameters'].keys() - {p[0] for p in module.params}
        if unknown_params:
            raise ValueError(f'{module.file}:1: unknown parameter overrides on {instance}: {sorted(unknown_params)}')
        params = [(n, inst['parameters'].get(n, v), t) for n, v, t in module.params] + module.localparams
        for direction, width, name in module.ports:
            found, value = mapping.lookup(instance, module.name, name)
            annotation = value if isinstance(value, dict) else {}
            if isinstance(value, dict):
                found = 'signal' in value or 'value' in value
                value = value.get('signal', value.get('value'))
            if name in inst.get('ports', {}):
                expr = inst['ports'][name]
            elif found:
                expr = '' if value is None else str(value)
            else:
                if name in incompatible and name not in reported_incompatible:
                    warn('auto-share-incompatible',
                         f'same-name port {name} has incompatible width/type declarations; '
                         'exposed separately; use an explicit port map to connect',
                         [entry[2] for entry in named_ports[name]])
                    reported_incompatible.add(name)
                if len(named_ports[name]) > 1 and (direction == 'inout' or bus_like(name, module.details[name]['type'])):
                    warn('auto-share-blocked', f'{instance}.{name} exposed per-instance; inout/bus ports require explicit mapping', [f'{instance}.{name}'])
                shared = name in auto_shared or (direction == 'interface' and len(named_ports[name]) == 1)
                prefix = instance if module_counts[module.name] > 1 or direction == 'inout' else module.name.lower()
                expr = name if shared else f'{prefix}_{name}'
                # An explicitly named consumer also connects to the default producer name.
                if direction == 'output' and name in explicit_targets:
                    expr = name
            detail = dict(module.details[name])
            resolved = detail.get('resolved_width', resolve_param_width(width, params))
            detail['unpacked'] = detail.get('resolved_unpacked', resolve_param_width(detail.get('unpacked', ''), params))
            built_in = re.fullmatch(r'(?:(?:wire|reg|logic|var)\s*)?(?:(?:signed|unsigned)\s*)?', detail['type'])
            bits = bit_width(resolved, detail.get('unpacked', '')) if built_in and direction != 'interface' else detail.get('bits')
            row = dict(module=module.name, instance=instance, port=name, direction=direction,
                       width=resolved, symbolic_width=width, detail=detail, bits=bits,
                       signal=expr, key=f'{instance}.{name}', annotation=annotation)
            rows.append(row)
            base = net_base(expr)
            if base:
                groups.setdefault(base, []).append(row)
            elif not expr.strip():
                warn('undriven-input' if direction == 'input' else 'unused-output',
                     f'{row["key"]} is unconnected', [row['key']])
            elif literal_width(expr) is not None:
                if direction != 'input':
                    raise ValueError(f'{module.file}:{detail["line"]}: constant on {direction} {row["key"]}')
            elif direction in ('output', 'inout', 'interface'):
                raise ValueError(f'{module.file}:{detail["line"]}: unsupported {direction} connection: {expr}')
    old = {}
    if previous_top:
        for d, w, n in previous_top.ports:
            old[n] = dict(direction=d, width=w, bits=bit_width(w, previous_top.details[n].get('unpacked', '')), detail=previous_top.details[n])
    signals = {}
    definitions = {n: d for i in instances for n, d in i['module'].interfaces.items()}
    interface_specs = dict(mapping.data.get('interfaces', {}))
    if previous_top:
        interface_specs.update(getattr(previous_top, 'interface_instances', {}))
    resolved_interfaces = {}
    for base, entries in groups.items():
        interface = [r for r in entries if r['direction'] == 'interface']
        if interface:
            if len(interface) != len(entries):
                raise ValueError(f'incompatible interface connection: {base}')
            spec = interface_signal(base, interface, interface_specs, definitions)
            checks += interface_array_checks(base, interface, spec)
            resolved_interfaces[base] = spec
            signals[base] = dict(direction='interface', width='', bits=None, detail=spec)
            continue
        typed_inputs = [r for r in entries if r['direction'] == 'input' and bus_like(r['port'], r['detail']['type'])]
        if len(typed_inputs) > 1:
            warn('explicit-bus-share', f'{base} explicitly shares bus/typed inputs; review protocol intent', [r['key'] for r in typed_inputs])
        drivers = [r for r in entries if r['direction'] in ('output', 'inout')]
        whole_arrays = [r for r in entries if r['signal'].strip() == base and r['detail'].get('unpacked')]
        source = whole_arrays[0] if whole_arrays else next((r for r in drivers if r['direction'] == 'output'), entries[0])
        direction = 'inout' if any(r['direction'] == 'inout' for r in entries) else (
            '' if drivers and any(r['direction'] == 'input' for r in entries) else
            'output' if drivers else 'input')
        width, bits = source['width'], source['bits']
        # Part selections describe a wider parent net, not an implicit truncation.
        slices = [selection_interval(r['signal']) for r in entries]
        high = max((s[1] for s in slices if s), default=-1)
        if not whole_arrays and high >= 0 and (not width or bits is None or high + 1 > bits):
            width, bits = f'[{high}:0]', high + 1
        signals[base] = dict(direction=direction, width=width, bits=bits, detail=source['detail'])
        for i, driver in enumerate(drivers):
            for other in drivers[i + 1:]:
                a = selection_interval(driver['signal']) or (0, (bits or 1) - 1)
                b = selection_interval(other['signal']) or (0, (bits or 1) - 1)
                if max(a[0], b[0]) <= min(a[1], b[1]):
                    warn('multiple-driver', f'{base} has multiple drivers: {driver["key"]}, {other["key"]}', [driver['key'], other['key']])
    if previous_top:
        signals.update(getattr(previous_top, 'custom_signals', {}))
    for spec in resolved_interfaces.values():
        for port in spec['definition'].get('ports', []):
            expr = str(spec['ports'][port['name']])
            if not expr or literal_width(expr) is not None:
                continue
            if not re.fullmatch(IDENT, expr):
                if expr in old:
                    signals.setdefault(expr, old[expr])
                else:
                    raise ValueError(f'interface input expression {expr!r} needs a declared top signal')
            width = resolve_param_width(port['width'], spec['defaults'])
            detail = dict(port, unpacked=resolve_param_width(port.get('unpacked', ''), spec['defaults']))
            signals.setdefault(expr, dict(direction=port['direction'], width=width,
                                          bits=bit_width(width, detail['unpacked']), detail=detail))
    if previous_top:
        custom = ''.join(getattr(previous_top, 'user_regions', [])) + getattr(previous_top, 'unmanaged_text', '')
        custom_names = set(re.findall(IDENT, uncomment(custom)))
        for name, signal in old.items():
            if name in custom_names:
                signals.setdefault(name, signal)
    # General input expressions may reference old top inputs; retain their declarations.
    for row in rows:
        if net_base(row['signal']) or literal_width(row['signal']) is not None or not row['signal'].strip():
            continue
        expression = re.sub(r"(?:\d+)?'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|'[01xXzZ]|\$" + IDENT, '', uncomment(row['signal']))
        dependencies = re.findall(r'\b' + IDENT + r'\b', expression)
        for dep in dependencies:
            if dep not in signals and dep in old:
                signals[dep] = old[dep]
        unknown = [dep for dep in dependencies if dep not in signals and dep not in old]
        if unknown:
            raise ValueError(f'unsupported expression dependencies in {row["key"]}: {", ".join(unknown)}')
    for row in rows:
        if row['direction'] == 'interface' or not row['signal'].strip():
            continue
        actual = expression_width(row['signal'], signals)
        expected = row['bits']
        if isinstance(actual, int) and isinstance(expected, int) and actual != expected:
            warn('width-mismatch', f'width mismatch {row["key"]}: port {expected} bits, connection {row["signal"].strip()} {actual} bits', [row['key']])
        elif actual is None or expected is None:
            warn('width-unknown', f'cannot determine width of {row["key"]} ({row["signal"].strip()})', [row['key']])
    # Infer a module's domain from the actual connected clock net. Multiple clocks
    # need per-port annotations; guessing one would conceal crossings.
    by_instance, by_key = {}, {}
    for row in rows:
        by_instance.setdefault(row['instance'], []).append(row)
        by_key[row['key']] = row
    domains = {}
    for inst in instances:
        clocks = [r['signal'].strip() for r in by_instance.get(inst['instance'], []) if
                  re.fullmatch(r'(?:clk(?:_\w+)?|\w+_clk(?:_i|_o)?)', r['port'])]
        domains[inst['instance']] = list(dict.fromkeys(clocks))
    annotations = mapping.data.get('annotations', {})
    domain_map = mapping.data.get('domains', {})
    synchronizers = mapping.data.get('synchronizers', [])

    def domain(row):
        ann = annotations.get(row['key'], annotations.get(f'{row["module"]}.{row["port"]}', {}))
        ann = dict(ann, **row['annotation'])
        spec = domain_map.get(row['instance'], domain_map.get(row['module']))
        if isinstance(spec, dict):
            spec = spec.get(row['port'], spec.get('clock'))
        clock = ann.get('clock', spec)
        if clock:
            clock_row = by_key.get(f'{row["instance"]}.{clock}')
            return clock_row['signal'].strip() if clock_row else clock
        values = domains[row['instance']]
        return values[0] if len(values) == 1 else None

    for base, entries in groups.items():
        for sink in [r for r in entries if r['direction'] == 'input']:
            ann = annotations.get(sink['key'], annotations.get(f'{sink["module"]}.{sink["port"]}', {}))
            if sink['annotation'].get('sync') or ann.get('sync') or sink['key'] in synchronizers or sink['instance'] in synchronizers:
                continue
            for source in [r for r in entries if r['direction'] == 'output']:
                a, b = domain(source), domain(sink)
                if a and b and a != b:
                    warn('cdc', f'CDC crossing {base}: {source["key"]} ({a}) -> {sink["key"]} ({b}) without declared synchronizer', [source['key'], sink['key']])
                elif len(domains[sink['instance']]) > 1 and b is None:
                    warn('cdc-unknown', f'ambiguous clock domain for {sink["key"]}; annotate clock', [sink['key']])
    module_metadata = {}
    for inst in instances:
        module = inst['module']
        if module.name not in module_metadata:
            module_metadata[module.name] = module.metadata()
    metadata = {'version': 1, 'port_map': mapping.data,
                'interface_instances': {n: {k: v for k, v in spec.items() if k not in ('definition', 'defaults')} for n, spec in resolved_interfaces.items()},
                'instances': {i['instance']: dict(module_metadata[i['module'].name], overrides=i['parameters']) for i in instances}}
    lines = ['// Generated by soc_integrate.py; named connection expressions survive update.',
             '',
             f'module {top_name} (']
    ports, internal = [], []
    # Preserve the actual previous header order, even for dependencies that were
    # discovered late through manual expressions. New external ports follow it.
    signal_order = [name for name in old if name in signals]
    signal_order += [name for name in signals if name not in old]
    for name in signal_order:
        signal = signals[name]
        if previous_top and name in getattr(previous_top, 'custom_signals', {}):
            continue
        d, w, detail = signal['direction'], signal['width'], signal['detail']
        if d == 'interface':
            params = '#(' + ', '.join(f'.{k}({v})' for k, v in detail['parameters'].items()) + ') ' if detail['parameters'] else ''
            dimensions = ' ' + detail['unpacked'] if detail['unpacked'] else ''
            connections = ', '.join(f'.{k}({v})' for k, v in detail['ports'].items())
            internal.append(f'    {detail["type"]} {params}{name}{dimensions} ({connections});')
        elif d:
            ports.append('    ' + declaration(d, w, name, detail))
        else:
            internal.append('    ' + declaration('', w, name, detail) + ';')
    metadata['declarations'] = [line.lstrip() for line in internal]
    lines[1] = '// soc-integrate: ' + json.dumps(compact_metadata(metadata, top_file), separators=(',', ':'))
    if ports:
        lines += [',\n'.join(ports), ');']
    else:
        lines[-1] = f'module {top_name} ();'
    lines += internal
    for inst in instances:
        if inst.get('preserved'):
            continue
        module = inst['module']
        params = inst.get('parameter_text', '')
        if not params and inst['parameters']:
            params = '#(' + ', '.join(f'.{k}({v})' for k, v in inst['parameters'].items()) + ')'
        lines.append(f'    {module.name} {params} {inst["instance"]} (')
        connections = by_instance.get(inst['instance'], [])
        for index, row in enumerate(connections):
            empty = not row['signal'].strip()
            if empty:
                lines.append('        // verilator lint_off PINCONNECTEMPTY')
            comma = ',' if index < len(connections) - 1 else ''
            lines.append(f'        .{row["port"]}({row["signal"]}){comma}')
            if empty:
                lines.append('        // verilator lint_on PINCONNECTEMPTY')
        lines.append('    );')
    if previous_top:
        for region in getattr(previous_top, 'user_regions', []):
            lines.append(region.rstrip('\n'))
        unmanaged = getattr(previous_top, 'unmanaged_text', '')
        if unmanaged:
            lines.append('// soc-integrate:user begin\n' + unmanaged + ('\n' if not unmanaged.endswith('\n') else '') + '// soc-integrate:user end')
    lines.append('endmodule')
    shared = {net: [r['key'] for r in entries] for net, entries in groups.items() if len(entries) > 1}
    code = '\n'.join(lines) + '\n'
    if previous_top:
        code = getattr(previous_top, 'preamble', '') + code
        suffix = getattr(previous_top, 'suffix', '')
        if suffix:
            code = code.rstrip('\n') + suffix
    return code, rows, checks, shared, metadata


def generate_top(modules, top_name='soc_top', port_map=None):
    return build_top(default_instances(modules, port_map or {}), top_name, port_map)[0]


def extract_map_from_top(top_file, expand=False):
    _, instances, meta, _ = parse_top(top_file)
    data = dict(meta.get('port_map', {}))
    mapping = PortMap(data)
    mappings = dict(mapping.mappings)
    shared = {}
    for inst in instances:
        for port, expr in inst['ports'].items():
            found, value = mapping.lookup(inst['instance'], inst['module'], port)
            expected = value.get('signal', value.get('value')) if isinstance(value, dict) else value
            if expand or not found or (expr.strip() != (expected or '').strip()):
                mappings[f'{inst["instance"]}.{port}'] = dict(value, signal=expr) if isinstance(value, dict) else expr
            base = net_base(expr)
            if base:
                shared.setdefault(base, []).append(f'{inst["instance"]}.{port}')
    data['mappings'] = mappings
    if meta.get('interface_instances'):
        _, _, _, top = parse_top(top_file)
        data['interfaces'] = top.interface_instances
    interface_types = {p.get('type', '').split('.')[0] for m in meta.get('instances', {}).values()
                       for p in m.get('ports', []) if p['direction'] == 'interface'}
    data['instances'] = [i for i in instances if i['module'] not in interface_types]
    data['shared_signals'] = {k: v for k, v in shared.items() if len(v) > 1}
    return data


def port_changes(instances, meta, top=None, map_data=None):
    messages, checks = [], []
    mapping = PortMap(map_data if map_data is not None else meta.get('port_map', {}))
    removed_nets, live_nets = {}, {}
    top_ports = {n for _, _, n in top.ports} if top else set()
    for inst in instances:
        module, name = inst['module'], inst['instance']
        if inst.get('preserved'):
            checks.append(dict(code='conditional-preserved', severity='warning', ports=[],
                               message=f'{name}: owned instance preserved verbatim with its wrapping and connections'))
            continue
        old_meta = meta.get('instances', {}).get(name, {})
        old = {p['name']: p for p in old_meta.get('ports', [])}
        previous = set(inst['ports'])
        current = {n: (d, w) for d, w, n in module.ports}
        added, deleted = current.keys() - previous, previous - current.keys()
        for port, expr in inst['ports'].items():
            base = net_base(expr)
            if base and port in deleted:
                removed_nets.setdefault(base, []).append(f'{name}.{port}')
            elif base and port in current:
                live_nets.setdefault(base, set()).add(current[port][0])
        for port in added:
            found, value = mapping.lookup(name, module.name, port)
            if isinstance(value, dict):
                value = value.get('signal', value.get('value'))
            base = net_base(value) if found and isinstance(value, str) else None
            if base:
                live_nets.setdefault(base, set()).add(current[port][0])
        for port in sorted(added):
            messages.append(f'[NEW] {name}.{port}')
        for port in sorted(deleted):
            messages.append(f'[DEL] {name}.{port}')
        if len(added) == len(deleted) == 1:
            before, after = next(iter(deleted)), next(iter(added))
            prior = old.get(before)
            params = [(n, inst['parameters'].get(n, v), t) for n, v, t in module.params] + module.localparams
            if prior:
                old_params = [(n, old_meta.get('overrides', {}).get(n, v), t) for n, v, t in old_meta.get('params', [])] + old_meta.get('localparams', [])
                before_width = resolve_param_width(prior['width'], old_params)
                after_width = resolve_param_width(current[after][1], params)
                before_dims = resolve_param_width(prior.get('unpacked', ''), old_params)
                after_dims = resolve_param_width(module.details[after].get('unpacked', ''), params)
                before_builtin = not bus_like('', prior.get('type', ''))
                after_builtin = not bus_like('', module.details[after].get('type', ''))
                before_bits = bit_width(before_width, before_dims) if before_builtin else prior.get('bits')
                after_bits = bit_width(after_width, after_dims) if after_builtin else module.details[after].get('bits')
                if prior['direction'] == current[after][0] and before_bits is not None and before_bits == after_bits:
                    suggestion = json.dumps({'mappings': {f'{name}.{after}': inst['ports'][before]}}, sort_keys=True)
                    message = f'[REN?] {name}.{before} -> {name}.{after}; possible rename; suggested port-map: {suggestion}'
                    messages.append(message)
                    checks.append(dict(code='possible-rename', severity='warning', message=message, ports=[f'{name}.{before}', f'{name}.{after}']))
        for port in sorted(previous & current.keys() & old.keys()):
            d, w = current[port]
            changed = []
            if d != old[port]['direction']:
                changed.append(f'direction {old[port]["direction"]} -> {d}')
            previous_params = [(n, old_meta.get('overrides', {}).get(n, v), t) for n, v, t in old_meta.get('params', [])]
            previous_width = resolve_param_width(old[port]['width'], previous_params + old_meta.get('localparams', []))
            current_params = [(n, inst['parameters'].get(n, v), t) for n, v, t in module.params] + module.localparams
            current_width = resolve_param_width(w, current_params)
            if w != old[port]['width'] or current_width != previous_width:
                changed.append(f'width {previous_width or "1"} -> {current_width or "1"}')
            if module.details[port].get('unpacked', '') != old[port].get('unpacked', ''):
                changed.append('unpacked dimensions changed')
            if module.details[port].get('type') != old[port].get('type', ''):
                changed.append('type changed')
            if changed:
                message = f'[MOD] {name}.{port}: ' + ', '.join(changed)
                messages.append(message)
                checks.append(dict(code='port-change', severity='warning', message=message, ports=[f'{name}.{port}']))
    if top:
        for base, endpoints in sorted(removed_nets.items()):
            directions = live_nets.get(base, set())
            if base not in top_ports and directions in ({'input'}, {'output'}):
                direction = next(iter(directions))
                checks.append(dict(code='removed-port-exposes-net', severity='warning', ports=endpoints,
                                   message=f'removed child port {", ".join(endpoints)}: former internal net {base} would become a new top-level {direction}; review the port-map before update'))
    return messages, checks


def load_update(target, files, options):
    config = {}
    implicit_files = not files
    if str(target).endswith('.json'):
        config = read_json_object(target, 'update config')
        target = config['output_file']
        files = files or [entry['file'] for entry in config['modules']]
    if implicit_files:
        # Source paths are an optional convenience carried by generated metadata.
        saved = read_metadata(Path(target).read_text(), target)
        sources = [p for i in saved.get('instances', {}).values()
                   for p in [i.get('file')] + [d.get('file') for d in i.get('interfaces', {}).values()] if p]
        files = list(dict.fromkeys(list(files) + sources))
    available = {}
    for modules in extract_sources(files, **options).values():
        available.update((m.name, m) for m in modules)
    definitions = {n: d for m in available.values() for n, d in m.interfaces.items()}
    available = {n: m for n, m in available.items() if m.kind == 'module'}
    for m in available.values():
        m.interfaces = definitions
    name, parsed, meta, top = parse_top(target, set(available))
    instances = []
    for inst in parsed:
        if inst['module'] not in available:
            raise ValueError(f'{target}: source for owned instance {inst["instance"]} ({inst["module"]}) is required')
        inst['module'] = available[inst['module']]
        instances.append(inst)
    if not instances and not meta.get('version'):
        raise ValueError(f'{target}:1: no supported module instances found')
    if not meta and config.get('port_snapshot'):
        meta['instances'] = {i['instance']: {'ports': config['port_snapshot'].get(i['module'].name, [])} for i in instances}
    return target, name, instances, meta, top, config


def report_checks(checks):
    for check in checks:
        print(f'Warning [{check["code"]}]: {check["message"]}', file=sys.stderr)
    print(f'Checks: {len(checks)} warning(s)', file=sys.stderr)


def export_csv(module, filepath):
    with open(filepath, 'w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Direction', 'Width', 'Port Name'])
        writer.writerows(module.ports)


def lint_collateral(args, instances):
    """Scope dependency warnings by source file; never waive the generated top."""
    if not args.output:
        raise ValueError('--lint-config requires an output top file')
    top = Path(args.output).resolve()
    config = top.with_suffix('.vlt')
    filelist = top.with_suffix('.lint.f')
    packages = list(dict.fromkeys(str(Path(p).resolve()) for p in args.packages))
    dependencies = [d['file'] for i in instances for d in i['module'].interfaces.values()]
    dependencies += [i['module'].file for i in instances] + list(getattr(args, 'files', []))
    sources = list(dict.fromkeys(packages + [str(Path(p).resolve()) for p in dependencies]))
    explicit = [Path(d).resolve() for d in args.vendor_dirs + args.library_dirs]
    for source in sources + [str(Path(d).resolve()) for d in args.include_dirs]:
        parts = Path(source).parts
        if 'vendor' in parts:
            explicit.append(Path(*parts[:parts.index('vendor') + 1]))
    directories = list(dict.fromkeys(str(d) for d in explicit))
    if str(top) in sources:
        raise ValueError('generated top cannot also be a dependency source')
    rules = [source for source in sources if 'vendor' in Path(source).parts]
    for directory in directories:
        path = Path(directory)
        if top.is_relative_to(path):
            # A glob over an ancestor of the top would suppress its diagnostics.
            rules += [str(p.resolve()) for p in sorted(path.rglob('*'))
                      if p.is_file() and p.suffix in ('.sv', '.v', '.vh', '.svh') and p.resolve() != top]
        else:
            rules.append(str(path / '*'))
    rules = list(dict.fromkeys(rules))
    lines = ['`verilator_config', '// Dependency diagnostics only; generated top warnings remain fatal.']
    # Performance and C++ symbol-portability diagnostics are outside the lint
    # group. Scope these to the same explicitly selected vendor sources too.
    for source in rules:
        lines += ['lint_off -file ' + json.dumps(source),
                  'lint_off -rule UNOPTFLAT -file ' + json.dumps(source),
                  'lint_off -rule SYMRSVDWORD -file ' + json.dumps(source)]
    manifest = [json.dumps(p) for p in packages]
    manifest += [json.dumps('-I' + str(Path(d).resolve())) for d in args.include_dirs]
    manifest += [json.dumps('-D' + d) for d in args.defines]
    manifest += ['-y ' + json.dumps(str(Path(d).resolve())) for d in args.library_dirs]
    manifest += [json.dumps(p) for p in sources if p not in packages]
    manifest.append(json.dumps(str(top)))
    return config, '\n'.join(lines) + '\n', filelist, '\n'.join(manifest) + '\n'


def emit_result(args, instances, name, data, previous=None, changes=None, extra_checks=()):
    if previous is None and args.output and Path(args.output).exists():
        raw = Path(args.output).read_text()
        generated = re.search(r'(?m)^// Generated by soc_integrate.py;', raw) and re.search(r'(?m)^// soc-integrate: ', raw)
        if not generated:
            if not getattr(args, 'force', False):
                raise ValueError(f'{args.output}: not a soc-integrate generated top; use --force to replace')
        else:
            _, prior_instances, meta, previous = parse_top(args.output)
            surviving = {i['instance'] for i in instances}
            removed = {i['instance'] for i in prior_instances} - surviving
            prune_preserved(previous, removed, meta)
            for instance in sorted(removed):
                print(f'Warning [removed-instance]: dropped tool-managed {instance}', file=sys.stderr)
            # Retained opaque instances participate in the graph but stay verbatim.
            opaque = {i['instance']: i for i in prior_instances if i.get('preserved')}
            for inst in instances:
                if inst['instance'] in opaque:
                    inst.update({k: v for k, v in opaque[inst['instance']].items() if k != 'module'})
    code, rows, checks, shared, _ = build_top(instances, name, data, previous, args.output)
    checks = list(extra_checks) + checks
    if previous is not None:
        checks += [dict(code='preserved-unmanaged', severity='warning', ports=[],
                        message=f'{args.output}:{line}: {statement} | preserved in an automatic user region')
                   for line, statement in getattr(previous, 'unmanaged', [])
                   if not any(c['code'] == 'preserved-unmanaged' and f':{line}: ' in c['message'] for c in extra_checks)]
    if any(i.get('preserved') for i in instances) and not any(c['code'] == 'conditional-preserved' for c in checks):
        checks.append(dict(code='conditional-preserved', severity='warning', ports=[],
                           message='owned conditional instances preserved verbatim with their wrapping and connections'))
    report_checks(checks)
    if args.strict and checks:
        raise ValueError('strict check failed; no output written')
    collateral = lint_collateral(args, instances) if args.lint_config else None
    if args.output:
        write_text(args.output, code)
        print(f'Top written: {args.output}')
    else:
        print(code, end='')
    if collateral:
        config, config_text, filelist, manifest = collateral
        write_text(config, config_text)
        write_text(filelist, manifest)
        print(f'Lint config written: {config}\nLint filelist written: {filelist}')
    directory = Path(args.output).resolve().parent if args.output else Path.cwd()
    if args.track:
        config = dict(top_module=name, output_file=str(Path(args.output).resolve()) if args.output else None,
                      modules=[dict(file=i['module'].file, module_name=i['module'].name, instance_name=i['instance']) for i in instances],
                      port_map=data, mappings=PortMap(data).mappings, shared_signals=shared,
                      port_snapshot={i['module'].name: i['module'].metadata()['ports'] for i in instances}, checks=checks)
        write_json(directory / f'{name}.integrate.json', config)
    if args.csv:
        with open(directory / f'{name}.integrate.csv', 'w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['Module', 'Instance', 'Port', 'Direction', 'Width', 'Signal', 'Shared_With', 'Status', 'Checks'])
            for row in rows:
                others = [k for k in shared.get(net_base(row['signal']), []) if k != row['key']]
                status = next((m.split(']')[0][1:] for m in changes or [] if row['key'] in m), '')
                warnings = '; '.join(c['code'] for c in checks if row['key'] in c['ports'])
                writer.writerow([row['module'], row['instance'], row['port'], row['direction'], row['width'], row['signal'], ', '.join(others), status, warnings])
    return checks


def compare_ports(module, snapshot):
    old = {p['name']: (p['direction'], p['width']) for p in snapshot['ports']}
    now = {n: (d, w) for d, w, n in module.ports}
    messages = []
    for name in sorted(now.keys() - old.keys()):
        messages.append(f'[NEW] {module.name}.{name}')
    for name in sorted(old.keys() - now.keys()):
        messages.append(f'[DEL] {module.name}.{name}')
    for name in sorted(old.keys() & now.keys()):
        if old[name] != now[name]:
            messages.append(f'[MOD] {module.name}.{name}: {old[name]} -> {now[name]}')
    added, deleted = now.keys() - old.keys(), old.keys() - now.keys()
    if len(added) == len(deleted) == 1:
        before, after = next(iter(deleted)), next(iter(added))
        prior = next(p for p in snapshot['ports'] if p['name'] == before)
        detail = module.details[after]
        before_width = resolve_param_width(prior['width'], snapshot.get('params', []) + snapshot.get('localparams', []))
        after_width = resolve_param_width(now[after][1], module.params + module.localparams)
        before_bits = prior.get('bits') if bus_like('', prior.get('type', '')) else bit_width(before_width, prior.get('unpacked', ''))
        after_bits = detail.get('bits') if bus_like('', detail.get('type', '')) else bit_width(after_width, detail.get('unpacked', ''))
        if prior['direction'] == now[after][0] and before_bits is not None and before_bits == after_bits:
            suggestion = json.dumps({'mappings': {f'{module.name}.{after}': '<former connection>'}})
            messages.append(f'[REN?] {module.name}.{before} -> {module.name}.{after}; suggested port-map: {suggestion} (snapshot has no connections; substitute the former signal)')
    return messages


def prune_map(data, removed, surviving):
    """Drop exact owners and templates which only matched removed endpoints."""
    data = json.loads(json.dumps(PortMap(data).data))
    live = {i['instance'] for i in surviving} | {i['module'].name for i in surviving}
    dead = ({i['instance'] for i in removed} | {i['module'].name for i in removed}) - live
    old_keys = [f'{i["instance"]}.{p}' for i in removed for _, _, p in i['module'].ports]
    live_keys = [f'{i["instance"]}.{p}' for i in surviving for _, _, p in i['module'].ports]

    def dead_rule(kind, pattern):
        regex = ''.join('(.*)' if c == '*' else '(.)' if c == '?' else re.escape(c) for c in pattern) if kind == 'glob' else pattern
        return any(re.fullmatch(regex, key) for key in old_keys) and not any(re.fullmatch(regex, key) for key in live_keys)

    patterns = {pattern: kind for kind, pattern, _ in PortMap(data).rules}
    for field in ('mappings', 'annotations', 'domains'):
        cleaned = {}
        for key, value in data.get(field, {}).items():
            if field == 'mappings' and (key.startswith(('regex:', 'glob:')) or key in patterns):
                pattern = key.split(':', 1)[1] if key.startswith(('regex:', 'glob:')) else key
                if dead_rule(patterns[pattern], pattern):
                    continue
            elif key.split('.')[0] in dead:
                continue
            cleaned[key] = value
        if field in data:
            data[field] = cleaned
    if 'templates' in data:
        data['templates'] = [r for r in data['templates'] if not dead_rule('regex' if 'regex' in r else 'glob', r.get('regex', r.get('glob')))]
    if 'instances' in data:
        data['instances'] = [i for i in data['instances'] if i.get('instance', i.get('instance_name')) not in dead and i.get('module') not in dead]
    if 'synchronizers' in data:
        data['synchronizers'] = [key for key in data['synchronizers'] if key.split('.')[0] not in dead]
    return data


def read_filelists(filelists, args, active=()):
    """Consume soc_flist-compatible plain source/option lists; paths are list-relative."""
    files = []
    for file in filelists:
        path = Path(file).resolve()
        if path in active:
            raise ValueError(f'{path}: recursive filelist')
        tokens = []
        for line in uncomment(path.read_text()).splitlines():
            tokens.extend(shlex.split(line, comments=True))
        index = 0
        def relative(value):
            return str((path.parent / value).resolve())
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if token in ('-I', '-D', '-y', '-f'):
                if index == len(tokens):
                    raise ValueError(f'{path}: {token} requires a value')
                value = tokens[index]
                index += 1
                if token == '-f':
                    files += read_filelists([relative(value)], args, active + (path,))
                elif token == '-D':
                    args.defines.append(value)
                else:
                    getattr(args, 'include_dirs' if token == '-I' else 'library_dirs').append(relative(value))
            elif token.startswith('+incdir+'):
                args.include_dirs.extend(relative(d) for d in token[len('+incdir+'):].split('+'))
            elif token.startswith('+define+'):
                args.defines.extend(token[len('+define+'):].split('+'))
            elif token.startswith(('-I', '-D')):
                getattr(args, 'include_dirs' if token[:2] == '-I' else 'defines').append(relative(token[2:]) if token[:2] == '-I' else token[2:])
            elif token.startswith('-'):
                raise ValueError(f'{path}: unsupported filelist option {token}')
            else:
                files.append(relative(token))
    return files


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    subs = cli.add_subparsers(dest='command', required=True)
    for command in ('extract', 'instantiate', 'wrap', 'csv', 'snapshot', 'diff', 'check', 'extract-map', 'integrate', 'update', 'remove'):
        sub = subs.add_parser(command)
        sub.add_argument('-I', '--include-dir', dest='include_dirs', action='append', default=[])
        sub.add_argument('-D', '--define', dest='defines', action='append', default=[])
        sub.add_argument('--package', dest='packages', action='append', default=[], help='Package/typedef source in dependency order (repeatable)')
        sub.add_argument('-y', '--library-dir', dest='library_dirs', action='append', default=[])
        sub.add_argument('--vendor-dir', dest='vendor_dirs', action='append', default=[])
        if command != 'snapshot':
            sub.add_argument('-f', '--filelist', action='append', default=[])
        sub.add_argument('--strict', action='store_true', help='Warnings fail without writing outputs')
        if command not in ('integrate', 'update', 'remove', 'extract-map'):
            sub.add_argument('-m', '--module')
        sub.add_argument('-n', '--name')
        sub.add_argument('-o', '--output')
        if command == 'integrate':
            sub.add_argument('files', nargs='*')
            sub.add_argument('--force', action='store_true', help='Allow replacing a non-generated file')
        else:
            sub.add_argument('file')
        if command in ('integrate', 'update', 'remove'):
            sub.add_argument('--map')
            sub.add_argument('--csv', action='store_true', help='Opt in to review CSV')
            sub.add_argument('--lint-config', action='store_true', help='Write vendor-scoped .vlt and .lint.f; top warnings stay fatal')
            sub.add_argument('--track', action='store_true', help='Opt in to .integrate.json')
            sub.add_argument('--no-config', action='store_true', help=argparse.SUPPRESS)
        if command in ('update', 'diff', 'check', 'remove'):
            sub.add_argument('--files', nargs='+', default=[])
        if command in ('diff', 'check'):
            sub.add_argument('snapshot', nargs='?')
        if command == 'remove':
            sub.add_argument('module_name')
        if command == 'extract-map':
            sub.add_argument('--verify', nargs='+')
            sub.add_argument('--expand', action='store_true')
        if command == 'snapshot':
            sub.add_argument('-f', '--format', choices=('json', 'csv', 'both'), default='both')
            sub.add_argument('-v', '--version', default='1.0.0')
            sub.add_argument('-c', '--changelog', default='')
    return cli


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    expanded = []
    for arg in argv:
        if arg.startswith('+incdir+'):
            for directory in arg[len('+incdir+'):].split('+'):
                expanded += ['-I', directory]
        elif arg.startswith('+define+'):
            for define in arg[len('+define+'):].split('+'):
                expanded += ['-D', define]
        else:
            expanded.append(arg)
    args = parser().parse_args(expanded)
    options = dict(include_dirs=args.include_dirs, defines=args.defines, packages=args.packages, library_dirs=args.library_dirs)
    if getattr(args, 'no_config', False):
        args.track = False
    try:
        listed = read_filelists(getattr(args, 'filelist', []), args)
        if hasattr(args, 'files'):
            args.files += listed
        elif listed:
            raise ValueError('-f filelist is supported with integrate or --files workflows')
        args.packages = order_packages(args.packages, args.include_dirs, args.defines, getattr(args, 'files', []) or ([args.file] if hasattr(args, 'file') and not str(args.file).endswith('.json') else []))
        options = dict(include_dirs=args.include_dirs, defines=args.defines, packages=args.packages, library_dirs=args.library_dirs)
        if args.command == 'integrate':
            if not args.files:
                raise ValueError('integrate requires module files or -f filelist')
            name = args.name or (Path(args.output).stem if args.output else None)
            if not name:
                raise ValueError('integrate requires -n NAME or -o OUTPUT')
            args.output = args.output or name + '.sv'
            modules = [next((m for m in ms if m.name == Path(file).stem), ms[0])
                       for file, ms in extract_sources(args.files, **options).items() if ms]
            definitions = {n: d for m in modules for n, d in m.interfaces.items()}
            for m in modules:
                m.interfaces = definitions
            data = read_json_object(args.map, 'port map') if args.map else {}
            emit_result(args, default_instances(modules, data), name, data)
        elif args.command in ('update', 'remove') or (args.command in ('diff', 'check') and not args.snapshot):
            target, name, instances, meta, top, config = load_update(args.file, args.files, options)
            if getattr(args, 'module', None) and args.module != name:
                raise ValueError(f'{target}: top module {args.module} not found (found {name})')
            removed = []
            if args.command == 'remove':
                removed = [i for i in instances if args.module_name in (i['module'].name, i['instance'])]
                if not removed:
                    raise ValueError(f'unknown module/instance {args.module_name!r}')
                instances = [i for i in instances if i not in removed]
            data = read_json_object(args.map, 'port map') if getattr(args, 'map', None) else meta.get('port_map', config.get('port_map', {'mappings': config.get('mappings', {})}))
            messages, checks = port_changes(instances, meta, top, data)
            for line, statement in top.unmanaged:
                checks.append(dict(code='preserved-unmanaged', severity='warning', ports=[],
                                   message=f'{target}:{line}: {statement} | preserved in an automatic user region'))
            for message in messages:
                print(message)
            if args.command == 'diff':
                checks += stale_map_checks(PortMap(data), instances)
                report_checks(checks)
                if args.strict and checks:
                    return 1
            elif args.command == 'check':
                _, _, graph_checks, _, _ = build_top(instances, name, meta.get('port_map', {}), top)
                report_checks(checks + graph_checks)
                if args.strict and (checks or graph_checks):
                    return 1
            else:
                if removed:
                    data = prune_map(data, removed, instances)
                    prune_preserved(top, {i['instance'] for i in removed}, meta)
                args.output = args.output or target
                emit_result(args, instances, args.name or name, data, top, messages, checks)
        elif args.command == 'extract-map':
            data = extract_map_from_top(args.file, args.expand)
            if args.verify:
                available = {m.name: m for ms in extract_sources(args.verify, **options).values() for m in ms}
                for inst in data['instances']:
                    module = available.get(inst['module'])
                    if not module:
                        raise ValueError(f'unknown module {inst["module"]}')
                    unknown = set(inst['ports']) - {n for _, _, n in module.ports}
                    if unknown:
                        raise ValueError(f'unknown ports on {inst["instance"]}: {sorted(unknown)}')
            if args.output:
                write_json(args.output, data)
            else:
                print(json.dumps(data, indent=2))
        else:
            module = select_module(args.file, args.module, **options)
            if args.command == 'extract':
                text = json.dumps(module.metadata(), indent=2)
            elif args.command == 'instantiate':
                text = generate_instance(module, args.name)
            elif args.command == 'wrap':
                text = generate_wrapper(module, args.name, args.output)
            elif args.command == 'csv':
                export_csv(module, args.output or 'ports.csv')
                return 0
            elif args.command == 'snapshot':
                prefix = args.output or str(Path(args.file).with_name(module.name + '_ports'))
                data = dict(module.metadata(), version=args.version, changelog=args.changelog)
                if args.format in ('json', 'both'):
                    write_json(prefix + '.json', data)
                if args.format in ('csv', 'both'):
                    export_csv(module, prefix + '.csv')
                return 0
            else:
                messages = compare_ports(module, read_json_object(args.snapshot, 'snapshot', 'pass RTL via --files'))
                print('\n'.join(messages) if messages else 'No port changes')
                return 1 if messages and args.command == 'check' else 0
            if args.output:
                write_text(args.output, text)
            else:
                print(text, end='' if text.endswith('\n') else '\n')
        return 0
    except (ValueError, OSError, KeyError, re.error, subprocess.TimeoutExpired, ET.ParseError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
