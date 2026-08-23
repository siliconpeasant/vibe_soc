#!/usr/bin/env python3
"""
IP-XACT / Spirit XML → yml2reg YAML MCP Server (xml2yml / ipxact2yml)

Converts register-bearing XML into the YAML schema consumed by yml2reg.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_python

SCRIPT_DIR = Path(__file__).parent / "scripts"

mcp = FastMCP(
    name="xml2yml",
    instructions=(
        "从 IP-XACT / Spirit XML 生成 yml2reg 兼容的寄存器 YAML。"
        "支持 yml2xml 方言与常见 IEEE Spirit/IP-XACT memoryMap/addressBlock。"
        "生成后请用 yml2reg / yml2docs 继续产出 RTL/DV/SW。"
    ),
)


def _python(script: str, *args: str, cwd: str | None = None, timeout: int = 120) -> str:
    return run_python(SCRIPT_DIR / script, *args, cwd=cwd, timeout=timeout)


def _require_xml(xml_file: str) -> Path:
    xml_path = Path(xml_file).expanduser().resolve()
    if not xml_path.is_file():
        raise ValueError(f"xml_file not found: {xml_path}")
    return xml_path


def _convert(
    xml_file: str,
    output_dir: str = "",
    name: str = "",
    protocol: str = "",
    fold_interrupts: bool = False,
) -> str:
    if importlib.util.find_spec("yaml") is None:
        raise RuntimeError("missing PyYAML; run make mcp-setup")
    xml_path = _require_xml(xml_file)
    args: list[str] = [str(xml_path)]
    if output_dir:
        args.extend(["-o", str(Path(output_dir).expanduser().resolve())])
    if name:
        args.extend(["--name", name])
    if protocol:
        args.extend(["--protocol", protocol])
    if fold_interrupts:
        args.append("--fold-interrupts")
    return _python("xml2yml.py", *args, cwd=str(xml_path.parent))


@mcp.tool()
def xml2yml(
    xml_file: str,
    output_dir: str = "",
    name: str = "",
    protocol: str = "",
    fold_interrupts: bool = False,
) -> str:
    """IP-XACT / Spirit XML → yml2reg YAML。

    Args:
        xml_file: Spirit/IP-XACT XML path
        output_dir: optional output directory (default: beside XML)
        name: optional YAML component name override
        protocol: optional bus protocol override (apb|ahb|dab)
        fold_interrupts: collapse expanded *_raw/_stat/... banks into interrupts[]
    """
    return _convert(xml_file, output_dir, name, protocol, fold_interrupts)


@mcp.tool()
def ipxact2yml(
    xml_file: str,
    output_dir: str = "",
    name: str = "",
    protocol: str = "",
    fold_interrupts: bool = False,
) -> str:
    """Alias of xml2yml: IP-XACT / Spirit XML → yml2reg YAML."""
    return _convert(xml_file, output_dir, name, protocol, fold_interrupts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xml2yml MCP server")
    parser.add_argument("--sse", action="store_true", help="use SSE transport")
    args = parser.parse_args()
    if args.sse:
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
