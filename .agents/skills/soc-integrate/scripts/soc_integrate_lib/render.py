"""Port declarations, instances and wrappers."""
import json
import re
from .common import resolve_param_width

VARIABLE_STORAGE = re.compile('\\b(?:reg|var)\\b')


def declaration(direction, width, name, detail=None):
    detail = detail or {}
    type_text = detail.get('declaration_type', detail.get('type', ''))
    # Storage in the child does not imply variable storage in the parent.
    type_text = VARIABLE_STORAGE.sub('wire', type_text)
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
    from .update import compact_metadata
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
