#!/usr/bin/env python3
"""Small, conservative RTL interface parser and SoC connection generator (stdlib only).

This is an interface parser, not an elaborator. Balanced lists are parsed rather
than split with regular expressions; unsupported interface syntax is an error.
"""
import argparse
import ast
import csv
import json
import operator
import re
import sys
from pathlib import Path


IDENT = r'[A-Za-z_][\w$]*'


def uncomment(text):
    """Mask comments, preserving offsets/newlines and quoted strings."""
    pattern = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/'
    return re.sub(pattern, lambda m: m[0] if m[0].startswith('"') else
                  re.sub(r'[^\n]', ' ', m[0]), text, flags=re.S)


def fail(file, text, pos, construct):
    raise ValueError(f'{file}:{text.count(chr(10), 0, pos) + 1}: unsupported {construct}')


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

    def read(self, file):
        file = Path(file).resolve()
        if file in self.active_files:
            raise ValueError(f'{file}:1: recursive include')
        self.active_files.append(file)
        result, stack, active = [], [], True
        text = uncomment(file.read_text(encoding='utf-8'))
        for number, line in enumerate(text.splitlines(keepends=True), 1):
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
                    if not match:
                        raise ValueError(f'{file}:{number}: unsupported function-like macro: {arg}')
                    self.macros[match[1]] = match[2] or ''
                elif active and kind == 'undef':
                    self.macros.pop(arg, None)
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
                    for _ in range(32):
                        names = re.findall(r'`(' + IDENT + ')', line)
                        if not names:
                            break
                        for name in names:
                            if name not in self.macros:
                                raise ValueError(f'{file}:{number}: undefined macro `{name}')
                        line = re.sub(r'`(' + IDENT + ')', lambda m: self.macros[m[1]], line)
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


def constant(expr, values=None):
    """Evaluate a deliberately small integer expression grammar, without eval."""
    values = values or {}
    expr = expr.replace('$clog2', 'clog2')
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
    values = {}
    for name, default, _ in params:
        value = constant(default, values)
        if value is not None:
            values[name] = value

    def dimension(match):
        parts = match[1].split(':')
        output = []
        for part in parts:
            value = constant(part, values)
            output.append(str(value) if value is not None else part.strip())
        return '[' + ':'.join(output) + ']'
    return re.sub(r'\[([^\]]+)\]', dimension, width)


def bit_width(width):
    if not width:
        return 1
    result = 1
    for dim in re.findall(r'\[([^\]]+)\]', width):
        parts = dim.split(':')
        if len(parts) != 2:
            return None
        hi, lo = map(constant, parts)
        if hi is None or lo is None:
            return None
        result *= abs(hi - lo) + 1
    return result


class VerilogModule:
    def __init__(self, name=''):
        self.name = name
        self.params = []             # Public parameters, backward-compatible tuples
        self.localparams = []
        self.ports = []              # Backward-compatible (direction, packed width, name)
        self.details = {}            # Type text, unpacked dimensions and source location
        self.file = ''

    def metadata(self):
        return {'module_name': self.name, 'file': self.file,
                'params': self.params, 'localparams': self.localparams,
                'ports': [dict(direction=d, width=w, name=n, **self.details.get(n, {}))
                          for d, w, n in self.ports]}


def parse_parameters(section, module, local=False):
    inherited = ''
    for item in split_port_items(section):
        item = re.sub(r'^\s*(?:parameter|localparam)\b\s*', '', item).strip()
        match = re.fullmatch(r'(.*?)\b(' + IDENT + r')\s*=\s*(.+)', item, re.S)
        if not match:
            raise ValueError(f'unsupported parameter declaration: {item}')
        type_text, name, value = match.groups()
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
        if unpacked.strip():
            raise ValueError(f'unsupported interface array: {item}')
        if not re.fullmatch(IDENT + r'(?:\.' + IDENT + ')?', type_text):
            raise ValueError(f'unsupported interface port: {item}')
    elif type_text and not re.fullmatch(
            r'(?:(?:wire|reg|logic|var)\s*)?(?:(?:signed|unsigned)\s*)?|' +
            r'(?:(?:wire|var)\s+)?' + IDENT + r'(?:::' + IDENT + r')*(?:\s+(?:signed|unsigned))?', type_text):
        raise ValueError(f'unsupported port type: {item}')
    detail = {'type': type_text, 'unpacked': resolve_param_width(unpacked.strip())}
    return (kind, width, name), detail, (kind, type_text, width)


