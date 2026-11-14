"""Compilation-unit preprocessing and package dependency ordering."""
import re
import shutil
import subprocess
from pathlib import Path
from .common import IDENT, line_number, uncomment

MISSING_INCLUDE = re.compile("%Error: (.*?):(\\d+):\\d+: Cannot find include file: '([^']+)'")
LINE_DIRECTIVE = re.compile('\\s*`line\\s+(\\d+)\\s+"([^"\\n]+)"\\s+(\\d+)')
QUOTED_STRING = re.compile('"(?:\\\\.|[^"\\\\])*"')
PACKAGE_DECLARATION = re.compile('\\bpackage\\s+(?:(?:automatic|static)\\s+)?([A-Za-z_][\\w$]*)\\s*;')
PREPROCESSOR_DIRECTIVE = re.compile('\\s*`(include|define|undef|ifdef|ifndef|elsif|else|endif)\\b(.*)')
PACKAGE_END = re.compile('\\bendpackage\\b')
CLASS_DECLARATION = re.compile('\\bclass\\s+([A-Za-z_][\\w$]*)')
TYPEDEF_DECLARATION = re.compile('\\btypedef\\b[^;]*?\\b([A-Za-z_][\\w$]*)\\s*;')
PACKAGE_REFERENCE = re.compile('(?<![\\w$:])([A-Za-z_][\\w$]*)\\s*::')
NON_SEMANTIC_DIRECTIVE = re.compile('\\s*`(?:timescale|default_nettype|celldefine|endcelldefine)\\b')
FUNCTION_MACRO_CALL = re.compile('`([A-Za-z_][\\w$]*)\\s*\\(')
MACRO_DEFINITION = re.compile('([A-Za-z_][\\w$]*)(?:\\s+(.*))?')
FUNCTION_MACRO_DEFINE = re.compile('[A-Za-z_][\\w$]*\\(')
MACRO_REFERENCE = re.compile('`([A-Za-z_][\\w$]*)')
IDENTIFIER = re.compile('[A-Za-z_][\\w$]*')
INCLUDE_PATH = re.compile('"([^"]+)"')


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
            directive = PREPROCESSOR_DIRECTIVE.match(line)
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
                    match = MACRO_DEFINITION.fullmatch(arg)
                    if FUNCTION_MACRO_DEFINE.match(arg):
                        name = IDENTIFIER.match(arg)[0]
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
                    match = INCLUDE_PATH.fullmatch(arg)
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
                if NON_SEMANTIC_DIRECTIVE.match(line):
                    result.append('\n')
                else:
                    for name in FUNCTION_MACRO_CALL.findall(line):
                        if name not in self.macros:
                            self.functions.add(name)
                    for _ in range(32):
                        names = [n for n in MACRO_REFERENCE.findall(line) if n not in self.functions]
                        if not names:
                            break
                        for name in names:
                            if name not in self.macros:
                                raise ValueError(f'{file}:{number}: undefined macro `{name}')
                        line = MACRO_REFERENCE.sub(lambda m: m[0] if m[1] in self.functions else self.macros[m[1]], line)
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


def preprocess_sources(files, include_dirs=(), defines=(), packages=()):
    """One ordered compilation unit, with per-root text and real-source locations."""
    roots = list(dict.fromkeys(str(Path(p).resolve()) for p in list(packages) + list(files)
                               if Path(p).suffix.lower() != '.xml'))
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
        match = MISSING_INCLUDE.search(error)
        if match:
            error = f'{match[1]}:{match[2]}: missing include "{match[3]}"'
        if 'Define or directive not defined' in error:
            error = 'undefined macro: ' + error
        raise ValueError(error)
    chunks = {source: ([], []) for source in roots}
    root, source, number = roots[0], roots[0], 1
    for line in result.stdout.splitlines(keepends=True):
        directive = LINE_DIRECTIVE.match(line)
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
        scan = QUOTED_STRING.sub(lambda m: ' ' * len(m[0]), scan)
        scopes = []
        for match in PACKAGE_DECLARATION.finditer(scan):
            location = locations[line_number(text, match.start()) - 1]
            if match[1] in declarations:
                source, line = location
                raise ValueError(f'{source}:{line}: duplicate package {match[1]}')
            declarations[match[1]] = (path, location)
            ending = PACKAGE_END.search(scan[match.end():])
            scopes.append((match.start(), match.end() + ending.end() if ending else len(scan), match[1]))
            package_edges[match[1]] = {}
        # Classes and typedefs can also qualify names; they are not packages.
        local_types = set(CLASS_DECLARATION.findall(scan))
        local_types.update(TYPEDEF_DECLARATION.findall(scan))
        references[path] = [(m[1], locations[line_number(text, m.start()) - 1],
                             next((name for a, b, name in scopes if a <= m.start() < b), None))
                            for m in PACKAGE_REFERENCE.finditer(scan)
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
