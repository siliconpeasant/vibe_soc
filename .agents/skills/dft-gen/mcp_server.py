#!/usr/bin/env python3
"""DFT generator MCP server (dft-gen).

Exclusive owner: soc-dft-engineer.

Tools:
  - dft_readiness_check
  - dft_sgdc_from_rtl
  - dft_sgdc_gen
"""

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
    name="dft-gen",
    instructions=(
        "DFT frontend readiness check and SpyGlass DFT SGDC/Tcl generation. "
        "Owner: soc-dft-engineer. Run SpyGlass DFT via soc-build.soc_dft."
    ),
)


def _python(*args: str, cwd: str | None = None) -> str:
    return run_python(SCRIPT_DIR / "dft_gen.py", *args, cwd=cwd)


@mcp.tool()
def dft_readiness_check(
    rtl_file: str,
    module: str = "",
    output: str = "",
    soft_scan: bool = True,
) -> str:
    """Scan RTL top for DFT frontend hooks (test_mode/scan/test_rst/clocks).

    Args:
        rtl_file: Verilog/SystemVerilog file containing the top module
        module: Module name if the file has multiple modules
        output: Optional JSON report path (also writes sibling .md)
        soft_scan: If true, missing scan_enable alone is not a hard fail when
            test_mode is present (default true for early frontend IP)
    """
    rtl = Path(rtl_file).expanduser().resolve()
    if not rtl.is_file():
        raise ValueError(f"rtl_file not found: {rtl}")
    args: list[str] = ["readiness", "--rtl", str(rtl)]
    if module:
        args.extend(["-m", module])
    if output:
        args.extend(["--out", str(Path(output).expanduser().resolve())])
    if soft_scan:
        args.append("--soft-scan")
    try:
        return _python(*args, cwd=str(rtl.parent))
    except Exception as exc:  # noqa: BLE001
        text = str(exc)
        if "DFT_ARTIFACTS=" in text or '"status"' in text:
            return text
        raise


@mcp.tool()
def dft_sgdc_from_rtl(
    rtl_file: str,
    output: str = "",
    module: str = "",
    tcl_output: str = "",
    period_ns: float = 5.0,
    testclock: bool = False,
    best_practice: bool = False,
) -> str:
    """Parse RTL top ports and write a starter SpyGlass DFT SGDC (+ optional Tcl).

    Args:
        rtl_file: Verilog/SystemVerilog file containing the top module
        output: SGDC path (default: beside RTL as <top>_dft.sgdc)
        module: Module name if the file has multiple modules
        tcl_output: Optional module-level driver Tcl path under de/dft/
        period_ns: Default clock period for SGDC clock lines
        testclock: Mark detected clocks as -atspeed -testclock
        best_practice: Comment/enable dft/dft_best_practice in generated Tcl
    """
    rtl = Path(rtl_file).expanduser().resolve()
    if not rtl.is_file():
        raise ValueError(f"rtl_file not found: {rtl}")
    args: list[str] = [
        "from-rtl",
        "--rtl",
        str(rtl),
        "--period",
        str(period_ns),
    ]
    if module:
        args.extend(["-m", module])
    if output:
        args.extend(["-o", str(Path(output).expanduser().resolve())])
    if tcl_output:
        args.extend(["--tcl", str(Path(tcl_output).expanduser().resolve())])
    if testclock:
        args.append("--testclock")
    if best_practice:
        args.append("--best-practice")
    return _python(*args, cwd=str(rtl.parent))


@mcp.tool()
def dft_sgdc_gen(
    config_file: str,
    output: str = "",
    tcl_output: str = "",
    best_practice: bool = False,
) -> str:
    """Generate SpyGlass DFT SGDC from reviewed YAML/JSON.

    Args:
        config_file: Path to dft_sgdc YAML/JSON (see references/dft_sgdc_template.yml)
        output: Explicit .sgdc path (e.g. de/dft/<top>_dft.sgdc)
        tcl_output: Optional module driver Tcl path
        best_practice: Enable dft/dft_best_practice in generated Tcl
    """
    cfg = Path(config_file).expanduser().resolve()
    if not cfg.is_file():
        raise ValueError(f"config_file not found: {cfg}")
    args: list[str] = ["gen", "--config", str(cfg)]
    if output:
        args.extend(["-o", str(Path(output).expanduser().resolve())])
    if tcl_output:
        args.extend(["--tcl", str(Path(tcl_output).expanduser().resolve())])
    if best_practice:
        args.append("--best-practice")
    return _python(*args, cwd=str(cfg.parent))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="dft-gen MCP server")
    parser.add_argument("--sse", action="store_true")
    args = parser.parse_args()
    mcp.run(transport="sse" if args.sse else "stdio")