def parse_module(name, content, file='<text>'):
    module = VerilogModule(name)
    module.file = str(file)
    text = uncomment(content)
    match = re.match(r'\s*module\s+' + re.escape(name) + r'\b\s*', text)
    if not match:
        fail(file, text, 0, 'module header')
    pos = match.end()
    try:
        if text[pos:pos + 1] == '#':
            pos += 1
            while text[pos].isspace():
                pos += 1
            section, pos = balanced(text, pos, file)
            parse_parameters(section, module)
        while text[pos].isspace():
            pos += 1
        if text[pos] == ';':
            section = ''
        elif text[pos] == '(':
            section, pos = balanced(text, pos, file)
        else:
            fail(file, text, pos, 'module port list')
        while text[pos].isspace():
            pos += 1
        if text[pos] != ';':
            fail(file, text, pos, 'module header terminator')
        body = text[pos + 1:]
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
            for item in items:
                pos = text.find(item.strip(), match.end())
                port, detail, inherited = parse_port(item, inherited)
                if port[2] in module.details:
                    raise ValueError(f'duplicate port: {port[2]}')
                module.ports.append(port)
                module.details[port[2]] = detail
        for _, _, port in module.ports:
            module.details[port]['line'] = text.count('\n', 0, text.find(port)) + 1
        return module
    except (ValueError, IndexError) as exc:
        fail(file, text, min(pos, len(text)), str(exc))


def extract_modules(filepath, include_dirs=(), defines=()):
    pp = Preprocessor(include_dirs, defines)
    text = pp.read(filepath)
    modules = []
    scan = re.sub(r'"(?:\\.|[^"\\])*"', lambda m: re.sub(r'[^\n]', ' ', m[0]), text)
    for match in re.finditer(r'\bmodule\s+(' + IDENT + ')', scan):
        end = re.search(r'\bendmodule\b', scan[match.end():])
        if not end:
            fail(filepath, text, match.start(), 'missing endmodule')
        line = text.count('\n', 0, match.start())
        file, number = pp.locations[line] if line < len(pp.locations) else (str(filepath), line + 1)
        try:
            module = parse_module(match[1], text[match.start():match.end() + end.end()], file)
        except ValueError as exc:
            # Translate module-relative diagnostics back to preprocessed source.
            loc = re.match(r'^(.*?):(\d+): (.*)', str(exc), re.S)
            if loc:
                offset = line + int(loc[2]) - 1
                source, lineno = pp.locations[offset] if offset < len(pp.locations) else (file, number)
                raise ValueError(f'{source}:{lineno}: {loc[3]}') from None
            raise
        module.file = str(Path(filepath).resolve())
        modules.append(module)
    if not modules:
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


def declaration(direction, width, name, detail=None):
    detail = detail or {}
    type_text = detail.get('type', '')
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


def generate_wrapper(module, wrapper_name=None):
    name = wrapper_name or module.name + '_wrap'
    params = ''
    if module.params:
        params = ' #(\n' + ',\n'.join(f'    parameter {t} {n} = {v}' for n, v, t in module.params) + '\n)'
    ports = []
    for d, w, n in module.ports:
        if d == 'interface':
            ports.append('    ' + module.details[n]['type'] + ' ' + n)
        else:
            ports.append('    ' + declaration(d, resolve_param_width(w), n, module.details[n]))
    instance = generate_instance(module)
    if module.params:
        for n, v, _ in module.params:
            instance = instance.replace(f'.{n}({v})', f'.{n}({n})', 1)
    locals_text = ''.join(f'    localparam {t} {n} = {v};\n' for n, v, t in module.localparams)
    return f'module {name}{params} (\n' + ',\n'.join(ports) + '\n);\n' + locals_text + instance + 'endmodule\n'


