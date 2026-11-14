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


def _call(command, args, include_dirs=None, defines=None, strict=False, packages=None):
    for directory in include_dirs or []:
        args += ['-I', directory]
    for define in defines or []:
        args += ['-D', define]
    for package in packages or []:
        args += ['--package', package]
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
                defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Extract directions, symbolic widths, types, dimensions and parameter defaults.

    include_dirs searches `include files; defines contains NAME or NAME=value.
    packages lists package/typedef files in dependency order for width resolution.
    Unsupported interface syntax reports source file, line and construct.
    """
    return _call('extract', [verilog_file] + _options(module=module_name), include_dirs, defines, packages=packages)


@mcp.tool()
def soc_instantiate(verilog_file: str, instance_name: str = '', module_name: str = '',
                    include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Generate named whole-expression connections without implicit bus slicing."""
    return _call('instantiate', [verilog_file] + _options(name=instance_name, module=module_name), include_dirs, defines, packages=packages)


@mcp.tool()
def soc_wrap(verilog_file: str, module_name: str = '', wrapper_name: str = '', output: str = '',
             include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Generate a passthrough wrapper preserving parameter and port type text."""
    return _call('wrap', [verilog_file] + _options(module=module_name, name=wrapper_name, output=output), include_dirs, defines, packages=packages)


@mcp.tool()
def soc_csv(verilog_file: str, module_name: str = '', output: str = 'ports.csv',
            include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Explicitly export a module's ports as CSV; integration CSV is separately opt-in."""
    return _call('csv', [verilog_file] + _options(module=module_name, output=output), include_dirs, defines, packages=packages)


@mcp.tool()
def soc_integrate(module_files: list[str], top_name: str, output_file: str, port_map: str = '',
                  csv: bool = False, track: bool = False, strict: bool = False,
                  include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Generate a top and print width/driver/connectivity/heuristic CDC checks.

    Exact instance.port then legacy module.port keys override ordered regex/glob
    templates. Native interface instances connect interface/modport ports.
    csv opts into review CSV; track opts into .integrate.json (both default off).
    strict rejects warnings before writing outputs. CDC checks are structural hints.
    """
    args = module_files + _options(name=top_name, output=output_file, map=port_map)
    if csv:
        args += ['--csv']
    if track:
        args += ['--track']
    return _call('integrate', args, include_dirs, defines, strict, packages)


@mcp.tool()
def soc_update(config_file: str = '', output: str = '', port_map: str = '', top_name: str = '',
               module_files: list[str] | None = None, top_file: str = '', csv: bool = False,
               track: bool = False, strict: bool = False, include_dirs: list[str] | None = None,
               defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Refresh named instances from CURRENT RTL, preserving manual expressions verbatim.

    Pass top_file and module_files for JSON-free update. config_file also accepts
    a top path or legacy .integrate.json. Embedded prior-port comments permit
    width/direction change reports; JSON is optional. New ports follow map/shared
    rules; deleted ports disappear. csv and track are independently opt-in.
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
    return _call('update', args, include_dirs, defines, strict, packages)


@mcp.tool()
def soc_extract_map(top_file: str, output: str = '', verify_modules: list[str] | None = None,
                    expand: bool = False, include_dirs: list[str] | None = None,
                    defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Extract named connections from the top without JSON; retain original templates.

    expand explicitly materializes every instance.port mapping. Manual overrides
    are exact keys; template rules and their order otherwise survive round trips.
    """
    args = [top_file] + _options(output=output)
    if verify_modules:
        args += ['--verify'] + verify_modules
    if expand:
        args += ['--expand']
    return _call('extract-map', args, include_dirs, defines, packages=packages)


@mcp.tool()
def soc_check(verilog_file: str, spec_file: str = '', module_name: str = '',
              module_files: list[str] | None = None, strict: bool = False,
              include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Check a module against a port spec, or a top's graph against CURRENT RTL.

    With spec_file, missing/extra/modified ports fail. Without it, supply the top
    and module_files; report width, multiple-driver, unconnected and CDC warnings.
    strict makes graph warnings errors. This is not CDC or timing signoff.
    """
    args = [verilog_file] + ([spec_file] if spec_file else []) + _options(module=module_name)
    if module_files:
        args += ['--files'] + module_files
    return _call('check', args, include_dirs, defines, strict, packages)


@mcp.tool()
def soc_snapshot(verilog_file: str, module_name: str = '', output: str = '',
                 format_type: str = 'both', version: str = '1.0.0', changelog: str = '',
                 include_dirs: list[str] | None = None, defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Save JSON/CSV port metadata for optional historical diffing."""
    args = [verilog_file] + _options(module=module_name, output=output, format=format_type,
                                    version=version, changelog=changelog)
    return _call('snapshot', args, include_dirs, defines, packages=packages)


@mcp.tool()
def soc_diff(verilog_file: str, snapshot_file: str = '', module_name: str = '',
             module_files: list[str] | None = None, include_dirs: list[str] | None = None,
             defines: list[str] | None = None, packages: list[str] | None = None) -> str:
    """Diff a module against a snapshot, or a top's instances against CURRENT RTL.

    Omit snapshot_file and supply module_files for JSON-free [NEW]/[DEL]/[MOD].
    """
    args = [verilog_file] + ([snapshot_file] if snapshot_file else []) + _options(module=module_name)
    if module_files:
        args += ['--files'] + module_files
    return _call('diff', args, include_dirs, defines, packages=packages)


@mcp.tool()
def soc_remove(config_file: str, module_name: str, module_files: list[str] | None = None,
               include_dirs: list[str] | None = None, defines: list[str] | None = None,
               packages: list[str] | None = None) -> str:
    """Remove a dependency from a tracked integration and regenerate its top."""
    args = [config_file, module_name]
    if module_files:
        args += ['--files'] + module_files
    return _call('remove', args, include_dirs, defines, packages=packages)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--sse', action='store_true')
    args = cli.parse_args()
    mcp.run(transport='sse' if args.sse else 'stdio')
