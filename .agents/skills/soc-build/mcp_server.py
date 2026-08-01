#!/usr/bin/env python3
"""
SoC Build MCP Server

轻量级 MCP Wrapper，暴露最常用的 soc-build 工具操作。
底层仍调用 scripts/ 目录下的现有 CLI 脚本，不改动原有逻辑。

运行方式:
    python3 mcp_server.py          # stdio transport (默认)
    python3 mcp_server.py --sse    # SSE transport (HTTP)
"""

import argparse
import glob
import getpass
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = PLUGIN_ROOT.parent
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_command, run_python
from loop_state_core import compute_rtl_fingerprint

# ---------------------------------------------------------------------------
# 路径推导
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent / "scripts"
SUPPORTED_SIMULATORS = {"iverilog", "vcs", "verilator", "xcelium"}
SUPPORTED_LINT_TOOLS = {"spyglass", "verilator"}
SUPPORTED_CDC_TOOLS = {"spyglass"}
SUPPORTED_SYN_TOOLS = {"yosys", "dc"}
TEST_NAME_RE = re.compile(r"[A-Za-z0-9_.-]+")
HDL_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
SEED_MATRIX_RE = re.compile(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*")
MCP_SERVER_ACTIVE_ENV = "SILICON_CREW_SOC_BUILD_MCP_ACTIVE"
VERDI_SCOPE_CHOICES = {"de", "dv"}


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="soc-build",
    instructions=(
        "SoC 项目脚手架和 EDA Make 目标执行工具。\n"
        "支持项目/模块创建、filelist、lint、编译、仿真、回归、覆盖率和综合。"
    ),
)


def _run(cmd: list[str], cwd: str = None, timeout: int = 120) -> str:
    """Compatibility wrapper retained for tests and downstream imports."""
    return run_command(cmd, cwd=cwd, timeout=timeout)


def _python(script: str, *args: str, cwd: str = None) -> str:
    """调用 scripts/ 目录下的 Python 脚本。"""
    return run_python(SCRIPT_DIR / script, *args, cwd=cwd)


def _module_path(module_dir: str) -> Path:
    """校验模块目录，避免在非 SoC 模块目录执行 Make 目标。"""
    raw_path = Path(module_dir).expanduser()
    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [PROJECT_ROOT / raw_path, Path.cwd() / raw_path]

    path = candidates[0].resolve()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir():
            path = resolved
            break
    if not path.is_dir():
        raise ValueError(f"module_dir is not a directory: {path}")
    if not (path / "Makefile").is_file():
        raise ValueError(f"module Makefile not found: {path / 'Makefile'}")
    return path


def _simulator(value: str) -> str:
    if value not in SUPPORTED_SIMULATORS:
        choices = ", ".join(sorted(SUPPORTED_SIMULATORS))
        raise ValueError(f"unsupported simulator '{value}'; choose one of: {choices}")
    return value


def _syn_tool(value: str) -> str:
    if value not in SUPPORTED_SYN_TOOLS:
        choices = ", ".join(sorted(SUPPORTED_SYN_TOOLS))
        raise ValueError(f"unsupported synthesis tool '{value}'; choose one of: {choices}")
    return value


def _seed(value: int) -> int:
    if value < 0 or value > 2**31 - 1:
        raise ValueError("seed must be between 0 and 2147483647")
    return value


def _tests(value: str, field: str = "tests") -> str:
    if not value:
        return value
    names = value.split(",")
    if len(names) > 256:
        raise ValueError(f"{field} supports at most 256 names")
    if any(not TEST_NAME_RE.fullmatch(name) for name in names):
        raise ValueError(f"{field} must be a comma-separated list of [A-Za-z0-9_.-] names")
    return value