class PortMap:
    """Exact instance keys, legacy module keys, then ordered template rules."""
    def __init__(self, data=None):
        data = data or {}
        self.data = data if any(k in data for k in ('mappings', 'templates', 'domains', 'annotations', 'instances', 'synchronizers')) else {'mappings': data}
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

    def lookup(self, instance, module, port):
        for key in (f'{instance}.{port}', f'{module}.{port}'):
            if key in self.exact:
                return True, self.exact[key]
        key = f'{instance}.{port}'
        for kind, pattern, value in self.rules:
            if kind == 'glob':
                # Capture '*' and '?' in order, while treating brackets literally.
                regex = ''.join('(.*)' if c == '*' else '(.)' if c == '?' else re.escape(c) for c in pattern)
            else:
                regex = pattern
            match = re.fullmatch(regex, key)
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


def parse_top(top_file):
    raw = Path(top_file).read_text()
    text = uncomment(raw)
    header = re.search(r'\bmodule\s+(' + IDENT + ')', text)
    if not header:
        fail(top_file, text, 0, 'missing top module')
    start = header.end()
    # Skip the top header so it cannot be mistaken for an instance.
    if text[start:].lstrip().startswith('#'):
        pos = text.index('(', start)
        _, start = balanced(text, pos, top_file)
    if text[start:].lstrip().startswith('('):
        _, start = balanced(text, text.index('(', start), top_file)
    start = text.index(';', start) + 1
    for construct in ('assign', 'always', 'always_comb', 'always_ff', 'initial', 'generate', 'function', 'task'):
        unsupported = re.search(r'\b' + construct + r'\b', text[start:])
        if unsupported:
            fail(top_file, text, start + unsupported.start(), f'top-level {construct}; update owns generated structure only')
    instances = []
    pattern = re.compile(r'\b(' + IDENT + r')\s*(#\s*\()?')
    pos = start
    keywords = {'module', 'endmodule', 'input', 'output', 'inout', 'wire', 'reg', 'logic',
                'assign', 'parameter', 'localparam', 'always', 'initial', 'if', 'else', 'begin', 'end'}
    while pos < len(text):
        match = pattern.search(text, pos)
        if not match:
            break
        pos = match.end()
        if match[1] in keywords:
            continue
        parameters, parameter_text = {}, ''
        if match[2]:
            block, end = balanced(text, pos - 1, top_file)
            parameters = named_connections(raw[pos:end - 1], top_file)
            parameter_text = raw[match.start(2):end]
            pos = end
        inst = re.match(r'\s*(' + IDENT + r')\s*\(', text[pos:])
        if not inst:
            if re.match(r'\s*' + IDENT + r'\s*\[', text[pos:]):
                fail(top_file, text, pos, 'instance arrays')
            continue
        open_pos = pos + inst.end() - 1
        _, end = balanced(text, open_pos, top_file)
        tail = re.match(r'\s*;', text[end:])
        if not tail:
            fail(top_file, text, end, 'instance array or multiple instances per statement')
        block = raw[open_pos + 1:end - 1]
        # Interface instances have an empty connection list.
        ports = named_connections(block, top_file) if block.strip() else {}
        instances.append(dict(module=match[1], instance=inst[1], parameters=parameters,
                              parameter_text=parameter_text, ports=ports))
        pos = end + tail.end()
    metadata = {}
    for line in raw.splitlines():
        if line.startswith('// soc-integrate: '):
            metadata = json.loads(line[len('// soc-integrate: '):])
    top = parse_module(header[1], text[header.start():], str(top_file))
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
        return bit_width(dims) if dims and ':' in dims else (1 if dims else signals.get(base, {}).get('bits'))
    if expr.startswith('{') and expr.endswith('}'):
        widths = [expression_width(x, signals) for x in split_port_items(expr[1:-1])]
        return sum(widths) if all(isinstance(w, int) for w in widths) else None
    return None


