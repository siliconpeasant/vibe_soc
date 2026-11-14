"""Vendor-scoped lint collateral."""
import json
from pathlib import Path



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
    # UNOPTFLAT is a performance diagnostic outside Verilator's lint group.
    # Keep it source-scoped too, as OpenTitan's FIFO/arbiter graphs trigger it.
    for source in rules:
        lines += ['lint_off -file ' + json.dumps(source),
                  'lint_off -rule UNOPTFLAT -file ' + json.dumps(source)]
    manifest = [json.dumps(p) for p in packages]
    manifest += [json.dumps('-I' + str(Path(d).resolve())) for d in args.include_dirs]
    manifest += [json.dumps('-D' + d) for d in args.defines]
    manifest += ['-y ' + json.dumps(str(Path(d).resolve())) for d in args.library_dirs]
    manifest += [json.dumps(p) for p in sources if p not in packages]
    manifest.append(json.dumps(str(top)))
    return config, '\n'.join(lines) + '\n', filelist, '\n'.join(manifest) + '\n'
