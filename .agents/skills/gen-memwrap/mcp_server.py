#!/usr/bin/env python3
"""
gen-memwrap MCP Server

Excel memory table → unified SoC wrap RTL + open-source macro .lib/.lef
(backend: sky130 OpenRAM / nangate45 FakeRAM catalogs).
"""

import argparse
import importlib.util
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(PLUGIN_ROOT / "scripts") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_python

SCRIPT_DIR = Path(__file__).parent / "scripts"

mcp = FastMCP(
    name="gen-memwrap",
    instructions=(
        "从 Excel 存储器表生成统一端口 memory wrap RTL，并附带 sky130 OpenRAM / "
        "nangate45 FakeRAM 的 .lib/.lef（catalog 或在线生成）。"
        "仅 sky130 与 nangate45；支持 spram/tpram/sfifo/asfifo/rom。"
    ),
)


@mcp.tool()
def gen_memwrap(
    excel_file: str,
    sheet_name: str,
    output_dir: str,
    platform: str = "auto",
    relaxed: bool = False,
    generate: bool = True,
) -> str:
    """从 Excel 生成 memory wrap + lib/lef（catalog 命中或在线 OpenRAM/FakeRAM 生成）。

    Args:
        excel_file: Excel 路径（含 TYPE / NumberOfWords / BitsInWord 等列）
        sheet_name: sheet 名子串（匹配包含该串的 sheet）
        output_dir: 输出目录（rtl/ lib/ lef/ generated/ report/ filelist.f）
        platform: sky130 | nangate45 | auto（auto 用行内 PLATFORM 列，默认 sky130）
        relaxed: True 时在 generate=false 下允许就近更大 catalog 宏
        generate: catalog 未命中时在线生成（sky130→OpenRAM；n45→bsg_fakeram 或 builtin）
    """
    missing = [n for n in ("pandas",) if importlib.util.find_spec(n) is None]
    if missing:
        raise RuntimeError(
            f"missing runtime modules {missing}; run make mcp-setup / scripts/setup_mcp_env.sh"
        )
    excel_path = Path(excel_file).expanduser().resolve()
    if not excel_path.is_file():
        raise ValueError(f"excel_file not found: {excel_path}")
    if not sheet_name or not str(sheet_name).strip():
        raise ValueError("sheet_name is required")
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    plat = (platform or "auto").strip().lower()
    if plat not in {"sky130", "nangate45", "auto"}:
        raise ValueError("platform must be sky130, nangate45, or auto")
    args = [
        str(excel_path),
        str(sheet_name).strip(),
        str(out),
        plat,
    ]
    if relaxed:
        args.append("--relaxed")
    args.append("--generate" if generate else "--no-generate")
    # longer timeout: OpenRAM can take many minutes per macro
    return run_python(
        SCRIPT_DIR / "gen_memwrap.py",
        *args,
        cwd=str(out),
        timeout=14400,
    )


@mcp.tool()
def gen_memwrap_status() -> str:
    """查询 OpenRAM / bsg_fakeram / builtin FakeRAM 是否可用。"""
    return run_python(SCRIPT_DIR / "gen_memwrap.py", "--status", timeout=60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gen-memwrap MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE transport")
    args = parser.parse_args()
    mcp.run(transport="sse" if args.sse else "stdio")
