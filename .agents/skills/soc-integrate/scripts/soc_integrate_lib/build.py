"""Connection graph and generated top construction."""
import json
import re
from .checks import bus_like, expression_width, interface_array_checks, interface_shape, literal_width, net_base, port_signature, selection_interval, stale_map_checks
from .common import IDENT, bit_width, constant, resolve_param_width, uncomment
from .portmap import PortMap
from .render import declaration
from .update import compact_metadata

DIMENSION = re.compile('\\[([^\\]]+)\\]')
CONSTANT_TOKEN = re.compile("(?:\\d+)?'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|'[01xXzZ]|\\$[A-Za-z_][\\w$]*")
IDENTIFIER_TOKEN = re.compile('\\b[A-Za-z_][\\w$]*\\b')
VALUE_STORAGE = re.compile('(?:(?:wire|reg|logic|var)\\s*)?(?:(?:signed|unsigned)\\s*)?')
IDENTIFIER = re.compile('[A-Za-z_][\\w$]*')
CLOCK_NAME = re.compile('(?:clk(?:_\\w+)?|\\w+_clk(?:_i|_o)?)')


def default_instances(modules, data):
    modules = [m for m in modules if m.kind == 'module']
    specs = data.get('instances') if isinstance(data, dict) else None
    if specs:
        available = {m.name: m for m in modules}
        for spec in specs:
            if spec['module'] not in available:
                raise ValueError(f"port map references unknown module/instance '{spec['module']}' (known: {', '.join(sorted(available))})")
        return [dict(module=available[s['module']], instance=s['instance'],
                     parameters=s.get('parameters', {}), parameter_text='', ports={}) for s in specs]
    return [dict(module=m, instance=f'u_{m.name.lower()}', parameters={}, parameter_text='', ports={}) for m in modules]


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
        bounds = DIMENSION.fullmatch(unpacked)
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


def build_top(instances, top_name='soc_top', map_data=None, previous_top=None, top_file=None):
    """Resolve connections, declare actual nets, and check the resulting graph."""
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
            resolved = detail.get('resolved_width', resolve_param_width(width, params)) if not inst['parameters'] else resolve_param_width(width, params)
            detail['unpacked'] = detail.get('resolved_unpacked', resolve_param_width(detail.get('unpacked', ''), params)) if not inst['parameters'] else resolve_param_width(detail.get('unpacked', ''), params)
            built_in = VALUE_STORAGE.fullmatch(detail['type'])
            bits = bit_width(resolved, detail.get('unpacked', '')) if built_in and direction != 'interface' else detail.get('bits')
            if inst['parameters'] and not built_in:
                bits = None  # Elaborated defaults cannot describe arbitrary overrides.
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
        source = next((r for r in drivers if r['direction'] == 'output'), entries[0])
        direction = 'inout' if any(r['direction'] == 'inout' for r in entries) else (
            '' if drivers and any(r['direction'] == 'input' for r in entries) else
            'output' if drivers else 'input')
        width, bits = source['width'], source['bits']
        # Part selections describe a wider parent net, not an implicit truncation.
        slices = [selection_interval(r['signal']) for r in entries]
        high = max((s[1] for s in slices if s), default=-1)
        if high >= 0 and (not width or bits is None or high + 1 > bits):
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
            if not IDENTIFIER.fullmatch(expr):
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
        custom_names = set(IDENTIFIER.findall(uncomment(custom)))
        for name, signal in old.items():
            if name in custom_names:
                signals.setdefault(name, signal)
    # General input expressions may reference old top inputs; retain their declarations.
    for row in rows:
        if net_base(row['signal']) or literal_width(row['signal']) is not None or not row['signal'].strip():
            continue
        expression = CONSTANT_TOKEN.sub('', uncomment(row['signal']))
        dependencies = IDENTIFIER_TOKEN.findall(expression)
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
                  CLOCK_NAME.fullmatch(r['port'])]
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
