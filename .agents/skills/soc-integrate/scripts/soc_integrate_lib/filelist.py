"""soc-build discovery adapter plus integration-aware source ordering."""
import contextlib
import importlib.util
import io
import json
import re
import tempfile
from pathlib import Path

from .common import uncomment, write_text
from .preprocess import order_packages, preprocess_sources
from .update import read_metadata

PACKAGE = re.compile(r'\bpackage\s+(?:(?:automatic|static)\s+)?[A-Za-z_][\w$]*\s*;')
INTERFACE = re.compile(r'\binterface\s+[A-Za-z_][\w$]*')
STRINGS = re.compile(r'"(?:\\.|[^"\\])*"')


def discover_sources(search_path, recursive=True):
    """Delegate directory scanning and its extension/dedup rules to soc-build."""
    script = Path(__file__).resolve().parents[3] / 'soc-build/scripts/soc_gen_flist.py'
    if not script.is_file():
        raise ValueError(f'soc-build filelist generator is required: {script}')
    spec = importlib.util.spec_from_file_location('soc_build_gen_flist', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='soc-integrate-flist-') as directory:
        manifest = Path(directory) / 'sources.f'
        with contextlib.redirect_stdout(io.StringIO()):
            status = module.gen_flist(search_path, str(manifest), recursive, ['*.v', '*.sv'])
        if status:
            raise ValueError(f'soc-build discovery failed for {search_path}')
        return [line for line in manifest.read_text().splitlines() if line and not line.startswith('#')]


def filelist_text(top_file, output, module_files=(), search_path='', recursive=True,
                  include_dirs=(), defines=(), packages=(), library_dirs=()):
    """Absolute soc_flist-compatible sources/options; packages precede consumers.

    Explicit module_files replaces tracked child sources. Discovery is optional;
    a tracked top alone is sufficient for the normal integration case.
    """
    top = str(Path(top_file).resolve())
    sources = list(module_files)
    if not sources:
        metadata = read_metadata(Path(top).read_text(), top)
        sources = [p for saved in metadata.get('instances', {}).values()
                   for p in [saved.get('file')] + [d.get('file') for d in saved.get('interfaces', {}).values()] if p]
    if search_path:
        sources += discover_sources(search_path, recursive)
    sources = list(dict.fromkeys(str(Path(p).resolve()) for p in sources + list(packages) if str(Path(p).resolve()) != top))
    if any(Path(p).suffix.lower() == '.xml' for p in sources):
        raise ValueError('IP-XACT describes interfaces only; supply HDL implementations via --files for a runnable filelist')
    prepared = preprocess_sources(sources + [top], include_dirs, defines)
    package_files, interface_files = list(packages), []
    for path, (text, _) in prepared.items():
        scan = STRINGS.sub('', uncomment(text))
        if path != top and PACKAGE.search(scan):
            package_files.append(path)
        elif path != top and INTERFACE.search(scan):
            interface_files.append(path)
    package_files = order_packages(package_files, include_dirs, defines, sources + [top])
    ordered = list(dict.fromkeys(package_files + interface_files + sources + [top]))
    lines = [f'# Auto-generated filelist: {Path(output).name}', f'# Total files: {len(ordered)}']
    lines += [json.dumps('-I' + str(Path(p).resolve())) for p in include_dirs]
    lines += [json.dumps('-D' + value) for value in defines]
    lines += ['-y ' + json.dumps(str(Path(p).resolve())) for p in library_dirs]
    lines += [json.dumps(p) for p in ordered]
    return '\n'.join(lines) + '\n'


def generate_filelist(top_file, output='', **options):
    output = output or str(Path(top_file).with_suffix('.f'))
    text = filelist_text(top_file, output, **options)
    write_text(output, text)
    return Path(output)
