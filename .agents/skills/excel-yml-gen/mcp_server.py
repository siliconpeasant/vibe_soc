#!/usr/bin/env python3
"""
Excel-to-YAML Register Generator MCP Server

轻量级 MCP Wrapper，将 Excel 寄存器表转换为 YAML 和寄存器 RTL。
底层仍调用 scripts/ 目录下的现有 CLI 脚本，不改动原有逻辑。

运行方式:
    python3 mcp_server.py          # stdio transport (默认)
    python3 mcp_server.py --sse    # SSE transport (HTTP)
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_command, run_python

# ---------------------------------------------------------------------------
# 路径推导
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent / "scripts"


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="excel-yml-gen",
    instructions=(
        "从 Excel 寄存器工作簿生成 YAML 和 Verilog regfile。"
    ),
)


def _run(cmd: list[str], cwd: str = None, timeout: int = 120) -> str:
    return run_command(cmd, cwd=cwd, timeout=timeout)


def _python(script: str, *args: str, cwd: str = None) -> str:
    """调用 scripts/ 目录下的 Python 脚本。"""
    return run_python(SCRIPT_DIR / script, *args, cwd=cwd)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def excel_yml_gen(excel_file: str, sheet_name: str, output_dir: str = ".") -> str:
    """从 Excel 寄存器描述生成 YAML 和 Verilog regfile。

    Args:
        excel_file: Excel 文件路径
        sheet_name: sheet 名称（如 demo_sys_ctrl_reg，会自动去掉 _reg 后缀）
        output_dir: 输出目录；默认在输入文件同级创建 <stem>_generated
    """
    missing = [name for name in ("pandas", "openpyxl") if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError(
            f"missing runtime modules {missing}; run scripts/setup_mcp_env.sh"
        )
    excel_path = Path(excel_file).expanduser().resolve()
    if not excel_path.is_file():
        raise ValueError(f"excel_file not found: {excel_path}")
    target_dir = (
        excel_path.parent / f"{excel_path.stem}_generated"
        if output_dir == "."
        else Path(output_dir).expanduser().resolve()
    )
    return _python("excel_yml_gen.py", str(excel_path), sheet_name, str(target_dir))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Excel-to-YAML Register Generator MCP Server"
    )
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    mcp.run(transport=transport)
