#!/usr/bin/env python3
"""
gen-asic-memmap MCP Server

从 Excel memory map 生成 ASIC 地址映射 YAML + C/SV sysmap header。
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
    name="gen-asic-memmap",
    instructions=(
        "从 Excel memmap sheet 生成芯片地址映射 YAML 与 C/SV sysmap header。"
    ),
)


@mcp.tool()
def gen_asic_memmap(excel_file: str, project_name: str, output_dir: str = ".") -> str:
    """从 Excel memory map 生成地址映射 YML + C/SV header。

    Args:
        excel_file: Excel 文件路径（含 memmap sheet）
        project_name: 项目名称（输出文件名前缀）
        output_dir: 输出目录；默认当前目录
    """
    missing = [n for n in ("pandas",) if importlib.util.find_spec(n) is None]
    if missing:
        raise RuntimeError(
            f"missing runtime modules {missing}; run make mcp-setup / scripts/setup_mcp_env.sh"
        )
    excel_path = Path(excel_file).expanduser().resolve()
    if not excel_path.is_file():
        raise ValueError(f"excel_file not found: {excel_path}")
    if not project_name or not str(project_name).strip():
        raise ValueError("project_name is required")
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    return run_python(
        SCRIPT_DIR / "gen_asic_memmap.py",
        str(excel_path),
        str(project_name).strip(),
        str(out),
        cwd=str(out),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gen-asic-memmap MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE transport")
    args = parser.parse_args()
    mcp.run(transport="sse" if args.sse else "stdio")
