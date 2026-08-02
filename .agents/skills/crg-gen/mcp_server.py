#!/usr/bin/env python3
"""
CRG generator MCP Server

轻量级 MCP Wrapper，从 Excel 配置生成 CRG RTL 与 SDC。
底层调用 scripts/crg_gen.py，不改动原有逻辑。

运行方式:
    python3 mcp_server.py          # stdio transport (默认)
    python3 mcp_server.py --sse    # SSE transport (HTTP)
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
DEFAULT_TIMEOUT_SEC = 600

mcp = FastMCP(
    name="crg-gen",
    instructions=(
        "从 Excel 配置生成 CRG（时钟复位生成）RTL 和 SDC 约束。\n"
        "输入含 top_info / clk_gen / rst_gen 等 sheet；\n"
        "输出时钟/复位 RTL、顶层、寄存器 YAML/RTL、连接 CSV 与 SDC。"
    ),
)


@mcp.tool()
def crg_gen(excel_file: str, output_dir: str = ".") -> str:
    """从 Excel 配置生成 CRG（时钟复位生成）RTL 和 SDC。

    Args:
        excel_file: Excel 配置文件路径（含 top_info/clk_gen/rst_gen 等 sheet）
        output_dir: 输出目录；默认当前目录，建议使用模块下 de/run/crg_gen/
    """
    missing = [
        name
        for name in ("pandas", "numpy", "openpyxl")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise RuntimeError(
            f"missing runtime modules {missing}; run scripts/setup_mcp_env.sh"
        )

    excel_path = Path(excel_file).expanduser().resolve()
    if not excel_path.is_file():
        raise ValueError(f"excel_file not found: {excel_path}")

    target_dir = (
        Path.cwd().resolve()
        if output_dir in {".", ""}
        else Path(output_dir).expanduser().resolve()
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    return run_python(
        SCRIPT_DIR / "crg_gen.py",
        str(excel_path),
        str(target_dir),
        cwd=str(target_dir),
        timeout=DEFAULT_TIMEOUT_SEC,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CRG generator MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    mcp.run(transport=transport)
