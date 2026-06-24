#!/usr/bin/env python3
"""OpenROAD-flow-scripts MCP server for silicon-crew."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(PLUGIN_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from mcp_runtime import run_command


MCP_SERVER_ACTIVE_ENV = "SILICON_CREW_SOC_OPENROAD_MCP_ACTIVE"
HDL_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
STAGES = {
    "synth",
    "floorplan",
    "place",
    "cts",
    "grt",
    "globalroute",
    "route",
    "finish",
    "final",
    "all",
    "generate_abstract",
    "clean_all",
}
HDL_SUFFIXES = {".v", ".sv", ".vh", ".svh"}
CONTAINER_PROJECT_DIR = "/work"
CONTAINER_ORFS_DIR = "/OpenROAD-flow-scripts/flow"
DEFAULT_ORFS_IMAGE = "openroad/orfs:latest"
DEFAULT_BACKEND = "local"
DEFAULT_LOCAL_ORFS_DIR = "/project/xuanwu9000/user/silicon/OpenROAD-flow-scripts-master/flow"
LOCAL_ORFS_ENV = "SILICON_CREW_ORFS_DIR"


mcp = FastMCP(
    name="soc-openroad",
    instructions=(
        "OpenROAD-flow-scripts physical-design handoff for silicon-crew projects. "
        "Generate portable ORFS config/SDC under pd/openroad, run ORFS stages, "
        "and summarize generated reports/results."
    ),
)


def _project(project_dir: str) -> Path:
    path = Path(project_dir).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"project_dir is not a directory: {path}")
    return path


def _module(project: Path, module_dir: str) -> Path:
    path = Path(module_dir).expanduser()
    if not path.is_absolute():
        path = project / path
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"module_dir is not a directory: {path}")
    return path


def _identifier(value: str, field: str) -> str:
    if not value or not HDL_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field} must be a Verilog identifier")
    return value


def _stage(value: str) -> str:
    if value not in STAGES:
        raise ValueError(f"stage must be one of: {', '.join(sorted(STAGES))}")
    return value


def _jobs(value: int) -> int:
    if value < 1 or value > 128:
        raise ValueError("jobs must be between 1 and 128")
    return value


def _backend(value: str) -> str:
    normalized = (value or DEFAULT_BACKEND).strip().lower()
    aliases = {"container": "auto"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"auto", "docker", "podman", "local"}:
        raise ValueError("backend must be one of: auto, docker, podman, local")
    return normalized


def _resolve_token(token: str, base: Path, project: Path) -> Path:
    text = token.strip()
    for name in ("SOC", "PROJECT_ROOT"):
        text = text.replace(f"$({name})", str(project))
        text = text.replace(f"${{{name}}}", str(project))
        text = text.replace(f"${name}", str(project))
    path = Path(os.path.expandvars(text)).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _project_make_path(path: Path, project: Path) -> str:
    resolved = path.resolve()
    try:
        return "$(PROJECT_ROOT)/" + resolved.relative_to(project).as_posix()
    except ValueError:
        return resolved.as_posix()


def _discover_filelists(module: Path, project: Path) -> list[Path]:
    run_filelist = module / "de/run/rtl.f"
    if not run_filelist.is_file():
        raise ValueError(f"missing required PD RTL filelist: {run_filelist}")
    return [run_filelist.resolve()]


def _expand_filelist(filelist: Path, project: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    incdirs: list[Path] = []
    seen_filelists: set[Path] = set()

    def add_unique(items: list[Path], path: Path) -> None:
        if path not in items:
            items.append(path)

    def parse(path: Path) -> None:
        path = path.resolve()
        if path in seen_filelists:
            return
        if not path.is_file():
            raise ValueError(f"missing filelist: {path}")
        seen_filelists.add(path)
        for line_no, raw_line in enumerate(path.read_text().splitlines(), 1):
            try:
                tokens = shlex.split(raw_line, comments=True, posix=True)
            except ValueError as exc:
                raise ValueError(f"{path}:{line_no}: invalid filelist syntax: {exc}") from exc
            index = 0
            while index < len(tokens):
                token = tokens[index]
                if token == "-f":
                    index += 1
                    if index >= len(tokens):
                        raise ValueError(f"{path}:{line_no}: -f requires a path")
                    parse(_resolve_token(tokens[index], path.parent, project))
                elif token.startswith("-f") and len(token) > 2:
                    parse(_resolve_token(token[2:], path.parent, project))
                elif token.startswith("+incdir+"):
                    for item in token[len("+incdir+") :].split("+"):
                        if item:
                            add_unique(incdirs, _resolve_token(item, path.parent, project))
                elif not token.startswith(("+", "-")) and Path(token).suffix.lower() in HDL_SUFFIXES:
                    source = _resolve_token(token, path.parent, project)
                    if not source.is_file():
                        raise ValueError(f"{path}:{line_no}: missing RTL source: {source}")
                    add_unique(files, source)
                index += 1

    parse(filelist)
    return files, incdirs


def _rtl_inputs(project: Path, module: Path) -> tuple[list[Path], list[Path], list[Path]]:
    filelists = _discover_filelists(module, project)
    rtl_files: list[Path] = []
    include_dirs: list[Path] = []
    for filelist in filelists:
        files, dirs = _expand_filelist(filelist, project)
        for item in files:
            if item not in rtl_files:
                rtl_files.append(item)
        for item in dirs:
            if item not in include_dirs:
                include_dirs.append(item)
    if not rtl_files:
        raise ValueError(f"no RTL files found through filelists: {filelists}")
    return filelists, rtl_files, include_dirs


def _emit_make_list(name: str, values: list[str]) -> str:
    if not values:
        return f"export {name} =\n"
    lines = [f"export {name} = \\"]
    for index, value in enumerate(values):
        suffix = " \\" if index < len(values) - 1 else ""
        lines.append(f"  {value}{suffix}")
    return "\n".join(lines) + "\n"


def _render_config(
    *,
    project: Path,
    design_name: str,
    platform: str,
    rtl_files: list[Path],
    include_dirs: list[Path],
    core_utilization: int,
    place_density: str,
) -> str:
    rtl_values = [_project_make_path(path, project) for path in rtl_files]
    include_values = [_project_make_path(path, project) for path in include_dirs]
    lines = [
        "# Generated by silicon-crew soc-openroad. Keep this file in the design repo.",
        "THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))",
        "PROJECT_ROOT := $(abspath $(THIS_DIR)/../../../..)",
        f"export DESIGN_NAME = {design_name}",
        f"export DESIGN_NICKNAME = {design_name}",
        f"export PLATFORM = {platform}",
        "",
        _emit_make_list("VERILOG_FILES", rtl_values).rstrip(),
    ]
    if include_values:
        lines.extend(["", _emit_make_list("VERILOG_INCLUDE_DIRS", include_values).rstrip()])
    lines.extend(
        [
            "",
            "export SDC_FILE = $(THIS_DIR)/constraint.sdc",
            "export ABC_AREA ?= 1",
            f"export CORE_UTILIZATION ?= {core_utilization}",
            "export TNS_END_PERCENT ?= 100",
            "export SYNTH_REPEATABLE_BUILD ?= 1",
        ]
    )
    if place_density:
        lines.append(f"export PLACE_DENSITY ?= {place_density}")
    elif platform == "nangate45":
        lines.extend(
            [
                "export PLACE_DENSITY_LB_ADDON ?= 0.20",
                "export PDN_TCL ?= $(PLATFORM_DIR)/grid_strategy-M1-M4-M7.tcl",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_sdc(design_name: str, clock_port: str, reset_port: str, clock_period_ns: float) -> str:
    lines = [
        f"# OpenROAD constraints for {design_name}",
        f"current_design {design_name}",
        "",
        "set clk_name core_clock",
        f"set clk_port_name {clock_port}",
        f"set clk_period {clock_period_ns:g}",
        "set clk_io_pct 0.2",
        "",
        "set clk_port [get_ports $clk_port_name]",
        "create_clock -name $clk_name -period $clk_period $clk_port",
        "",
        "set non_clock_inputs [all_inputs -no_clocks]",
        "set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_name $non_clock_inputs",
        "set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_name [all_outputs]",
    ]
    if reset_port:
        lines.extend(
            [
                "",
                f"set reset_port [get_ports -quiet {reset_port}]",
                "if { [llength $reset_port] > 0 } {",
                "  set_false_path -from $reset_port",
                "}",
            ]
        )
    return "\n".join(lines) + "\n"


def _default_design_config(project: Path, platform: str, design_name: str, backend: str = DEFAULT_BACKEND) -> Path:
    design_dir = project / "pd/openroad" / platform / design_name
    local_config = design_dir / "config.local.mk"
    if backend == "local" and local_config.is_file():
        return local_config
    return design_dir / "config.mk"


def _default_work_home(project: Path, backend: str = DEFAULT_BACKEND) -> Path:
    if backend == "local":
        return project / "pd/openroad/work_local"
    return project / "pd/openroad/work"


def _default_orfs_dir() -> str:
    return os.environ.get(LOCAL_ORFS_ENV, DEFAULT_LOCAL_ORFS_DIR)


def _orfs(orfs_dir: str) -> Path:
    path = Path(orfs_dir).expanduser().resolve()
    if not (path / "Makefile").is_file() or not (path / "scripts/variables.mk").is_file():
        raise ValueError(f"orfs_dir must point to OpenROAD-flow-scripts/flow: {path}")
    return path


def _container_path(path: Path, project: Path, field: str) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(project)
    except ValueError as exc:
        raise ValueError(f"{field} must be inside project_dir for container backend: {resolved}") from exc
    if not relative.parts:
        return CONTAINER_PROJECT_DIR
    return f"{CONTAINER_PROJECT_DIR}/{relative.as_posix()}"


def _detect_engine_family(command: str) -> str:
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return "podman" if command == "podman" else "docker"
    text = f"{result.stdout}\n{result.stderr}".lower()
    if "podman" in text:
        return "podman"
    return "podman" if command == "podman" else "docker"


def _resolve_container_engine(backend: str) -> tuple[str, str] | None:
    candidates = [backend] if backend in {"docker", "podman"} else ["docker", "podman"]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate, _detect_engine_family(candidate)
    return None


def _container_command(
    *,
    engine_command: str,
    engine_family: str,
    project: Path,
    config: Path,
    work: Path,
    target: str,
    flow_variant: str,
    jobs: int,
    docker_image: str,
) -> list[str]:
    container_config = _container_path(config, project, "design_config")
    container_work = _container_path(work, project, "work_home")
    make_args = [
        "make",
        f"-j{jobs}",
        target,
        f"DESIGN_CONFIG={container_config}",
        f"WORK_HOME={container_work}",
        f"FLOW_VARIANT={flow_variant}",
    ]
    inner = "set -e; "
    inner += f"cd {shlex.quote(CONTAINER_ORFS_DIR)}; "
    inner += "if [ -f ../env.sh ]; then . ../env.sh; fi; "
    inner += shlex.join(make_args)

    user_args = ["-u", f"{os.getuid()}:{os.getgid()}"] if hasattr(os, "getuid") else []
    if engine_family == "podman" and hasattr(os, "getuid"):
        user_args = ["--userns=keep-id", "--user", f"{os.getuid()}:{os.getgid()}"]

    return [
        engine_command,
        "run",
        "--rm",
        "-i",
        *user_args,
        "-e",
        "LIBGL_ALWAYS_SOFTWARE=1",
        "-e",
        f"FLOW_HOME={CONTAINER_ORFS_DIR}/",
        "-e",
        f"WORK_HOME={container_work}",
        "-v",
        f"{project}:{CONTAINER_PROJECT_DIR}",
        "--network",
        "host",
        docker_image,
        "bash",
        "-lc",
        inner,
    ]


def _require_active() -> None:
    if os.environ.get(MCP_SERVER_ACTIVE_ENV) != "1":
        raise RuntimeError(
            "OpenROAD-flow-scripts execution must run through the registered "
            "soc-openroad MCP server; direct Python invocation is disabled"
        )


@mcp.tool()
def soc_openroad_init(
    project_dir: str,
    module_dir: str = "chip/top",
    design_name: str = "",
    top_module: str = "",
    platform: str = "nangate45",
    clock_port: str = "clk",
    reset_port: str = "rst_n",
    clock_period_ns: float = 10.0,
    core_utilization: int = 55,
    place_density: str = "",
    output_dir: str = "",
) -> str:
    """Generate ORFS config/SDC under <project>/pd/openroad/<platform>/<design>.

    Args:
        project_dir: SoC project root such as vibe_soc
        module_dir: module workspace relative to project_dir, default chip/top
        design_name: ORFS design name; defaults to top_module or module directory name
        top_module: RTL top module; defaults to design_name
        platform: ORFS platform such as nangate45/sky130hd/asap7
        clock_port: top-level clock port
        reset_port: optional reset port for false-path constraint
        clock_period_ns: clock period in ns
        core_utilization: ORFS CORE_UTILIZATION
        place_density: optional ORFS PLACE_DENSITY override
        output_dir: optional config directory; defaults to pd/openroad/<platform>/<design>
    """
    project = _project(project_dir)
    module = _module(project, module_dir)
    design = _identifier(design_name or top_module or module.name, "design_name")
    _identifier(top_module or design, "top_module")
    _identifier(clock_port, "clock_port")
    if reset_port:
        _identifier(reset_port, "reset_port")
    if clock_period_ns <= 0:
        raise ValueError("clock_period_ns must be positive")
    if core_utilization < 1 or core_utilization > 99:
        raise ValueError("core_utilization must be between 1 and 99")

    filelists, rtl_files, include_dirs = _rtl_inputs(project, module)
    out_dir = Path(output_dir).expanduser() if output_dir else _default_design_config(project, platform, design, "auto").parent
    if not out_dir.is_absolute():
        out_dir = project / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    config = out_dir / "config.mk"
    sdc = out_dir / "constraint.sdc"
    config.write_text(
        _render_config(
            project=project,
            design_name=design,
            platform=platform,
            rtl_files=rtl_files,
            include_dirs=include_dirs,
            core_utilization=core_utilization,
            place_density=place_density,
        )
    )
    sdc.write_text(_render_sdc(design, clock_port, reset_port, clock_period_ns))

    rel_config = config.relative_to(project)
    rel_sdc = sdc.relative_to(project)
    rel_filelists = [str(path.relative_to(project)) for path in filelists]
    rel_rtl = [str(path.relative_to(project)) for path in rtl_files]
    return "\n".join(
        [
            f"[OK] OpenROAD config generated: {rel_config}",
            f"[OK] OpenROAD SDC generated: {rel_sdc}",
            f"[INFO] DESIGN_NAME={design} PLATFORM={platform}",
            f"[INFO] Filelists: {', '.join(rel_filelists)}",
            f"[INFO] RTL files: {', '.join(rel_rtl)}",
        ]
    )


@mcp.tool()
def soc_openroad_run(
    project_dir: str,
    orfs_dir: str = "",
    design_config: str = "",
    stage: str = "synth",
    platform: str = "nangate45",
    design_name: str = "vibe_soc_top",
    flow_variant: str = "base",
    work_home: str = "",
    jobs: int = 1,
    timeout: int = 7200,
    backend: str = DEFAULT_BACKEND,
    docker_image: str = DEFAULT_ORFS_IMAGE,
) -> str:
    """Run an OpenROAD-flow-scripts stage through the registered MCP process.

    Args:
        project_dir: SoC project root
        orfs_dir: OpenROAD-flow-scripts/flow directory; defaults to SILICON_CREW_ORFS_DIR or /project/xuanwu9000/user/silicon/OpenROAD-flow-scripts-master/flow for backend=local
        design_config: config.mk path; defaults to pd/openroad/<platform>/<design>/config.mk
        stage: ORFS make target, e.g. synth/floorplan/place/cts/route/finish/all
        platform: used only for default design_config path
        design_name: used only for default design_config path
        flow_variant: ORFS FLOW_VARIANT
        work_home: output root; defaults to <project>/pd/openroad/work_local for local backend and <project>/pd/openroad/work for container backends
        jobs: make -j value
        timeout: process timeout in seconds
        backend: local/auto/docker/podman; default local uses the local ORFS directory, while auto/docker/podman use containers and never silently fall back to local
        docker_image: container image for docker/podman backend
    """
    _require_active()
    project = _project(project_dir)
    target = _stage(stage)
    _jobs(jobs)
    selected_backend = _backend(backend)
    config = Path(design_config).expanduser() if design_config else _default_design_config(project, platform, design_name, selected_backend)
    if not config.is_absolute():
        config = project / config
    config = config.resolve()
    if not config.is_file():
        raise ValueError(f"design_config not found: {config}")
    work = Path(work_home).expanduser() if work_home else _default_work_home(project, selected_backend)
    if not work.is_absolute():
        work = project / work
    work.mkdir(parents=True, exist_ok=True)

    engine = _resolve_container_engine(selected_backend)
    if selected_backend in {"auto", "docker", "podman"}:
        if engine is None:
            if selected_backend == "auto":
                raise RuntimeError(
                    "container backend unavailable: install Docker/Podman, or call "
                    "soc_openroad_run with backend=local and a valid orfs_dir"
                )
            raise RuntimeError(f"{selected_backend} backend requested but command not found")
        engine_command, engine_family = engine
        command = _container_command(
            engine_command=engine_command,
            engine_family=engine_family,
            project=project,
            config=config,
            work=work,
            target=target,
            flow_variant=flow_variant,
            jobs=jobs,
            docker_image=docker_image,
        )
        output = run_command(command, timeout=timeout)
        backend_label = engine_family
    else:
        flow = _orfs(orfs_dir or _default_orfs_dir())
        command = [
            "make",
            f"-j{jobs}",
            target,
            f"DESIGN_CONFIG={config}",
            f"WORK_HOME={work}",
            f"FLOW_VARIANT={flow_variant}",
        ]
        output = run_command(command, cwd=flow, timeout=timeout)
        backend_label = "local"

    lines = [
        f"[OK] ORFS stage completed: {target}",
        f"[INFO] BACKEND={backend_label}",
        f"[INFO] DESIGN_CONFIG={config}",
        f"[INFO] WORK_HOME={work}",
    ]
    if backend_label in {"docker", "podman"}:
        lines.append(f"[INFO] IMAGE={docker_image}")
    lines.append(output)
    return "\n".join(lines).rstrip()


@mcp.tool()
def soc_openroad_status(
    project_dir: str,
    design_name: str = "vibe_soc_top",
    platform: str = "nangate45",
    flow_variant: str = "base",
    work_home: str = "",
) -> str:
    """Summarize ORFS outputs under <project>/pd/openroad/work_local by default."""
    project = _project(project_dir)
    work = Path(work_home).expanduser() if work_home else _default_work_home(project, DEFAULT_BACKEND)
    if not work.is_absolute():
        work = project / work
    root = work / "results" / platform / design_name / flow_variant
    logs = work / "logs" / platform / design_name / flow_variant
    reports = work / "reports" / platform / design_name / flow_variant
    expected = {
        "synth": root / "1_synth.odb",
        "floorplan": root / "2_floorplan.odb",
        "place": root / "3_place.odb",
        "cts": root / "4_cts.odb",
        "grt": root / "5_1_grt.odb",
        "route": root / "5_route.odb",
        "finish": root / "6_final.odb",
        "gds": root / "6_final.gds",
        "def": root / "6_final.def",
        "verilog": root / "6_final.v",
    }
    summary = {
        "project_dir": str(project),
        "design_name": design_name,
        "platform": platform,
        "flow_variant": flow_variant,
        "work_home": str(work),
        "outputs": {name: {"path": str(path), "exists": path.exists()} for name, path in expected.items()},
        "recent_logs": [str(path) for path in sorted(logs.glob("*.log"))[-10:]] if logs.is_dir() else [],
        "recent_reports": [str(path) for path in sorted(reports.glob("*"))[-20:]] if reports.is_dir() else [],
    }
    return json.dumps(summary, indent=2, sort_keys=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SoC OpenROAD MCP Server")
    parser.add_argument("--sse", action="store_true", help="使用 SSE (HTTP) transport")
    args = parser.parse_args()

    os.environ[MCP_SERVER_ACTIVE_ENV] = "1"
    mcp.run(transport="sse" if args.sse else "stdio")
