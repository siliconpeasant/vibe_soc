"""Conservative module and port parsing."""
import re
from .checks import bus_like
from .common import IDENT, balanced, fail, line_number, resolve_param_width, split_port_items, uncomment

PORT_DIRECTION = re.compile('(input|output|inout)\\b\\s*')
PORT_FIELDS = re.compile('(.*?)\\b([A-Za-z_][\\w$]*)\\s*((?:\\[[^\\]]+\\]\\s*)*)', re.S)
QUOTED_STRING = re.compile('"(?:\\\\.|[^"\\\\])*"')
MACRO_REFERENCE = re.compile('`([A-Za-z_][\\w$]*)')
PARAMETER_FIELDS = re.compile('(.*?)\\b([A-Za-z_][\\w$]*)\\s*((?:\\[[^\\]]+\\]\\s*)*)=\\s*(.+)', re.S)
TYPE_KEYWORD = re.compile('\\btype\\b')
OPEN_PAREN = re.compile('\\s*\\(')
IMPORT_START = re.compile('import\\b')
PARAMETER_STATEMENT = re.compile('\\b(parameter|localparam)\\s+([^;]+);')
IMPORT_STATEMENT = re.compile('\\bimport\\s+([^;]+);')
BARE_PORT = re.compile('[A-Za-z_][\\w$]*\\s*(?:\\[[^\\]]+\\]\\s*)*')
PORT_NAME_DIMS = re.compile('([A-Za-z_][\\w$]*)\\s*((?:\\[[^\\]]+\\]\\s*)*)')
PACKED_DIMENSION = re.compile('\\[[^\\]]+\\]')
INTERFACE_TYPE = re.compile('[A-Za-z_][\\w$]*(?:\\.[A-Za-z_][\\w$]*)?')
MODPORT_STATEMENT = re.compile('\\bmodport\\s+([^;]+);')
DIRECTION_STATEMENT = re.compile('\\b(input|output|inout)\\b([^;]*);')
NAMED_TYPE = re.compile('((?:(?:wire|var)\\s+)?)([A-Za-z_][\\w$]*)(\\s+(?:signed|unsigned))?')
LOCATION_PREFIX = re.compile('^.*?:\\d+: ', re.S)
PARAMETER_PREFIX = re.compile('^\\s*(?:parameter|localparam)\\b\\s*')
VALUE_TYPE = re.compile('(?:(?:wire|reg|logic|var)\\s*)?(?:(?:signed|unsigned)\\s*)?|(?:(?:wire|var)\\s+)?[A-Za-z_][\\w$]*(?:::[A-Za-z_][\\w$]*)*(?:\\s+(?:signed|unsigned))?')
STORAGE_STATEMENT = re.compile('\\b(reg|logic)\\s+([^;]+);')
MODPORT_FIELDS = re.compile('\\s*([A-Za-z_][\\w$]*)\\s*\\((.*)\\)\\s*', re.S)
IDENTIFIER = re.compile('[A-Za-z_][\\w$]*')
DIRECTION_KEYWORD = re.compile('\\b(input|output|inout)\\b')


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
        self.bus_interfaces = []

    def metadata(self):
        data = {'module_name': self.name, 'file': self.file, 'kind': self.kind,
                'interfaces': self.interfaces,
                'modports': self.modports,
                'params': self.params, 'localparams': self.localparams,
                'imports': self.imports, 'param_dims': self.param_dims,
                'ports': [dict(direction=d, width=w, name=n, **self.details.get(n, {}))
                          for d, w, n in self.ports]}
        if self.bus_interfaces:
            data['bus_interfaces'] = self.bus_interfaces
        return data


def parse_parameters(section, module, local=False):
    inherited = ''
    for item in split_port_items(section):
        item = PARAMETER_PREFIX.sub('', item).strip()
        match = PARAMETER_FIELDS.fullmatch(item)
        if not match:
            raise ValueError(f'unsupported parameter declaration: {item}')
        type_text, name, dims, value = match.groups()
        module.param_dims[name] = dims.strip()
        inherited = type_text.strip() or inherited
        if any(p[0] == name for p in module.params + module.localparams):
            raise ValueError(f'duplicate parameter: {name}')
        if TYPE_KEYWORD.search(inherited):
            raise ValueError(f'unsupported type parameter: {item}')
        (module.localparams if local else module.params).append((name, value.strip(), inherited))


