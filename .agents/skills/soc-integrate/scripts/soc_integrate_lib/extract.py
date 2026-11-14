"""Source extraction and compiler-assisted public type resolution."""
import json
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
import xml.etree.ElementTree as ET
from pathlib import Path
from .common import IDENT, constant, line_number
from .parse import parse_module
from .preprocess import order_packages, preprocess_sources
from .render import declaration

VERILATOR_VERSION = re.compile('Verilator (\\d+)\\.(\\d+)')
QUOTED_STRING = re.compile('"(?:\\\\.|[^"\\\\])*"')
DEFINITION_START = re.compile('\\b(module|interface)\\s+([A-Za-z_][\\w$]*)')
NON_NEWLINE = re.compile('[^\\n]')
DIMENSION = re.compile('\\[([^\\]]+)\\]')
UNSUPPORTED_OPTION = re.compile('(?:Invalid|Unknown|Unrecognized|Unsupported) (?:option|argument)', re.I)
SOURCE_DIAGNOSTIC = re.compile('^(.*?):(\\d+): (.*)', re.S)
BOUND_SEPARATOR = re.compile('(?<!:):(?!:)')


@lru_cache(maxsize=1)
def verilator_version():
    result = subprocess.run(['verilator', '--version'], capture_output=True, text=True, timeout=10)
    match = VERILATOR_VERSION.search(result.stdout)
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


def resolve_types(module, packages, include_dirs, defines, *, version_detector=None):
    """Resolve public-header probes with JSON, legacy XML, then symbolic text.

    A compiler syntax/type error is always fatal, never a reason to downgrade.
    Only unsupported AST options/formats fall back. Scratch is disposable.
    """
    with tempfile.TemporaryDirectory(prefix='soc-integrate-') as directory:
        root = Path(directory)
        header = root / (module.name + '.sv')
        dimension_names, bit_names = {}, {}
        localparams = ''.join(f'localparam {t} {n} = {v};\n' for n, v, t in module.localparams)
        for direction, width, name in module.ports:
            if direction == 'interface':
                continue
            bit_names[name] = f'__soc_integrate_bits_{len(bit_names)}'
            localparams += f'localparam integer {bit_names[name]} = $bits({name});\n'
            for field, dims in (('resolved_width', width), ('resolved_unpacked', module.details[name].get('unpacked', ''))):
                names = []
                for expr in DIMENSION.findall(dims):
                    pair = []
                    for bound in BOUND_SEPARATOR.split(expr):
                        identifier = f'__soc_integrate_dim_{len(dimension_names)}_{len(names)}_{len(pair)}'
                        localparams += f'localparam integer {identifier} = {bound};\n'
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
        header.write_text(origin + public_header + '\n' + localparams + 'endmodule\n')
        formats = ['json', 'xml'] if (version_detector or verilator_version)() >= (5, 32) else ['xml']
        for format_name in formats:
            json_format = format_name == 'json'
            command = ['verilator', '--' + format_name + '-only', '--prefix', 'Vports',
                       '--Mdir', str(root / 'obj'), '--top-module', module.name, '-Wno-fatal']
            if not json_format:
                command += ['--xml-output', str(root / 'ports.xml')]
            command += ['-I' + str(d) for d in include_dirs] + ['-D' + d for d in defines]
            result = subprocess.run(command + [str(p) for p in packages] + [str(header)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                if UNSUPPORTED_OPTION.search(result.stderr):
                    continue
                raise ValueError(f'{source_file}:{source_line}: Verilator header type resolution failed:\n{result.stderr.strip().replace(str(header), source_file)}')
            try:
                tree = json.loads((root / 'obj/Vports.tree.json').read_text()) if json_format else ET.parse(root / 'ports.xml')
                values = ast_constants(tree, module.name, json_format)
                if any(identifier not in values for identifier in bit_names.values()):
                    continue
            except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError):
                continue
            for name, identifier in bit_names.items():
                module.details[name]['bits'] = values[identifier]
            for (name, field), dimensions in dimension_names.items():
                if dimensions and all(values.get(n) is not None for pair in dimensions for n in pair):
                    module.details[name][field] = ''.join('[' + ':'.join(str(values[n]) for n in pair) + ']' for pair in dimensions)
            return


def extract_sources(files, include_dirs=(), defines=(), packages=()):
    packages = order_packages(packages, include_dirs, defines, files)
    prepared = preprocess_sources(files, include_dirs, defines, packages)
    return {str(file): extract_modules(file, include_dirs, defines, packages, prepared) for file in files}


DEFINITION_END = {'module': re.compile(r'\bendmodule\b'), 'interface': re.compile(r'\bendinterface\b')}


def extract_modules(filepath, include_dirs=(), defines=(), packages=(), prepared=None):
    if Path(filepath).suffix.lower() == '.xml':
        from .ipxact import import_component
        return [import_component(filepath)]
    standalone = prepared is None
    if standalone:
        packages = order_packages(packages, include_dirs, defines, [filepath])
    prepared = prepared if prepared is not None else preprocess_sources([filepath], include_dirs, defines, packages)
    text, locations = prepared[str(Path(filepath).resolve())]
    modules = []
    scan = QUOTED_STRING.sub(lambda m: NON_NEWLINE.sub(' ', m[0]), text)
    definition_end = 0
    for match in DEFINITION_START.finditer(scan):
        if match.start() < definition_end:
            continue
        end = DEFINITION_END[match[1]].search(scan[match.end():])
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
            loc = SOURCE_DIAGNOSTIC.match(str(exc))
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
        if packages and module.kind == 'module' and shutil.which('verilator'):
            resolve_types(module, packages, include_dirs, defines)
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
