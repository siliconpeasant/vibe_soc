---
name: soc-openroad
description: Prepare and run local-default OpenROAD-flow-scripts physical-design handoff for silicon-crew SoC projects. Use when Codex needs to generate ORFS config/SDC under pd/openroad, run synth/floorplan/place/cts/route/finish/all stages through the default local ORFS path or explicit container backends, summarize OpenROAD reports/results, or connect vibe_soc-style RTL projects to OpenROAD.
---

# SoC OpenROAD

## Overview

Use the registered `soc-openroad` MCP server. Prefer the validated local ORFS execution path with `backend=local`, `orfs_dir=${SILICON_CREW_ORFS_DIR}`, and `jobs=1`. Use Docker/Podman only when explicitly requested with `backend=auto`, `backend=docker`, or `backend=podman`. Keep OpenROAD-flow-scripts and OpenROAD source trees independent from the SoC repository; store design-owned handoff files under `pd/openroad/<platform>/<design>/`.

## Layout contract

Use this scheme for vibe_soc-style projects:

```text
<project>/
└── pd/openroad/
    ├── <platform>/<design>/
    │   ├── config.mk
    │   └── constraint.sdc
    └── work_local/           # default local ORFS logs/objects/reports/results; ignored by Git
```

Do not copy RTL into OpenROAD-flow-scripts. The generated `config.mk` points back to project RTL via `$(PROJECT_ROOT)/...` paths. For container runs, the MCP mounts the SoC project at `/work`, so `pd/openroad/<platform>/<design>/config.mk` and `pd/openroad/work` must stay inside the project.

## MCP tools

| Tool | Purpose |
|---|---|
| `soc_openroad_init` | generate portable ORFS `config.mk` and `constraint.sdc` from project filelists |
| `soc_openroad_run` | run an ORFS Make stage through the MCP process; default `backend=local` uses the validated local ORFS path and `jobs=1`; container backends are explicit and never silently fall back |
| `soc_openroad_status` | summarize ORFS result/report/log files under `pd/openroad/work_local` by default |

## Workflow

1. Ensure RTL/lint/synthesis handoff is already valid through `soc-build`.
2. Call `soc_openroad_init` with `project_dir`, `module_dir`, `design_name`, platform, clock/reset ports, and period. For a top-level `vibe_soc` run, use `module_dir=chip/top`, `design_name=vibe_soc_top`, `platform=nangate45`.
3. Require the module build filelist `de/run/rtl.f` as the PD RTL source of truth. If `de/run/rtl.f` is missing, stop before OpenROAD config generation and report the missing build artifact; do not fall back to `de/rtl/filelist.f`. After `soc_openroad_init`, review `config.mk` and confirm `VERILOG_FILES` was derived from `de/run/rtl.f` with portable `$(PROJECT_ROOT)/...` paths so local and container runs can see the files.
4. Review generated `pd/openroad/<platform>/<design>/config.mk` and `constraint.sdc`. Fix clock/reset constraints from design requirements, not guesses.
5. Call `soc_openroad_run` with `stage=synth|floorplan|place|cts|route|finish|all`. By default this uses `backend=local`, `orfs_dir=${SILICON_CREW_ORFS_DIR}`, `jobs=1`, and `pd/openroad/work_local`. For local backend, prefer `config.local.mk` when it exists because it selects the validated `openroad-local` wrappers and compatibility Tcl.
6. Call `soc_openroad_status` and record real report/result paths in the PD handoff summary. PD is not a `pipeline_state.json` stage.

For container execution, explicitly call `soc_openroad_run` with `backend=auto|docker|podman` and the desired image. Container execution must not silently fall back to local.

OpenROAD execution must remain in the registered MCP tool. Do not replace it with direct shell `make` or `openroad` commands from a stage agent.
