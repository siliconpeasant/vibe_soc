#!/usr/bin/env python3
"""lib-db-gen MCP server: Liberty→.db convert and Verilog port stub→.db."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_python

SCRIPT_DIR = Path(__file__).parent / "scripts"

mcp = FastMCP(
    name="lib-db-gen",
    instructions=(
        "将 Liberty .lib 转为 Synopsys .db（默认 dc_shell + enable_write_lib_mode），"
        "或从 Verilog top 端口生成 stub Liberty/.db。"
        "专属综合工程师（soc-synthesis-engineer）；stub 仅用于早期 link，非签核库。"
    ),
)


def _python(*args: str, cwd: str | None = None, timeout: int = 3600) -> str:
    return run_python(SCRIPT_DIR / "lib_db_gen.py", *args, cwd=cwd, timeout=timeout)


@mcp.tool()
def lib_db_convert(
    lib_file: str,
    db_file: str,
    lc_shell: str = "",
    dc_shell: str = "",
    shell_mode: str = "",
    work_dir: str = "",
    library_name: str = "",
    no_run: bool = False,
    keep_tcl: bool = False,
) -> str:
    """Convert an existing Liberty .lib to Synopsys .db.

    Default shell_mode is dc: dc_shell + enable_write_lib_mode (clean exit).
    Optional shell_mode=lc uses lc_shell (may SIGSEGV after successful write_lib
    on some hosts); auto prefers dc then falls back to lc.

    Args:
        lib_file: Input .lib path
        db_file: Output .db path
        lc_shell: Optional lc_shell binary (only for shell_mode lc/auto)
        dc_shell: Optional dc_shell binary (default PATH / DC_SHELL)
        shell_mode: dc|auto|lc (default dc / LIB_DB_SHELL_MODE)
        work_dir: Optional shell work directory
        library_name: Optional library name override
        no_run: Only emit convert Tcl without running the shell
        keep_tcl: Keep convert Tcl after success
    """
    lib_path = Path(lib_file).expanduser().resolve()
    db_path = Path(db_file).expanduser().resolve()
    if not lib_path.is_file():
        raise ValueError(f"lib_file not found: {lib_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    args = ["convert", "--lib", str(lib_path), "--db", str(db_path)]
    if lc_shell:
        args.extend(["--lc-shell", lc_shell])
    if dc_shell:
        args.extend(["--dc-shell", dc_shell])
    if shell_mode:
        args.extend(["--shell-mode", shell_mode])
    if work_dir:
        args.extend(["--work-dir", str(Path(work_dir).expanduser().resolve())])
    if library_name:
        args.extend(["--library-name", library_name])
    if no_run:
        args.append("--no-run")
    if keep_tcl:
        args.append("--keep-tcl")
    return _python(*args, cwd=str(db_path.parent))


@mcp.tool()
def lib_db_stub(
    top_v: str,
    lib_file: str,
    db_file: str,
    top: str = "",
    lc_shell: str = "",
    dc_shell: str = "",
    shell_mode: str = "",
    work_dir: str = "",
    library_name: str = "",
    no_run: bool = False,
    keep_tcl: bool = False,
) -> str:
    """Generate black-box stub Liberty from a Verilog top and optionally compile to .db.

    Args:
        top_v: Verilog top file
        lib_file: Output stub .lib path
        db_file: Output .db path
        top: Module name if file has multiple modules
        lc_shell: Optional lc_shell binary (only for shell_mode lc/auto)
        dc_shell: Optional dc_shell binary
        shell_mode: dc|auto|lc (default dc)
        work_dir: Optional shell work directory
        library_name: Optional library name
        no_run: Only emit .lib + Tcl
        keep_tcl: Keep convert Tcl after success
    """
    v_path = Path(top_v).expanduser().resolve()
    if not v_path.is_file():
        raise ValueError(f"top_v not found: {v_path}")
    lib_path = Path(lib_file).expanduser().resolve()
    db_path = Path(db_file).expanduser().resolve()
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    args = ["stub", "--top-v", str(v_path), "--lib", str(lib_path), "--db", str(db_path)]
    if top:
        args.extend(["--top", top])
    if lc_shell:
        args.extend(["--lc-shell", lc_shell])
    if dc_shell:
        args.extend(["--dc-shell", dc_shell])
    if shell_mode:
        args.extend(["--shell-mode", shell_mode])
    if work_dir:
        args.extend(["--work-dir", str(Path(work_dir).expanduser().resolve())])
    if library_name:
        args.extend(["--library-name", library_name])
    if no_run:
        args.append("--no-run")
    if keep_tcl:
        args.append("--keep-tcl")
    return _python(*args, cwd=str(db_path.parent))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="lib-db-gen MCP server")
    parser.add_argument("--sse", action="store_true")
    args = parser.parse_args()
    mcp.run(transport="sse" if args.sse else "stdio")
