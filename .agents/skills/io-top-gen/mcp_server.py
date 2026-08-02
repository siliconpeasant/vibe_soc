#!/usr/bin/env python3
"""
IO/Pad generator MCP Server

轻量级 MCP Wrapper，从 Excel 配置生成 IO/Pad RTL。
底层调用 scripts/io_top_gen.py，不改动原有逻辑。

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
    name="io-top-gen",
    instructions=(
        "从 Excel 配置生成 IO/Pad 相关 RTL（io_top、io_ring、pin_mux、SDC）。\n"
        "输入含 pad_cfg / pin_mux 等 sheet；\n"
        "输出 pad ring、pin mux、寄存器 YAML/RTL、连接 CSV 与 SDC。"
    ),
)


@mcp.tool()
def io_top_gen(excel_file: str, output_dir: str = ".") -> str:
    """从 Excel 配置生成 IO/Pad 相关 RTL（io_top、io_ring、pin_mux、SDC）。

    Args:
        excel_file: Excel 配置文件路径（含 pad_cfg/pin_mux sheet）
        output_dir: 输出目录；默认当前目录，建议使用模块下 de/run/io_top_gen/
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
        SCRIPT_DIR / "io_top_gen.py",
        str(excel_path),
        str(target_dir),
        cwd=str(target_dir),
        timeout=DEFAULT_TIMEOUT_SEC,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IO/Pad generator MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    mcp.run(transport=transport)
