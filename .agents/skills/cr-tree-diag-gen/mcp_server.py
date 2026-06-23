#!/usr/bin/env python3
"""
CR Tree Diagram Generator MCP Server

轻量级 MCP Wrapper，暴露 cr_tree_diag_gen 的核心功能。

运行方式:
    python3 mcp_server.py          # stdio transport (默认)
"""

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 路径推导：确保能导入同目录下的 scripts 包
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="cr-tree-diag-gen",
    instructions=(
        "时钟/复位树链路图生成器。\n"
        "将 Excel 表格转换为 Draw.io (.drawio) 或 Excalidraw (.excalidraw) 格式的拓扑图。\n"
        "支持时钟树和复位树，自动检测表格类型。"
    ),
)


# ---------------------------------------------------------------------------
# 核心生成逻辑
# ---------------------------------------------------------------------------
def _generate(input_path: str, output_path: str = None, output_dir: str = None) -> str:
    """核心生成逻辑"""
    # 延迟导入，避免 MCP 启动时加载失败
    try:
        from scripts.parser import CrgExcelParser
        from scripts.graph import Graph
        from scripts.layout import HierarchicalLayout
        from scripts.renderer import DrawioRenderer
        from scripts.excalidraw_renderer import ExcalidrawRenderer
    except ImportError as exc:
        raise RuntimeError(
            "missing diagram runtime dependencies; run scripts/setup_mcp_env.sh"
        ) from exc

    input_file = Path(input_path).expanduser().resolve()
    if not input_file.is_file():
        raise ValueError(f"input file not found: {input_file}")

    # 推导输出路径
    if output_path:
        output_paths = [output_path]
    else:
        input_stem = input_file.stem
        if input_stem.endswith("_table"):
            output_stem = input_stem[:-6] + "_tree"
        else:
            output_stem = input_stem + "_tree"
        if output_dir:
            output_dir_path = str(Path(output_dir).expanduser().resolve())
        else:
            output_dir_path = str(input_file.parent / f"{input_stem}_diagram")
        output_paths = [
            os.path.join(output_dir_path, output_stem + ".drawio"),
            os.path.join(output_dir_path, output_stem + ".excalidraw"),
        ]

    # 解析
    parser = CrgExcelParser(str(input_file))
    rows = parser.parse()
    summary = parser.get_summary(rows)

    # 检测类型
    is_reset = any("SOFT_DFLT" in str(k).upper() for k in rows[0].keys()) if rows else False
    tree_type = "Reset Tree" if is_reset else "Clock Tree"

    # 构建图
    graph = Graph()
    if is_reset:
        graph.build_reset_tree_from_rows(rows)
    else:
        graph.build_from_rows(rows)

    errors = graph.validate()
    warnings_text = "\n".join(f"  - {e}" for e in errors) if errors else "None"

    # 布局
    layout = HierarchicalLayout(
        level_spacing=280,
        node_spacing=70,
        start_x=80,
        start_y=120,
    )
    layout.compute(graph)

    # 渲染
    results = []
    title = f"CRG {tree_type}"
    for out_path in output_paths:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        ext = os.path.splitext(out_path)[1].lower()
        if ext in (".excalidraw", ".json"):
            renderer = ExcalidrawRenderer()
            renderer.render(graph, out_path, title=title)
            results.append(f"Excalidraw: {out_path}")
        else:
            renderer = DrawioRenderer()
            renderer.render(graph, out_path, title=title)
            results.append(f"Draw.io: {out_path}")

    return (
        f"Generated {tree_type}\n"
        f"Signals: {summary['total']}, Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}\n"
        f"Attributes: {summary['attrs']}\n"
        f"Warnings: {warnings_text}\n"
        f"Outputs:\n" + "\n".join(f"  - {r}" for r in results)
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def cr_tree_diag_gen(input_path: str, output_dir: str = None) -> str:
    """从 Excel 表格生成时钟/复位树图（同时输出 drawio + excalidraw）。

    Args:
        input_path: 输入 Excel 文件路径（.xlsx），时钟树或复位树表格
        output_dir: 输出目录；留空则在输入同级创建 <stem>_diagram
    """
    return _generate(input_path, output_dir=output_dir)


@mcp.tool()
def cr_tree_diag_gen_drawio(input_path: str, output_path: str = None) -> str:
    """从 Excel 表格生成 Draw.io 格式的时钟/复位树图。

    Args:
        input_path: 输入 Excel 文件路径（.xlsx）
        output_path: 输出文件路径（.drawio），留空则自动推导
    """
    if not output_path:
        input_file = Path(input_path).expanduser().resolve()
        input_stem = input_file.stem
        if input_stem.endswith("_table"):
            output_stem = input_stem[:-6] + "_tree"
        else:
            output_stem = input_stem + "_tree"
        output_path = str(input_file.parent / f"{input_stem}_diagram" / (output_stem + ".drawio"))
    return _generate(input_path, output_path=output_path)


@mcp.tool()
def cr_tree_diag_gen_excalidraw(input_path: str, output_path: str = None) -> str:
    """从 Excel 表格生成 Excalidraw 格式的时钟/复位树图。

    Args:
        input_path: 输入 Excel 文件路径（.xlsx）
        output_path: 输出文件路径（.excalidraw），留空则自动推导
    """
    if not output_path:
        input_file = Path(input_path).expanduser().resolve()
        input_stem = input_file.stem
        if input_stem.endswith("_table"):
            output_stem = input_stem[:-6] + "_tree"
        else:
            output_stem = input_stem + "_tree"
        output_path = str(input_file.parent / f"{input_stem}_diagram" / (output_stem + ".excalidraw"))
    return _generate(input_path, output_path=output_path)


if __name__ == "__main__":
    mcp.run()
