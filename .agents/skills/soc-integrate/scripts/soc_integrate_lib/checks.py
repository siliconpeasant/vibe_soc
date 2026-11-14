"""Connection widths, domains and structured diagnostics."""
import json
import re
import sys
from .common import IDENT, balanced, bit_width, constant, resolve_param_width, split_port_items, uncomment

SINGLE_SELECTION = re.compile('\\s*[A-Za-z_][\\w$]*\\s*\\[([^\\[\\]]+)\\]\\s*')
INDEXED_SELECTION = re.compile('(.+?)\\s*([+-]):\\s*(.+)')
SIGNAL_EXPRESSION = re.compile('\\s*([A-Za-z_][\\w$]*)\\s*(?:\\[[^\\]]+\\]\\s*)*')
SIZED_LITERAL = re.compile("(\\d+)'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+")
FILL_LITERAL = re.compile("'[01xXzZ]")
UNSIZED_INTEGER = re.compile('\\d+')
DIMENSION = re.compile('\\[([^\\]]+)\\]')
BOUND_SEPARATOR = re.compile('(?<!:):(?!:)')
NET_STORAGE = re.compile('\\b(?:wire|reg|var)\\b')
VALUE_STORAGE = re.compile('\\b(?:wire|var|reg|logic|bit|signed|unsigned)\\b')
BUS_NAME = re.compile('^(?:tl_|axi_|apb_|ahb_)|_(?:req|rsp)(?:_|$)|h2d|d2h')
PACKED_DIMENSION = re.compile('\\[[^\\]]+\\]')
WHITESPACE = re.compile('\\s+')


def bus_like(name, type_text):
    value_type = VALUE_STORAGE.sub('', type_text).strip()
    return bool(value_type and '.' not in value_type or BUS_NAME.search(name))


def selection_interval(expr):
    match = SINGLE_SELECTION.fullmatch(uncomment(expr))
    if not match:
        return None
    selection = match[1]
    indexed = INDEXED_SELECTION.fullmatch(selection)
    if indexed:
        base, width = constant(indexed[1]), constant(indexed[3])
        if base is None or width is None:
            return None
        if width <= 0:
            raise ValueError(f'invalid indexed part-select width: {expr}')
        low, high = (base, base + width - 1) if indexed[2] == '+' else (base - width + 1, base)
    else:
        parts = BOUND_SEPARATOR.split(selection)
        values = [constant(p) for p in parts]
        if len(values) not in (1, 2) or None in values:
            return None
        low, high = min(values), max(values)
    if low < 0:
        raise ValueError(f'negative part-select index: {expr}')
    return low, high


def net_base(expr):
    match = SIGNAL_EXPRESSION.fullmatch(uncomment(expr))
    return match[1] if match else None


def literal_width(expr):
    match = SIZED_LITERAL.fullmatch(expr.strip())
    if match:
        return int(match[1])
    if FILL_LITERAL.fullmatch(expr.strip()):
        return 'fill'
    if UNSIZED_INTEGER.fullmatch(expr.strip()):
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
        dims = ''.join(PACKED_DIMENSION.findall(expr))
        interval = selection_interval(expr)
        return interval[1] - interval[0] + 1 if interval else (None if dims else signals.get(base, {}).get('bits'))
    if expr.startswith('{') and expr.endswith('}'):
        widths = [expression_width(x, signals) for x in split_port_items(expr[1:-1])]
        return sum(widths) if all(isinstance(w, int) for w in widths) else None
    return None


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
        type_text = NET_STORAGE.sub('', type_text)
        type_text = ' '.join(type_text.split())
        if type_text in ('', 'signed', 'unsigned'):
            type_text = 'logic ' + type_text
        if type_text.strip() in ('logic', 'logic unsigned'):
            type_text = 'logic'
    unpacked = resolve_param_width(detail.get('unpacked', ''), params)
    if direction == 'interface':
        unpacked = repr(interface_shape(unpacked))
    dimensions = (resolve_param_width(width, params), unpacked)
    return (direction == 'interface', ' '.join(type_text.split()),
            *(WHITESPACE.sub('', dim) for dim in dimensions))


def interface_shape(dimensions):
    """Canonical bounds for equivalent size/range unpacked declarations."""
    shape = []
    for dimension in DIMENSION.findall(dimensions):
        bounds = [constant(v) for v in BOUND_SEPARATOR.split(dimension)]
        if None in bounds:
            shape.append(WHITESPACE.sub('', dimension))
        else:
            shape.append((0, bounds[0] - 1) if len(bounds) == 1 else tuple(bounds))
    return tuple(shape)


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


def report_checks(checks):
    for check in checks:
        print(f'Warning [{check["code"]}]: {check["message"]}', file=sys.stderr)
    print(f'Checks: {len(checks)} warning(s)', file=sys.stderr)


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
