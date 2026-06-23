#!/usr/bin/env python3
"""
YAML-to-Register RTL MCP Server

轻量级 MCP Wrapper，将 YAML 寄存器描述转换为 APB/AHB 寄存器 RTL。
底层仍调用 scripts/ 目录下的现有 CLI 脚本，不改动原有逻辑。

运行方式:
    python3 mcp_server.py          # stdio transport (默认)
    python3 mcp_server.py --sse    # SSE transport (HTTP)
"""

import argparse
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
    name="yml2reg",
    instructions=(
        "从 YAML 寄存器描述生成 APB/AHB Verilog regfile。"
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
def yml2reg(yaml_file: str, protocol: str = "apb") -> str:
    """从 YAML 寄存器描述生成 Verilog regfile。

    Args:
        yaml_file: YAML 寄存器描述文件路径
        protocol: 总线协议，可选 apb / ahb
    """
    yaml_path = Path(yaml_file).expanduser().resolve()
    if not yaml_path.is_file():
        raise ValueError(f"yaml_file not found: {yaml_path}")
    if protocol not in {"apb", "ahb"}:
        raise ValueError("protocol must be apb or ahb")
    return _python("yml2reg.py", str(yaml_path), protocol, cwd=str(yaml_path.parent))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YAML-to-Register RTL MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    mcp.run(transport=transport)
