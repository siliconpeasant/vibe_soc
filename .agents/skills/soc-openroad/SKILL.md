---
name: soc-openroad
description: Prepare and run Docker-first OpenROAD-flow-scripts physical-design handoff for silicon-crew SoC projects. Use when Codex needs to generate ORFS config/SDC under pd/openroad, run synth/floorplan/place/cts/route/finish/all stages through Docker/Podman or explicit local ORFS, summarize OpenROAD reports/results, or connect vibe_soc-style RTL projects to OpenROAD.
---

# SoC OpenROAD

## Overview

Use the registered `soc-openroad` MCP server. Prefer Docker/Podman execution with the ORFS image; use local ORFS only when the user explicitly requests `backend=local`. Keep OpenROAD-flow-scripts and OpenROAD source trees independent from the SoC repository; store design-owned handoff files under `pd/openroad/<platform>/<design>/`.

## Layout contract

Use this scheme for vibe_soc-style projects:

```text
<project>/
└── pd/openroad/
    ├── <platform>/<design>/
    │   ├── config.mk
    │   └── constraint.sdc
    └── work/                 # ORFS logs/objects/reports/results; ignored by Git
```

Do not copy RTL into OpenROAD-flow-scripts. The generated `config.mk` points back to project RTL via `$(PROJECT_ROOT)/...` paths. For container runs, the MCP mounts the SoC project at `/work`, so `pd/openroad/<platform>/<design>/config.mk` and `pd/openroad/work` must stay inside the project.

## MCP tools

| Tool | Purpose |
|---|---|
| `soc_openroad_init` | generate portable ORFS `config.mk` and `constraint.sdc` from project filelists |
| `soc_openroad_run` | run an ORFS Make stage through the MCP process; default `backend=auto` uses Docker/Podman and does not silently fall back to local |
| `soc_openroad_status` | summarize ORFS result/report/log files under `pd/openroad/work` |

## Workflow

1. Ensure RTL/lint/synthesis handoff is already valid through `soc-build`.
2. Call `soc_openroad_init` with `project_dir`, `module_dir`, `design_name`, platform, clock/reset ports, and period. For a top-level `vibe_soc` run, use `module_dir=chip/top`, `design_name=vibe_soc_top`, `platform=nangate45`.
3. Review generated `pd/openroad/<platform>/<design>/config.mk` and `constraint.sdc`. Fix clock/reset constraints from design requirements, not guesses.
4. Call `soc_openroad_run` with `stage=synth|floorplan|place|cts|route|finish|all`. Use the default `backend=auto` for Docker/Podman with `docker_image=openroad/orfs:latest` unless the task specifies another image.
5. Call `soc_openroad_status` and record real report/result paths in `pipeline_state.json`.

For explicit local execution, call `soc_openroad_run` with `backend=local` and `orfs_dir=<OpenROAD-flow-scripts>/flow`. Do not use local execution to work around a missing container runtime unless the user approves it.

OpenROAD execution must remain in the registered MCP tool. Do not replace it with direct shell `make` or `openroad` commands from a stage agent.