def _seeds(value: str) -> str:
    if not SEED_MATRIX_RE.fullmatch(value):
        raise ValueError("seeds must use comma/range syntax such as 1,3,10-20")
    total = 0
    for item in value.split(","):
        if "-" in item:
            start, end = (int(part) for part in item.split("-", 1))
            if start > end:
                raise ValueError(f"invalid descending seed range: {item}")
            total += end - start + 1
        else:
            start = end = int(item)
            total += 1
        if start > 2**31 - 1 or end > 2**31 - 1:
            raise ValueError("seeds must be between 0 and 2147483647")
        if total > 10000:
            raise ValueError("seed matrix supports at most 10000 runs")
    return value


def _jobs(value: int) -> int:
    if value < 1 or value > 128:
        raise ValueError("jobs must be between 1 and 128")
    return value


def _hdl_identifier(value: str, field: str) -> str:
    if value and not HDL_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field} must be a Verilog identifier")
    return value


def _latest_existing(paths: list[str]) -> str:
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return ""
    return str(max(existing, key=lambda path: path.stat().st_mtime))


def _detect_gui_variables() -> dict[str, str]:
    variables: dict[str, str] = {}
    display = os.environ.get("DISPLAY", "")
    if not display:
        sockets = sorted(Path("/tmp/.X11-unix").glob("X*"))
        if (Path("/tmp/.X11-unix") / "X0").exists():
            display = ":0"
        elif sockets:
            display = f":{sockets[0].name[1:]}"
    if display:
        variables["DISPLAY"] = display

    xauthority = os.environ.get("XAUTHORITY", "")
    if not xauthority:
        user = getpass.getuser()
        xauthority = _latest_existing(glob.glob(f"/run/gdm/auth-for-{user}-*/database"))
    if xauthority:
        variables["XAUTHORITY"] = xauthority

    return variables


def _make(
    module_dir: str,
    targets: list[str],
    variables: dict[str, str | int],
    timeout: int,
) -> str:
    if os.environ.get(MCP_SERVER_ACTIVE_ENV) != "1":
        raise RuntimeError(
            "EDA Make targets must run through the registered soc-build MCP server; "
            "direct Python/Tool object invocation is disabled"
        )
    path = _module_path(module_dir)
    command = ["make", *targets]
    command.extend(f"{name}={value}" for name, value in variables.items())
    return _run(command, cwd=str(path), timeout=timeout)


def _native_evidence_files(path: Path, tool_family: str) -> list[Path]:
    """Return native log/report/netlist candidates, excluding prior evidence."""
    patterns = (
        ("dv/sim/**/sim.log", "dv/sim/**/*.log")
        if tool_family == "soc_sim"
        else (
            "de/syn/**/*.log",
            "de/syn/**/*.rpt",
            "de/syn/**/*netlist*.v",
            "de/syn/**/*netlist*.sv",
            "de/syn/**/*.svf",
            "de/syn/**/*.upf",
        )
    )
    files: set[Path] = set()
    for pattern in patterns:
        for candidate in path.glob(pattern):
            relative = candidate.relative_to(path)
            if candidate.is_file() and "loop_evidence" not in relative.parts:
                files.add(candidate)
    return sorted(files)


def _artifact_signatures(paths: list[Path]) -> dict[Path, tuple[int, int]]:
    return {
        path: (stat.st_mtime_ns, stat.st_size)
        for path in paths
        if (stat := path.stat()).st_size > 0
    }


def _capture_loop_artifacts(
    path: Path,
    tool_family: str,
    run_id: str,
    output: str,
    before: dict[Path, tuple[int, int]],
) -> list[str]:
    """Capture command output and changed native products under a unique run ID."""
    base = path / ("dv/sim" if tool_family == "soc_sim" else "de/syn")
    evidence_dir = base / "loop_evidence" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    primary = evidence_dir / ("sim.log" if tool_family == "soc_sim" else "synth.log")
    primary.write_text(
        output.rstrip() + "\n" if output.strip() else "registered command produced no stdout\n",
        encoding="utf-8",
    )
    captured = [primary]
    for candidate in _native_evidence_files(path, tool_family):
        stat = candidate.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
        # Synthesis-owned products must be fresh. Canonical UPF is a reviewed
        # source input, so capture it even when synthesis correctly leaves it
        # byte-identical; its digest binds downstream Formality/CLP to intent.
        source_input = tool_family == "soc_syn" and candidate.suffix == ".upf"
        if stat.st_size <= 0 or (
            before.get(candidate) == signature and not source_input
        ):
            continue
        relative = candidate.relative_to(path)
        destination = evidence_dir / "native" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, destination)
        captured.append(destination)
    return [item.relative_to(path).as_posix() for item in captured]


