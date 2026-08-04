#!/usr/bin/env python3
"""
YAML Register Map MCP Server (yml2reg)

RTL + software + verification deliverables from one YAML source.
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
    name="yml2reg",
    instructions=(
        "从 YAML 生成 APB/AHB/DAB regfile RTL、Spirit XML、Excel、C/sysmap 头、"
        "UVM regmodel/ral_lib/init/define、bus adapter 模板、JSON/CSV regmap，"
        "以及 multi-block top RAL。"
    ),
)


def _python(script: str, *args: str, cwd: str = None, timeout: int = 120) -> str:
    return run_python(SCRIPT_DIR / script, *args, cwd=cwd, timeout=timeout)


def _require_yaml(yaml_file: str) -> Path:
    yaml_path = Path(yaml_file).expanduser().resolve()
    if not yaml_path.is_file():
        raise ValueError(f"yaml_file not found: {yaml_path}")
    return yaml_path


def _docs_args(yaml_path: Path, output_dir: str = "") -> list[str]:
    args = [str(yaml_path)]
    if output_dir:
        args.extend(["-o", str(Path(output_dir).expanduser().resolve())])
    return args


@mcp.tool()
def yml2reg(yaml_file: str, protocol: str = "apb") -> str:
    """生成 APB/AHB/DAB regfile RTL（含中断 bank、lock、完整总线时序）。"""
    yaml_path = _require_yaml(yaml_file)
    if protocol not in {"apb", "ahb", "dab"}:
        raise ValueError("protocol must be apb, ahb, or dab")
    return _python("yml2reg.py", str(yaml_path), protocol, cwd=str(yaml_path.parent))


@mcp.tool()
def yml2xml(yaml_file: str, output_dir: str = "") -> str:
    """生成 Spirit/IP-XACT XML。"""
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2xml.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2excel(yaml_file: str, output_dir: str = "") -> str:
    """生成 Excel 寄存器表。"""
    if importlib.util.find_spec("openpyxl") is None:
        raise RuntimeError("missing openpyxl; run make mcp-setup")
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2excel.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2reg_c(
    yaml_file: str,
    output_dir: str = "",
    guard: str = "",
    no_fill_gaps: bool = False,
) -> str:
    """生成软件 C 头（含 sparse reserved MMIO struct）。"""
    yaml_path = _require_yaml(yaml_file)
    args = _docs_args(yaml_path, output_dir)
    if guard:
        args.extend(["-g", guard])
    if no_fill_gaps:
        args.append("--no-fill-gaps")
    return _python("yml2reg_c.py", *args, cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2sysmap(yaml_file: str, output_dir: str = "") -> str:
    """生成模块 sysmap 片段。"""
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2sysmap.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2uvm_ral(yaml_file: str, output_dir: str = "", coverage: bool = False) -> str:
    """生成 UVM regmodel NAME_ral.svh（含 GET/SET、maps、backdoor、coverage 选项）。"""
    yaml_path = _require_yaml(yaml_file)
    args = _docs_args(yaml_path, output_dir)
    if coverage:
        args.append("--coverage")
    return _python("yml2uvm_ral.py", *args, cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2uvm_ral_top(
    yaml_file: str, output_dir: str = "", emit_children: bool = True
) -> str:
    """从 top YAML（blocks:[]）生成 multi-block top RAL。"""
    yaml_path = _require_yaml(yaml_file)
    args = _docs_args(yaml_path, output_dir)
    if emit_children:
        args.append("--emit-children")
    return _python("yml2uvm_ral_top.py", *args, cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2sv_define(yaml_file: str, output_dir: str = "") -> str:
    """生成 DV 地址 define（.h/.svh）。"""
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2sv_define.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2regs_init(yaml_file: str, output_dir: str = "") -> str:
    """生成寄存器 init：*_regs_init.sv/.c/.h。"""
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2regs_init.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2ral_lib(yaml_file: str, output_dir: str = "") -> str:
    """生成 regs_*_ral_lib.svh（extends block + config/mirror helpers）。"""
    yaml_path = _require_yaml(yaml_file)
    return _python("yml2ral_lib.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2bus_adapters(yaml_file: str = "", output_dir: str = "") -> str:
    """生成 APB/AHB/DAB UVM adapter 模板 yml2reg_bus_adapters.svh。"""
    if yaml_file:
        yaml_path = _require_yaml(yaml_file)
        return _python(
            "yml2bus_adapters.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR)
        )
    args = []
    if output_dir:
        args.extend(["-o", str(Path(output_dir).expanduser().resolve())])
    return _python("yml2bus_adapters.py", *args, cwd=str(SCRIPT_DIR))


@mcp.tool()
def yml2regmap_export(yaml_file: str, output_dir: str = "") -> str:
    """导出 regmap JSON + CSV。"""
    yaml_path = _require_yaml(yaml_file)
    return _python(
        "yml2regmap_export.py", *_docs_args(yaml_path, output_dir), cwd=str(SCRIPT_DIR)
    )


@mcp.tool()
def yml2docs(
    yaml_file: str,
    output_dir: str = "",
    targets: str = "xml,excel,h,sysmap,ral,define,init,ral_lib,regmap,adapter",
    guard: str = "",
    no_fill_gaps: bool = False,
) -> str:
    """一键生成文档+验证全套（模块 YAML 或 top blocks YAML）。不生成 RTL。"""
    tset = {t.strip().lower() for t in targets.split(",") if t.strip()}
    if "excel" in tset and importlib.util.find_spec("openpyxl") is None:
        raise RuntimeError("missing openpyxl; run make mcp-setup")
    yaml_path = _require_yaml(yaml_file)
    args = _docs_args(yaml_path, output_dir) + ["--targets", targets]
    if guard:
        args.extend(["-g", guard])
    if no_fill_gaps:
        args.append("--no-fill-gaps")
    return _python("yml2docs.py", *args, cwd=str(SCRIPT_DIR))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YAML Register Map MCP Server")
    parser.add_argument("--sse", action="store_true")
    args = parser.parse_args()
    mcp.run(transport="sse" if args.sse else "stdio")