def default_instances(modules, data):
    specs = data.get('instances') if isinstance(data, dict) else None
    if specs:
        available = {m.name: m for m in modules}
        return [dict(module=available[s['module']], instance=s['instance'],
                     parameters=s.get('parameters', {}), parameter_text='', ports={}) for s in specs]
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
    dimensions = (resolve_param_width(width, params),
                  resolve_param_width(detail.get('unpacked', ''), params))
    return (direction == 'interface', ' '.join(type_text.split()),
            *(re.sub(r'\s+', '', dim) for dim in dimensions))


def build_top(instances, top_name='soc_top', map_data=None, previous_top=None):
    """Resolve connections, declare actual nets, and check the resulting graph."""
    mapping = PortMap(map_data)
    rows, groups, checks = [], {}, []

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
                shared = name in auto_shared or (direction == 'interface' and len(named_ports[name]) == 1)
                prefix = instance if module_counts[module.name] > 1 else module.name.lower()
                expr = name if shared else f'{prefix}_{name}'
                # An explicitly named consumer also connects to the default producer name.
                if direction == 'output' and name in explicit_targets:
                    expr = name
            detail = dict(module.details[name])
            resolved = resolve_param_width(width, params)
            detail['unpacked'] = resolve_param_width(detail.get('unpacked', ''), params)
            built_in = re.fullmatch(r'(?:(?:wire|reg|logic|var)\s*)?(?:(?:signed|unsigned)\s*)?', detail['type'])
            bits = bit_width(resolved + detail.get('unpacked', '')) if built_in and direction != 'interface' else None
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
            old[n] = dict(direction=d, width=w, bits=bit_width(w), detail=previous_top.details[n])
    signals = {}
    for base, entries in groups.items():
        interface = [r for r in entries if r['direction'] == 'interface']
        if interface:
            types = {r['detail']['type'].split('.')[0] for r in interface}
            if len(types) != 1 or len(interface) != len(entries):
                raise ValueError(f'incompatible interface connection: {base}')
            signals[base] = dict(direction='interface', width='', bits=None, detail={'type': next(iter(types))})
            continue
        drivers = [r for r in entries if r['direction'] in ('output', 'inout')]
        source = next((r for r in drivers if r['direction'] == 'output'), entries[0])
        direction = 'inout' if any(r['direction'] == 'inout' for r in entries) else (
            '' if drivers and any(r['direction'] == 'input' for r in entries) else
            'output' if drivers else 'input')
        width, bits = source['width'], source['bits']
        # Part selections describe a wider parent net, not an implicit truncation.
        slices = [re.search(r'\[\s*(\d+)\s*(?::\s*(\d+)\s*)?\]', r['signal']) for r in entries]
        high = max((max(int(s[1]), int(s[2] or s[1])) for s in slices if s), default=-1)
        if high >= 0 and (not width or bits is None or high + 1 > bits):
            width, bits = f'[{high}:0]', high + 1
        signals[base] = dict(direction=direction, width=width, bits=bits, detail=source['detail'])
        for i, driver in enumerate(drivers):
            for other in drivers[i + 1:]:
                def interval(row):
                    m = re.search(r'\[(\d+)(?::(\d+))?\]', row['signal'].replace(' ', ''))
                    return (min(int(m[1]), int(m[2] or m[1])), max(int(m[1]), int(m[2] or m[1]))) if m else (0, (bits or 1) - 1)
                a, b = interval(driver), interval(other)
                if max(a[0], b[0]) <= min(a[1], b[1]):
                    warn('multiple-driver', f'{base} has multiple drivers: {driver["key"]}, {other["key"]}', [driver['key'], other['key']])
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
    domains = {}
    for inst in instances:
        clocks = [r['signal'].strip() for r in rows if r['instance'] == inst['instance'] and
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
            clock_row = next((r for r in rows if r['instance'] == row['instance'] and r['port'] == clock), None)
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
    metadata = {'version': 1, 'port_map': mapping.data,
                'instances': {i['instance']: dict(i['module'].metadata(), overrides=i['parameters']) for i in instances}}
    lines = ['// Generated by soc_integrate.py; named connection expressions survive update.',
             '// soc-integrate: ' + json.dumps(metadata, separators=(',', ':')),
             f'module {top_name} (']
    ports, internal = [], []
    # Preserve the actual previous header order, even for dependencies that were
    # discovered late through manual expressions. New external ports follow it.
    signal_order = [name for name in old if name in signals]
    signal_order += [name for name in signals if name not in old]
    for name in signal_order:
        signal = signals[name]
        d, w, detail = signal['direction'], signal['width'], signal['detail']
        if d == 'interface':
            internal.append(f'    {detail["type"]} {name} ();')
        elif d:
            ports.append('    ' + declaration(d, w, name, detail))
        else:
            internal.append('    ' + declaration('', w, name, detail) + ';')
    lines += [',\n'.join(ports), ');'] + internal
    for inst in instances:
        module = inst['module']
        params = inst.get('parameter_text', '')
        if not params and inst['parameters']:
            params = '#(' + ', '.join(f'.{k}({v})' for k, v in inst['parameters'].items()) + ')'
        lines.append(f'    {module.name} {params} {inst["instance"]} (')
        connections = [row for row in rows if row['instance'] == inst['instance']]
        for index, row in enumerate(connections):
            empty = not row['signal'].strip()
            if empty:
                lines.append('        // verilator lint_off PINCONNECTEMPTY')
            comma = ',' if index < len(connections) - 1 else ''
            lines.append(f'        .{row["port"]}({row["signal"]}){comma}')
            if empty:
                lines.append('        // verilator lint_on PINCONNECTEMPTY')
        lines.append('    );')
    lines.append('endmodule')
    shared = {net: [r['key'] for r in entries] for net, entries in groups.items() if len(entries) > 1}
    return '\n'.join(lines) + '\n', rows, checks, shared, metadata


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
    interface_types = {p.get('type', '').split('.')[0] for m in meta.get('instances', {}).values()
                       for p in m.get('ports', []) if p['direction'] == 'interface'}
    data['instances'] = [i for i in instances if i['module'] not in interface_types]
    data['shared_signals'] = {k: v for k, v in shared.items() if len(v) > 1}
    return data


def port_changes(instances, meta):
    messages, checks = [], []
    for inst in instances:
        module, name = inst['module'], inst['instance']
        old_meta = meta.get('instances', {}).get(name, {})
        old = {p['name']: p for p in old_meta.get('ports', [])}
        previous = set(inst['ports'])
        current = {n: (d, w) for d, w, n in module.ports}
        for port in sorted(current.keys() - previous):
            messages.append(f'[NEW] {name}.{port}')
        for port in sorted(previous - current.keys()):
            messages.append(f'[DEL] {name}.{port}')
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
    return messages, checks


def load_update(target, files, options):
    config = {}
    if str(target).endswith('.json'):
        config = json.loads(Path(target).read_text())
        target = config['output_file']
        files = files or [entry['file'] for entry in config['modules']]
    name, parsed, meta, top = parse_top(target)
    if not files:
        files = list(dict.fromkeys(v['file'] for v in meta.get('instances', {}).values() if v.get('file')))
    available = {}
    for file in files:
        available.update((m.name, m) for m in extract_modules(file, **options))
    interface_types = {m.details[n]['type'].split('.')[0] for m in available.values()
                       for d, _, n in m.ports if d == 'interface'}
    instances = []
    for inst in parsed:
        if inst['module'] not in available:
            # Native interface declarations are retained by the connected child ports.
            if inst['module'] in interface_types and not inst['ports'] and not inst['parameter_text']:
                continue
            raise ValueError(f'{target}:1: current RTL required for module {inst["module"]}; supply --files')
        inst['module'] = available[inst['module']]
        instances.append(inst)
    if not instances:
        raise ValueError(f'{target}:1: no supported module instances found')
    if not meta and config.get('port_snapshot'):
        meta['instances'] = {i['instance']: {'ports': config['port_snapshot'].get(i['module'].name, [])} for i in instances}
    return target, name, instances, meta, top, config


def report_checks(checks):
    for check in checks:
        print(f'Warning [{check["code"]}]: {check["message"]}')
    print(f'Checks: {len(checks)} warning(s)')


def export_csv(module, filepath):
    with open(filepath, 'w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['Direction', 'Width', 'Port Name'])
        writer.writerows(module.ports)


def emit_result(args, instances, name, data, previous=None, changes=None, extra_checks=()):
    code, rows, checks, shared, _ = build_top(instances, name, data, previous)
    checks = list(extra_checks) + checks
    report_checks(checks)
    if args.strict and checks:
        raise ValueError('strict check failed; no output written')
    if args.output:
        write_text(args.output, code)
        print(f'Top written: {args.output}')
    else:
        print(code, end='')
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
    return messages


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    subs = cli.add_subparsers(dest='command', required=True)
    for command in ('extract', 'instantiate', 'wrap', 'csv', 'snapshot', 'diff', 'check', 'extract-map', 'integrate', 'update', 'remove'):
        sub = subs.add_parser(command)
        sub.add_argument('-I', '--include-dir', dest='include_dirs', action='append', default=[])
        sub.add_argument('-D', '--define', dest='defines', action='append', default=[])
        sub.add_argument('--strict', action='store_true', help='Warnings fail without writing outputs')
        sub.add_argument('-m', '--module')
        sub.add_argument('-n', '--name')
        sub.add_argument('-o', '--output')
        if command == 'integrate':
            sub.add_argument('files', nargs='+')
        else:
            sub.add_argument('file')
        if command in ('integrate', 'update', 'remove'):
            sub.add_argument('--map')
            sub.add_argument('--csv', action='store_true', help='Opt in to review CSV')
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
    options = dict(include_dirs=args.include_dirs, defines=args.defines)
    if getattr(args, 'no_config', False):
        args.track = False
    try:
        if args.command == 'integrate':
            modules = [select_module(file, **options) for file in args.files]
            data = json.loads(Path(args.map).read_text()) if args.map else {}
            emit_result(args, default_instances(modules, data), args.name or 'soc_top', data)
        elif args.command in ('update', 'remove') or (args.command in ('diff', 'check') and not args.snapshot):
            target, name, instances, meta, top, config = load_update(args.file, args.files, options)
            if args.command == 'remove':
                instances = [i for i in instances if i['module'].name != args.module_name]
            messages, checks = port_changes(instances, meta)
            for message in messages:
                print(message)
            if args.command == 'diff':
                report_checks(checks)
                if args.strict and checks:
                    return 1
            elif args.command == 'check':
                _, _, graph_checks, _, _ = build_top(instances, name, meta.get('port_map', {}), top)
                report_checks(checks + graph_checks)
                if args.strict and (checks or graph_checks):
                    return 1
            else:
                data = json.loads(Path(args.map).read_text()) if args.map else meta.get('port_map', config.get('port_map', {'mappings': config.get('mappings', {})}))
                args.output = args.output or target
                emit_result(args, instances, args.name or name, data, top, messages, checks)
        elif args.command == 'extract-map':
            data = extract_map_from_top(args.file, args.expand)
            if args.verify:
                available = {m.name: m for f in args.verify for m in extract_modules(f, **options)}
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
                text = generate_wrapper(module, args.name)
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
                messages = compare_ports(module, json.loads(Path(args.snapshot).read_text()))
                print('\n'.join(messages) if messages else 'No port changes')
                return 1 if messages and args.command == 'check' else 0
            if args.output:
                write_text(args.output, text)
            else:
                print(text, end='' if text.endswith('\n') else '\n')
        return 0
    except (ValueError, OSError, KeyError, re.error) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