def parse_port(item, inherited=None):
    item = item.strip()
    direction = PORT_DIRECTION.match(item)
    if direction:
        kind = direction[1]
        rest = item[direction.end():]
    elif inherited and BARE_PORT.fullmatch(item):
        kind, type_text, width = inherited
        rest = item
        match = PORT_NAME_DIMS.fullmatch(rest)
        return (kind, width, match[1]), {'type': type_text, 'unpacked': match[2].strip()}, inherited
    else:
        kind, rest = 'interface', item
    match = PORT_FIELDS.fullmatch(rest)
    if not match:
        raise ValueError(f'unsupported port declaration: {item}')
    prefix, name, unpacked = match.groups()
    width = resolve_param_width(''.join(PACKED_DIMENSION.findall(prefix)))
    type_text = PACKED_DIMENSION.sub('', prefix).strip()
    if kind == 'interface' and ('::' in type_text or type_text.endswith('_t')):
        kind = 'input'  # Implicit direction on a clearly identified value type.
    if kind == 'interface':
        if not INTERFACE_TYPE.fullmatch(type_text):
            raise ValueError(f'unsupported interface port: {item}')
    elif type_text and not VALUE_TYPE.fullmatch(type_text):
        raise ValueError(f'unsupported port type: {item}')
    detail = {'type': type_text, 'unpacked': resolve_param_width(unpacked.strip())}
    return (kind, width, name), detail, (kind, type_text, width)


def check_header_macros(section, file, text, start):
    scan = QUOTED_STRING.sub(lambda m: ' ' * len(m[0]), section)
    macro = MACRO_REFERENCE.search(scan)
    if macro:
        if OPEN_PAREN.match(scan[macro.end():]):
            construct = f'function-like macro `{macro[1]} in port/parameter header; install verilator'
        else:
            construct = f'undefined macro `{macro[1]} in port/parameter header; supply -D or an include'
        fail(file, text, start + macro.start(), construct)


MODULE_HEADER = re.compile(r'\s*(module|interface)\s+(' + IDENT + r')\b\s*')
TRAILING_IDENTIFIER = re.compile(r'\b(' + IDENT + r')\b(?=\s*(?:\[|$))')


def parse_module(name, content, file='<text>'):
    module = VerilogModule(name)
    module.file = str(file)
    text = uncomment(content)
    match = MODULE_HEADER.match(text)
    if not match or match[2] != name:
        fail(file, text, 0, 'module header')
    module.kind = match[1]
    pos = match.end()
    try:
        import_start = pos
        while IMPORT_START.match(text[pos:]):
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
            for decl in MODPORT_STATEMENT.finditer(body):
                for item in split_port_items(decl[1]):
                    modport = MODPORT_FIELDS.fullmatch(item)
                    if modport:
                        module.modports[modport[1]] = sorted(set(DIRECTION_KEYWORD.findall(modport[2])))
        for param in PARAMETER_STATEMENT.finditer(body):
            parse_parameters(param[2], module, param[1] == 'localparam')
        items = split_port_items(section)
        non_ansi = bool(items) and all(IDENTIFIER.fullmatch(p.strip()) for p in items)
        inherited = None
        if non_ansi:
            declared = {}
            for decl in DIRECTION_STATEMENT.finditer(body):
                inherited = None
                for item in split_port_items(decl[0][:-1]):
                    port, detail, inherited = parse_port(item, inherited)
                    if port[2] in declared:
                        raise ValueError(f'duplicate port declaration: {port[2]}')
                    name_match = next(m for m in TRAILING_IDENTIFIER.finditer(item) if m[1] == port[2])
                    detail['line'] = line_number(text, pos + 1 + decl.start() + decl[0].find(item) + name_match.start())
                    declared[port[2]] = (port, detail)
            for item in items:
                name = item.strip()
                if name not in declared:
                    raise ValueError(f'non-ANSI port without direction declaration: {name}')
                port, detail = declared.pop(name)
                # Merge later storage declarations without changing header order.
                for redecl in STORAGE_STATEMENT.finditer(body):
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
        imports = IMPORT_STATEMENT.findall(module.imports)
        imported = [entry.strip() for group in imports for entry in group.split(',')]
        wildcards = [entry[:-3] for entry in imported if entry.endswith('::*')]
        for direction, _, name in module.ports:
            if direction == 'interface':
                continue
            detail = module.details[name]
            type_text = detail['type']
            named = NAMED_TYPE.fullmatch(type_text)
            if not named or not bus_like('', type_text):
                continue
            explicit = [entry for entry in imported if entry.endswith('::' + named[2])]
            qualified = explicit[0] if len(explicit) == 1 else (wildcards[0] + '::' + named[2] if len(wildcards) == 1 else None)
            if not qualified and len(wildcards) > 1:
                raise ValueError(f'{file}:{detail["line"]}: unsupported unqualified port type {named[2]} with multiple wildcard imports; use package::type')
            if qualified:
                detail['declaration_type'] = (named[1] or '') + qualified + (named[3] or '')
        return module
    except (ValueError, IndexError) as exc:
        if LOCATION_PREFIX.match(str(exc)):
            raise
        fail(file, text, min(pos, len(text)), str(exc))
