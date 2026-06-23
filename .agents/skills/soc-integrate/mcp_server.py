#!/usr/bin/env python3
"""
SoC Integrate MCP Server

轻量级 MCP Wrapper，暴露 SoC 端口管理与顶层集成工具。
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
    name="soc-integrate",
    instructions=(
        "SoC RTL 端口提取、实例化、wrapper、顶层集成和接口变更追踪工具。"
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
def soc_extract(verilog_file: str, module_name: str = "") -> str:
    """提取 Verilog 模块的端口信息（方向、位宽、参数）。

    Args:
        verilog_file: Verilog 文件绝对/相对路径
        module_name: 模块名，留空则自动推导
    """
    args = ["extract", verilog_file]
    if module_name:
        args += ["-m", module_name]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_instantiate(verilog_file: str, instance_name: str = "") -> str:
    """生成 Verilog 模块的实例化代码（.port(signal) 格式）。

    Args:
        verilog_file: Verilog 文件路径
        instance_name: 实例化名，留空则使用模块名
    """
    args = ["instantiate", verilog_file]
    if instance_name:
        args += ["-n", instance_name]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_integrate(
    module_files: list[str],
    top_name: str,
    output_file: str,
    port_map: str = "",
) -> str:
    """将多个 Verilog 模块集成到一个顶层模块中。

    Args:
        module_files: 待集成模块的 Verilog 文件路径列表
        top_name: 顶层模块名
        output_file: 输出顶层文件路径
        port_map: 可选端口映射 JSON 文件路径
    """
    args = ["integrate"] + module_files + ["-n", top_name, "-o", output_file]
    if port_map:
        args += ["--map", port_map]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_wrap(verilog_file: str, module_name: str = "", wrapper_name: str = "", output: str = "") -> str:
    """生成 Verilog 模块的 wrapper（信号透传 + 可选逻辑注入点）。

    Args:
        verilog_file: 原始 Verilog 文件路径
        module_name: 指定模块名（文件内有多个模块时）
        wrapper_name: wrapper 模块名，留空则自动推导
        output: 输出文件路径，留空则打印到 stdout
    """
    args = ["wrap", verilog_file]
    if module_name:
        args += ["-m", module_name]
    if wrapper_name:
        args += ["-n", wrapper_name]
    if output:
        args += ["-o", output]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_csv(verilog_file: str, module_name: str = "", output: str = "ports.csv") -> str:
    """将 Verilog 模块端口导出为 CSV（便于 review 和文档化）。

    Args:
        verilog_file: Verilog 文件路径
        module_name: 指定模块名
        output: 输出 CSV 文件路径，默认 ports.csv
    """
    args = ["csv", verilog_file, "-o", output]
    if module_name:
        args += ["-m", module_name]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_snapshot(
    verilog_file: str,
    module_name: str = "",
    output: str = "",
    format_type: str = "both",
    version: str = "1.0.0",
    changelog: str = "",
) -> str:
    """保存 Verilog 模块端口快照（JSON + CSV），用于后续变更追踪。

    Args:
        verilog_file: Verilog 文件路径
        module_name: 指定模块名
        output: 输出文件前缀，留空则自动写入 verilog_file 同级目录的 <module>_ports
        format_type: 输出格式，可选 json / csv / both（默认 both）
        version: 快照版本号
        changelog: 变更说明
    """
    args = ["snapshot", verilog_file, "-f", format_type, "-v", version]
    if module_name:
        args += ["-m", module_name]
    if output:
        args += ["-o", output]
    if changelog:
        args += ["-c", changelog]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_diff(verilog_file: str, snapshot_file: str, module_name: str = "") -> str:
    """对比当前 Verilog 模块与历史快照的差异（检测新增/删除/修改端口）。

    Args:
        verilog_file: 当前 Verilog 文件路径
        snapshot_file: 历史快照 JSON 文件路径
        module_name: 指定模块名
    """
    args = ["diff", verilog_file, snapshot_file]
    if module_name:
        args += ["-m", module_name]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_extract_map(top_file: str, output: str = "", verify_modules: list[str] = None) -> str:
    """从顶层 Verilog 文件提取所有实例化的连接关系，生成 port map JSON。

    Args:
        top_file: 顶层 Verilog 文件路径
        output: 输出 JSON 文件路径，留空则打印到 stdout
        verify_modules: 原始模块文件列表，用于验证端口存在性
    """
    args = ["extract-map", top_file]
    if output:
        args += ["-o", output]
    if verify_modules:
        args += ["--verify"] + verify_modules
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_update(
    config_file: str,
    output: str = "",
    port_map: str = "",
    top_name: str = "",
) -> str:
    """根据 .integrate.json 配置文件一键刷新顶层（子模块端口变更后使用）。

    执行流程：提取当前 mapping → 对比端口快照 → 重新生成顶层 → 更新配置。

    Args:
        config_file: integrate 配置文件路径（.integrate.json）
        output: 覆盖输出文件路径
        port_map: 覆盖端口映射 JSON 文件路径
        top_name: 覆盖顶层模块名
    """
    args = ["update", config_file]
    if output:
        args += ["-o", output]
    if port_map:
        args += ["--map", port_map]
    if top_name:
        args += ["-n", top_name]
    return _python("soc_integrate.py", *args)


@mcp.tool()
def soc_remove(config_file: str, module_name: str) -> str:
    """从集成配置中删除指定模块，并自动刷新顶层。

    Args:
        config_file: integrate 配置文件路径（.integrate.json）
        module_name: 要删除的模块名
    """
    return _python("soc_integrate.py", "remove", config_file, module_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SoC Integrate MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    mcp.run(transport=transport)
