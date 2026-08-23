---
name: dft-gen
description: >
  Check DFT frontend readiness (test_mode/scan/test_rst hooks), generate DFT
  collateral under de/dft/, and package inputs for soc_dft (VC SpyGlass TestMAX).
  Exclusive skill of soc-dft-engineer.
---

# DFT Generator

**Owner role:** `soc-dft-engineer` only. MCP `dft-gen` is connected at the
project parent for routing; execution remains exclusive to this owner through
the role's named MCP inheritance.

**Lane split:** this owner emits DFT readiness reports + design collateral
(SGDC/Tcl notes). **DFT execution** uses registered **`soc-build.soc_dft`**
(Make target `dft`, VC Static / TestMAX, default goal `dft_scan_ready`). Do not
run functional sim, synthesis, Formality, CLP, or OpenROAD from this skill.

Project DFT frontend standard (e.g. 金山文档 *DFT前端实现规范*) is the primary
policy authority when present. Bundled checklist is a bootstrap until that
standard is checked into the workspace.

## Quick Start

```bash
# 1) Readiness: scan RTL top ports/names for DFT hooks
python scripts/dft_gen.py readiness --rtl path/to/top.v -m top --out de/dft/top_dft_readiness.json

# 2) From RTL ports → starter SGDC + optional module notes Tcl
python scripts/dft_gen.py from-rtl --rtl path/to/top.v -m top -o de/dft/top_dft.sgdc --tcl de/dft/top_dft.tcl

# 3) From reviewed YAML → hierarchical SGDC
python scripts/dft_gen.py gen --config de/dft/top_dft.yml -o de/dft/top_dft.sgdc --tcl de/dft/top_dft.tcl
```

Then run VC SpyGlass DFT through the registered MCP (not shell):

```text
soc-build.soc_dft(module_dir=..., rtl_top=..., dft_tool="vc_static")
```

## MCP tools

| Tool | Purpose |
|------|---------|
| `dft_readiness_check` | Port/name heuristics + optional docs scan → JSON/MD readiness |
| `dft_sgdc_from_rtl` | RTL top ports → starter `.sgdc` (+ optional `.tcl`) |
| `dft_sgdc_gen` | YAML/JSON config → `.sgdc` (+ optional `.tcl`) |

Successful generators print a machine-readable `DFT_ARTIFACTS=<json>` line.

## SGDC shape (design record)

SGDC remains a useful human/review artifact and maps conceptually to VC Static
TestMAX constraints (`set_test_mode`, `create_test_clock`, …). Runtime does
**not** use classic SpyGlass `sg_shell` / `run_goal`.

```text
current_design <top>
test_mode -name <path> -value 1
reset -name <path> -value 0
clock -name <path> [-atspeed -testclock -period 5.0 -edge {0 1}]
```

Starter `from-rtl` only sees **top ports**. Hierarchical `test_rstn` /
`dftrstdisable*` / pad clocks require reviewed YAML paths.

## Runtime driver (VCUM)

Registered Make driver: `scripts/dft/vc_dft.tcl` via `vc_static_shell`:

```tcl
set_app_var enable_dft true
analyze / elaborate <top>
# optional: source de/dft/*_vc.tcl or *_lib.tcl
configure_dft_setup -goal dft_scan_ready
check_dft
# optional: configure_dft_setup -goal dft_best_practice ; check_dft
report_violations -app {DFT} ...
```

Prefer a reviewed `de/dft/*_vc.tcl` for real test clocks / test_mode. Without it,
the driver bootstraps from `VC_CLOCK_PORT` / `VC_TEST_MODE_PORT` /
`VC_RESET_PORT` (and related env vars).

## Workflow for the owner agent

1. Locate module, `RTL_TOP`, and filelist.
2. Run `dft_readiness_check`; treat missing **must** categories as blockers.
3. Generate/refresh `de/dft/<top>_dft.sgdc` (and VC setup Tcl when useful).
4. Call `soc_dft` with explicit top; triage `de/run/dft/report_dft.txt`.
5. Hand RTL/CRG gaps to the owning stage agent; re-run after their snapshot.

## Validation

```bash
python -m unittest discover -s tests
```

## Layout

- `SKILL.md` — this file
- `mcp_server.py` — MCP entry
- `scripts/dft_gen.py` — CLI generator / readiness
- `references/dft_frontend_checklist.md` — bootstrap checklist
- `references/dft_sgdc_template.yml` — YAML example
- `tests/` — unit tests
