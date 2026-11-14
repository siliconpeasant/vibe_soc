#!/usr/bin/env python3
"""MCP transport for the stdlib SoC interface and integration CLI."""
import argparse
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN_ROOT / 'scripts'))
from mcp_runtime import run_python

SCRIPT = Path(__file__).parent / 'scripts' / 'soc_integrate.py'
mcp = FastMCP(name='soc-integrate', instructions='Extract, connect, check and refresh RTL interfaces.')


def _call(command, args, include_dirs=None, defines=None, strict=False, packages=None, library_dirs=None):
    for directory in include_dirs or []:
        args += ['-I', directory]
    for define in defines or []:
        args += ['-D', define]
    for package in packages or []:
        args += ['--package', package]
    for directory in library_dirs or []:
        args += ['-y', directory]
    if strict:
        args += ['--strict']
    return run_python(SCRIPT, command, *args)


def _options(**options):
    args = []
    for flag, value in options.items():
        if value:
            args += ['--' + flag.replace('_', '-'), value]
    return args


@mcp.tool()
def soc_extract(verilog_file: str, module_name: str = '', include_dirs: list[str] | None = None,
                defines: list[str] | None = None, packages: list[str] | None = None,
                library_dirs: list[str] | None = None) -> str:
    """Extract directions, symbolic widths, types, dimensions and parameter defaults.

    include_dirs searches `include files; defines contains NAME or NAME=value.
    packages lists package/typedef files in any order; dependencies are sorted.
    Width resolution prefers version-detected Verilator JSON, then XML, then text.
    Unsupported interface syntax reports source file, line and construct.

    Parameters: verilog_file, module_name, include_dirs, defines, packages, library_dirs
    """
    return _call('extract', [verilog_file] + _options(module=module_name), include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_instantiate(verilog_file: str, instance_name: str = '', module_name: str = '',
                    include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
                    library_dirs: list[str] | None = None) -> str:
    """Generate named whole-expression connections without implicit bus slicing.

    Parameters: verilog_file, instance_name, module_name, include_dirs, defines, packages, library_dirs
    """
    return _call('instantiate', [verilog_file] + _options(name=instance_name, module=module_name), include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_wrap(verilog_file: str, module_name: str = '', wrapper_name: str = '', output: str = '',
             include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
             library_dirs: list[str] | None = None) -> str:
    """Generate a passthrough wrapper preserving parameter and port type text.

    Parameters: verilog_file, module_name, wrapper_name, output, include_dirs, defines, packages, library_dirs
    """
    return _call('wrap', [verilog_file] + _options(module=module_name, name=wrapper_name, output=output), include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_csv(verilog_file: str, module_name: str = '', output: str = 'ports.csv',
            include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
            library_dirs: list[str] | None = None) -> str:
    """Explicitly export a module's ports as CSV; integration CSV is separately opt-in.

    Parameters: verilog_file, module_name, output, include_dirs, defines, packages, library_dirs
    """
    return _call('csv', [verilog_file] + _options(module=module_name, output=output), include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_integrate(module_files: list[str], top_name: str, output_file: str, port_map: str = '',
                  csv: bool = False, track: bool = False, strict: bool = False,
                  include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
                  lint_config: bool = False, library_dirs: list[str] | None = None,
                  vendor_dirs: list[str] | None = None, force: bool = False,
                  chip: bool = False, domains: str = '', irq_json: str = '', irq_header: str = '') -> str:
    """Generate a top and print width/driver/connectivity/heuristic CDC checks.

    Exact instance.port then legacy module.port keys override ordered regex/glob
    templates. interfaces configures concrete interface types, parameters, ports and arrays.
    lint_config emits vendor-scoped .vlt/.lint.f; generated top warnings stay fatal.
    csv opts into review CSV; track opts into .integrate.json (both default off).
    strict rejects warnings before writing outputs. CDC checks are structural hints.
    chip exposes only pads/top_ports and explicitly top domain nets; incomplete wiring fails.
    domains reads clock/reset JSON wiring only. irq_json/irq_header opt into IRQ tables.

    Parameters: module_files, top_name, output_file, port_map, csv, track, strict, include_dirs, defines, packages, lint_config, library_dirs, vendor_dirs, force, chip, domains, irq_json, irq_header
    """
    args = module_files + _options(name=top_name, output=output_file, map=port_map)
    if csv:
        args += ['--csv']
    if track:
        args += ['--track']
    if lint_config:
        args += ['--lint-config']
    for directory in library_dirs or []:
        args += ['-y', directory]
    if force:
        args += ['--force']
    if chip:
        args += ['--chip']
    args += _options(domains=domains, irq_json=irq_json, irq_header=irq_header)
    for directory in vendor_dirs or []:
        args += ['--vendor-dir', directory]
    return _call('integrate', args, include_dirs, defines, strict, packages)


@mcp.tool()
def soc_update(config_file: str = '', output: str = '', port_map: str = '', top_name: str = '',
               module_files: list[str] | None = None, top_file: str = '', csv: bool = False,
               track: bool = False, strict: bool = False, include_dirs: list[str] | None = None,
               defines: list[str] | None = None, packages: list[str] | None = None,
               lint_config: bool = False, library_dirs: list[str] | None = None,
               vendor_dirs: list[str] | None = None) -> str:
    """Refresh named instances from CURRENT RTL, preserving manual expressions verbatim.

    Pass top_file and module_files for JSON-free update. config_file also accepts
    a top path or legacy .integrate.json. Embedded v1/v2 prior-port comments permit
    width/direction change reports; JSON is optional. New ports follow map/shared
    rules; deleted ports disappear. Unmanaged user text is preserved verbatim.
    csv, track and lint_config are independently opt-in.

    Parameters: config_file, output, port_map, top_name, module_files, top_file, csv, track, strict, include_dirs, defines, packages, lint_config, library_dirs, vendor_dirs
    """
    target = top_file or config_file
    if not target:
        raise ValueError('top_file or config_file is required')
    args = [target] + _options(output=output, map=port_map, name=top_name)
    if module_files:
        args += ['--files'] + module_files
    if csv:
        args += ['--csv']
    if track:
        args += ['--track']
    if lint_config:
        args += ['--lint-config']
    for directory in library_dirs or []:
        args += ['-y', directory]
    for directory in vendor_dirs or []:
        args += ['--vendor-dir', directory]
    return _call('update', args, include_dirs, defines, strict, packages)


@mcp.tool()
def soc_extract_map(top_file: str, output: str = '', verify_modules: list[str] | None = None,
                    expand: bool = False, include_dirs: list[str] | None = None,
                    defines: list[str] | None = None, packages: list[str] | None = None,
                    library_dirs: list[str] | None = None) -> str:
    """Extract named connections from the top without JSON; retain original templates.

    expand explicitly materializes every instance.port mapping. Manual overrides
    are exact keys; template rules and their order otherwise survive round trips.

    Parameters: top_file, output, verify_modules, expand, include_dirs, defines, packages, library_dirs
    """
    args = [top_file] + _options(output=output)
    if verify_modules:
        args += ['--verify'] + verify_modules
    if expand:
        args += ['--expand']
    return _call('extract-map', args, include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_check(verilog_file: str, spec_file: str = '', module_name: str = '',
              module_files: list[str] | None = None, strict: bool = False,
              include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
              library_dirs: list[str] | None = None, chip: bool = False,
              domains: str = '', port_map: str = '') -> str:
    """Check a module against a port spec, or a top's graph against CURRENT RTL.

    With spec_file, missing/extra/modified ports fail. Without it, supply the top
    and module_files; report width, multiple-driver, unconnected and CDC warnings.
    strict makes graph warnings errors. This is not CDC or timing signoff.
    chip checks whitelist/completeness; domains/port_map supply declared wiring intent.

    Parameters: verilog_file, spec_file, module_name, module_files, strict, include_dirs, defines, packages, library_dirs, chip, domains, port_map
    """
    args = [verilog_file] + ([spec_file] if spec_file else []) + _options(module=module_name)
    if module_files:
        args += ['--files'] + module_files
    if chip:
        args += ['--chip']
    args += _options(domains=domains, map=port_map)
    return _call('check', args, include_dirs, defines, strict, packages, library_dirs=library_dirs)


@mcp.tool()
def soc_snapshot(verilog_file: str, module_name: str = '', output: str = '',
                 format_type: str = 'both', version: str = '1.0.0', changelog: str = '',
                 include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None,
                 library_dirs: list[str] | None = None) -> str:
    """Save JSON/CSV port metadata for optional historical diffing.

    Parameters: verilog_file, module_name, output, format_type, version, changelog, include_dirs, defines, packages, library_dirs
    """
    args = [verilog_file] + _options(module=module_name, output=output, format=format_type,
                                    version=version, changelog=changelog)
    return _call('snapshot', args, include_dirs, defines, packages=packages, library_dirs=library_dirs)


@mcp.tool()
def soc_diff(verilog_file: str, snapshot_file: str = '', module_name: str = '',
             module_files: list[str] | None = None, include_dirs: list[str] | None = None,
             defines: list[str] | None = None, packages: list[str] | None = None, strict: bool = False,
             library_dirs: list[str] | None = None) -> str:
    """Diff a module against a snapshot, or a top's instances against CURRENT RTL.

    Omit snapshot_file and supply module_files for JSON-free [NEW]/[DEL]/[MOD].

    Parameters: verilog_file, snapshot_file, module_name, module_files, include_dirs, defines, packages, strict, library_dirs
    """
    args = [verilog_file] + ([snapshot_file] if snapshot_file else []) + _options(module=module_name)
    if module_files:
        args += ['--files'] + module_files
    return _call('diff', args, include_dirs, defines, strict, packages, library_dirs=library_dirs)


@mcp.tool()
def soc_remove(config_file: str, module_name: str, module_files: list[str] | None = None,
               include_dirs: list[str] | None = None, defines: list[str] | None = None,
               packages: list[str] | None = None,
               lint_config: bool = False, library_dirs: list[str] | None = None,
               output: str = '', strict: bool = False, port_map: str = '',
               vendor_dirs: list[str] | None = None) -> str:
    """Remove by instance or module name from a generated top or legacy config.

    output selects a destination; port_map supplies replacement map rules.
    strict rejects warnings before writing. Unknown names fail.
    lint_config, library_dirs and vendor_dirs control scoped lint collateral.

    Parameters: config_file, module_name, module_files, include_dirs, defines, packages, lint_config, library_dirs, output, strict, port_map, vendor_dirs
    """
    args = [config_file, module_name] + _options(output=output, map=port_map)
    if module_files:
        args += ['--files'] + module_files
    if lint_config:
        args += ['--lint-config']
    for directory in library_dirs or []:
        args += ['-y', directory]
    for directory in vendor_dirs or []:
        args += ['--vendor-dir', directory]
    return _call('remove', args, include_dirs, defines, strict, packages)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--sse', action='store_true')
    args = cli.parse_args()
    mcp.run(transport='sse' if args.sse else 'stdio')