def _make_with_loop_evidence(
    module_dir: str,
    targets: list[str],
    variables: dict[str, str | int],
    timeout: int,
    tool_family: str,
) -> str:
    """Run an MCP Make target and bind its success to one immutable RTL snapshot."""
    path = _module_path(module_dir)
    rtl_filelist_target = str(path / "de" / "run" / "rtl.f")
    _make(module_dir, [rtl_filelist_target], {}, timeout=120)
    source_fingerprint = compute_rtl_fingerprint(path)
    if not source_fingerprint:
        raise RuntimeError(
            "cannot create loop evidence: resolved RTL/filelist fingerprint is empty"
        )
    run_id = f"{tool_family}-{uuid.uuid4().hex}"
    before = _artifact_signatures(_native_evidence_files(path, tool_family))
    output = _make(module_dir, targets, variables, timeout)
    final_fingerprint = compute_rtl_fingerprint(path)
    if final_fingerprint != source_fingerprint:
        raise RuntimeError(
            f"RTL/filelist changed during {tool_family}; discard this run and rerun"
        )
    evidence = {
        "run_id": run_id,
        "source_fingerprint": source_fingerprint,
        "tool_family": tool_family,
        "artifacts": _capture_loop_artifacts(
            path, tool_family, run_id, str(output), before
        ),
    }
    return str(output).rstrip() + "\nLOOP_EVIDENCE=" + json.dumps(
        evidence, sort_keys=True
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def soc_init(project_name: str, output_dir: str = ".", top_module: str = "") -> str:
    """初始化标准化 SoC 项目目录结构。

    Args:
        project_name: 项目名称（同时作为目录名和默认顶层模块前缀）
        output_dir: 输出父目录，默认当前目录
        top_module: 顶层模块名，留空则使用 <project_name>_top
    """
    args = ["init", project_name, "-o", output_dir]
    if top_module:
        args += ["-t", top_module]
    return _python("soc_project_init.py", *args)


@mcp.tool()
def soc_add_ip(ip_name: str, project_dir: str, ip_type: str = "digital") -> str:
    """在项目中新增 IP 模块。

    Args:
        ip_name: IP 模块名
        project_dir: 项目根目录路径
        ip_type: IP 类型，可选 digital 或 third_party
    """
    return _python("soc_project_init.py", "add_ip", ip_name, "-p", project_dir, "-t", ip_type)


@mcp.tool()
def soc_add_chip(module_name: str, project_dir: str) -> str:
    """在 chip/ 目录下新增子模块。

    Args:
        module_name: 子模块名，如 core / bus / periph
        project_dir: 项目根目录路径
    """
    return _python("soc_project_init.py", "add_chip", module_name, "-p", project_dir)


@mcp.tool()
def soc_flist(path: str, output: str = "", recursive: bool = False) -> str:
    """递归扫描目录生成 Verilog filelist（.f）。

    Args:
        path: 待扫描的目录路径
        output: 输出 filelist 文件路径，留空则打印到 stdout
        recursive: 是否递归扫描子目录
    """
    args = [path]
    if output:
        args += ["-o", output]
    if recursive:
        args += ["-r"]
    return _python("soc_gen_flist.py", *args)


@mcp.tool()
def soc_lint(
    module_dir: str,
    lint_tool: str = "verilator",
    rtl_top: str = "",
    gui: bool = False,
) -> str:
    """对指定模块执行 lint 检查。

    Args:
        module_dir: 包含 Makefile 的模块目录（如 chip/top 或 ip/digital/xxx）
        lint_tool: lint 工具，可选 verilator / spyglass
        rtl_top: 可选 RTL 顶层模块名
        gui: 是否在 lint 完成后打开图形界面
    """
    if lint_tool not in SUPPORTED_LINT_TOOLS:
        choices = ", ".join(sorted(SUPPORTED_LINT_TOOLS))
        raise ValueError(f"lint_tool must be one of: {choices}")
    variables = {"LINT_TOOL": lint_tool}
    if rtl_top:
        variables["RTL_TOP"] = _hdl_identifier(rtl_top, "rtl_top")
    if gui:
        variables["GUI"] = 1
        variables.update(_detect_gui_variables())
    return _make(module_dir, ["lint"], variables, timeout=120)


@mcp.tool()
def soc_cdc(
    module_dir: str,
    cdc_tool: str = "spyglass",
    rtl_top: str = "",
    gui: bool = False,
) -> str:
    """对指定模块执行 CDC 检查。

    Args:
        module_dir: 包含 Makefile 的模块目录（如 chip/top 或 ip/digital/xxx）
        cdc_tool: CDC 工具；当前 MCP 只允许 spyglass
        rtl_top: 可选 RTL 顶层模块名
        gui: 是否在 CDC 完成后打开图形界面
    """
    if cdc_tool not in SUPPORTED_CDC_TOOLS:
        choices = ", ".join(sorted(SUPPORTED_CDC_TOOLS))
        raise ValueError(f"cdc_tool must be one of: {choices}")
    variables = {"CDC_TOOL": cdc_tool}
    if rtl_top:
        variables["RTL_TOP"] = _hdl_identifier(rtl_top, "rtl_top")
    if gui:
        variables["GUI"] = 1
        variables.update(_detect_gui_variables())
    return _make(module_dir, ["cdc"], variables, timeout=1200)


@mcp.tool()
def soc_comp(module_dir: str, simulator: str = "vcs", top_module: str = "") -> str:
    """编译仿真指定模块。

    Args:
        module_dir: 包含 Makefile 的模块目录
        simulator: 仿真器，可选 iverilog / vcs / verilator / xcelium
        top_module: 可选编译顶层模块名
    """
    variables = {"SIMULATOR": _simulator(simulator)}
    if top_module:
        variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
    return _make(module_dir, ["comp"], variables, timeout=600)


@mcp.tool()
def soc_sim(
    module_dir: str,
    simulator: str = "vcs",
    seed: int = 1,
    test: str = "default",
    top_module: str = "",
    fsdb: bool = False,
) -> str:
    """编译并运行一次仿真，返回含不可变日志路径的 LOOP_EVIDENCE。

    Args:
        module_dir: 包含 Makefile 的模块目录
        simulator: 仿真器，可选 iverilog / vcs / verilator / xcelium
        seed: 非负随机种子
        test: 安全的测试名；模块可通过 TEST 变量使用该值
        top_module: 可选 testbench 顶层模块名
        fsdb: 是否打开 FSDB 波形；映射到 Make 变量 FSDB=1
    """
    variables = {
        "SIMULATOR": _simulator(simulator),
        "SEED": _seed(seed),
        "TEST": _tests(test, "test"),
    }
    if top_module:
        variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
    if fsdb:
        variables["FSDB"] = 1
    return _make_with_loop_evidence(
        module_dir,
        ["comp", "sim"],
        variables,
        timeout=1800,
        tool_family="soc_sim",
    )


@mcp.tool()
def soc_regress(
    module_dir: str,
    simulator: str = "vcs",
    tests: str = "",
    seeds: str = "1",
    jobs: int = 1,
    top_module: str = "",
) -> str:
    """执行模块的多测试、多 seed 回归。

    Args:
        module_dir: 包含 Makefile 和 regress 目标的模块目录
        simulator: 仿真器，可选 iverilog / vcs / verilator / xcelium
        tests: 可选的逗号分隔测试名；留空时使用模块 dv/tests/tests.list
        seeds: seed 列表或范围，例如 1,3,10-20
        jobs: 并发任务数，范围 1..128
    """
    variables: dict[str, str | int] = {
        "SIMULATOR": _simulator(simulator),
        "REGRESS_SEEDS": _seeds(seeds),
        "REGRESS_JOBS": _jobs(jobs),
    }
    if tests:
        variables["REGRESS_TESTS"] = _tests(tests)
    if top_module:
        variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
    return _make(module_dir, ["regress"], variables, timeout=43200)


@mcp.tool()
def soc_coverage(
    module_dir: str,
    simulator: str = "vcs",
    mode: str = "single",
    test: str = "default",
    seed: int = 1,
    tests: str = "",
    seeds: str = "1",
    jobs: int = 1,
    top_module: str = "",
) -> str:
    """采集覆盖率并生成模块覆盖率报告。

    Args:
        module_dir: 包含 Makefile 和 coverage 目标的模块目录
        simulator: 仿真器；当前项目通常使用 vcs
        mode: single 执行单次 coverage，regress 执行 coverage-regress
        test: single 模式测试名
        seed: single 模式随机种子
        tests: regress 模式可选逗号分隔测试名
        seeds: regress 模式 seed 列表或范围
        jobs: regress 模式并发任务数，范围 1..128
    """
    simulator = _simulator(simulator)
    if mode == "single":
        variables: dict[str, str | int] = {
            "SIMULATOR": simulator,
            "TEST": _tests(test, "test"),
            "SEED": _seed(seed),
        }
        if top_module:
            variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
        return _make(module_dir, ["coverage"], variables, timeout=3600)
    if mode == "regress":
        variables = {
            "SIMULATOR": simulator,
            "REGRESS_SEEDS": _seeds(seeds),
            "REGRESS_JOBS": _jobs(jobs),
        }
        if tests:
            variables["REGRESS_TESTS"] = _tests(tests)
        if top_module:
            variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
        return _make(module_dir, ["coverage-regress"], variables, timeout=3600)
    raise ValueError("mode must be single or regress")


@mcp.tool()
def soc_syn(module_dir: str, rtl_top: str = "", syn_tool: str = "yosys") -> str:
    """综合指定 RTL 顶层，返回含不可变日志/网表路径的 LOOP_EVIDENCE。

    Args:
        module_dir: 包含 Makefile 和 syn 目标的模块目录
        rtl_top: 可选的 RTL 顶层模块名
        syn_tool: 综合工具，可选 yosys / dc
    """
    variables: dict[str, str | int] = {"SYN_TOOL": _syn_tool(syn_tool)}
    if rtl_top:
        variables["RTL_TOP"] = _hdl_identifier(rtl_top, "rtl_top")
    return _make_with_loop_evidence(
        module_dir,
        ["syn"],
        variables,
        timeout=1200,
        tool_family="soc_syn",
    )


@mcp.tool()
def soc_verdi(
    module_dir: str,
    scope: str = "dv",
    simulator: str = "vcs",
    top_module: str = "",
    test: str = "default",
) -> str:
    """打开模块的 Verdi GUI。

    Args:
        module_dir: 包含 Makefile 的模块目录
        scope: de 只加载 RTL/source；dv 加载仿真数据库和波形
        simulator: 仿真器，可选 iverilog / vcs / verilator / xcelium
        top_module: 可选顶层模块名
        test: 安全的测试名；用于选择模块 Makefile 中的测试配置
    """
    if scope not in VERDI_SCOPE_CHOICES:
        raise ValueError("scope must be de or dv")
    variables: dict[str, str | int] = {
        "SUBDIR": scope,
        "SIMULATOR": _simulator(simulator),
        "TEST": _tests(test, "test"),
    }
    if top_module:
        variables["TOP_MODULE"] = _hdl_identifier(top_module, "top_module")
    return _make(module_dir, ["verdi"], variables, timeout=120)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SoC Build MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    transport = "sse" if args.sse else "stdio"
    os.environ[MCP_SERVER_ACTIVE_ENV] = "1"
    mcp.run(transport=transport)
