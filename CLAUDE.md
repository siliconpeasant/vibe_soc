# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`vibe_soc` is a silicon-crew style SoC frontend project. RTL creation and material refactoring follow a gated pipeline:

```text
architecture (optional) -> doc -> rtl -> {verif, syn}
```

Stage role agents produce canonical artifacts under strict artifact roots only:

- documentation: `docs/`
- RTL and filelists: `de/rtl/`
- constraints / synthesis / STA: `de/syn/`
- lint/build transient output: `de/run/`
- testbench: `dv/tb/`
- simulation output: `dv/sim/`

Do not create legacy `rtl/`, `constraints/`, root `sim/`, or root `syn/` directories.

Before dispatching RTL work, read the full silicon-crew rules at `.agents/rules/`, especially `01_swarm_flow.md`, `02_toolchain.md`, and `05_pipeline_state.md`.

## High-level architecture

### Module layout

```text
chip/
  core/       example compute module
  bus/        example bus module
  periph/     peripheral aggregation module
  lib/        reusable library cells
  top/        SoC top; currently an OpenTitan Earlgrey vendor island
ip/
  digital/    in-house digital IP (uart, spi, soc_ip_common, opentitan_tlul, opentitan_uart, ...)
  third_party/ third-party IP wrappers
pd/openroad/  project-owned OpenROAD handoff configs
scripts/      shared Make rules, toolchains, environment setup, hygiene checks
```

Every module or IP uses the same internal structure:

```text
<module>/
  docs/
  de/rtl/           synthesizable RTL and filelist.f / filelist.mk
  de/syn/           SDC, synthesis scripts, netlist deliverables
  de/run/           transient lint/build filelists and logs (gitignored)
  dv/tb/            testbench and test lists
  dv/sim/           simulation logs, waves, cache (gitignored)
  dv/cov/           coverage database and reports (gitignored)
  pipeline_state.json   gated stage tracker
  Makefile
```

### `chip/top` is currently an OpenTitan island

`chip/top` does not contain a native `vibe_soc_top`. It stages an OpenTitan Earlgrey vendor island:

- RTL source: `chip/top/de/rtl/vendor/opentitan/`
- FuseSoC-generated static dependencies: `chip/top/de/rtl/generated/opentitan_fusesoc/`
- Canonical dependency order: `chip/top/de/rtl/filelist.mk` -> `de/run/rtl.f` and `dv/sim/<case>/dut.f`
- Test index: `chip/top/dv/tb/tests/opentitan_cases.manifest.json` plus category JSON shards
- Prebuilt software images: `chip/top/dv/tb/sw/cases/<test>/`
- Default smoke test: `chip_sw_uart_smoketest`
- Native splits should be built as separate modules under `chip/` or `ip/digital/` and wired through each module's `de/rtl/filelist.mk`, not as ad-hoc fallbacks inside `chip/top`.

### Filelists and integration

- `de/rtl/filelist.f` is the canonical RTL filelist.
- `de/rtl/filelist.mk` may include child module filelists to compose a top-level order.
- `make flist` / `make validate-flist` generate and flatten the simulation filelist (`dv/sim/<case>/dut.canonical.f`).
- Top-level integration and port maintenance should use the `soc-integrate` MCP server; do not hand-edit auto-generated top wiring.

## Common commands

Run all commands from the repository root unless noted.

### Setup and environment

```bash
source scripts/setup.sh          # set PROJECT_ROOT, SOC, CHIP_PATH, IP_PATH
make check-env                   # verify toolchain presence
make check-repo                  # check for local paths / license leakage
make list-modules                # list all buildable chip/IP modules
make print-config MODULE=ip/digital/uart SIMULATOR=vcs
```

Per-user tool paths and license settings go in `scripts/local.mk` (copied from `scripts/local.mk.example`). This file is gitignored and must not be committed.

### Build, lint, simulation, regression

All EDA targets accept `MODULE=<path>`. The default module is `chip/top`.

```bash
make lint MODULE=ip/digital/uart LINT_TOOL=verilator
make comp MODULE=chip/top SIMULATOR=vcs
make sim  MODULE=ip/digital/uart SIMULATOR=vcs TEST=uart_all SEED=7
make test MODULE=ip/digital/uart SIMULATOR=vcs TEST=uart_all SEED=7
make regress MODULE=ip/digital/uart REGRESS_SEEDS=1-10 REGRESS_JOBS=4
make coverage MODULE=ip/digital/uart TEST=uart_all SEED=7
make coverage-regress MODULE=ip/digital/uart REGRESS_SEEDS=1-10 REGRESS_JOBS=4
make report MODULE=ip/digital/uart
make verdi MODULE=chip/top
make syn MODULE=ip/digital/uart RTL_TOP=uart
```

For `chip/top` OpenTitan simulations:

```bash
make comp MODULE=chip/top SIMULATOR=vcs
make sim  MODULE=chip/top TEST=chip_sw_uart_smoketest FSDB=0
```

- `FSDB=0` by default; set `FSDB=1` only when you need a debug waveform.
- For a single test with a specific seed, prefer `make test`.
- Regression results are written to `dv/sim/regress/summary.txt` and `summary.json`.

### Synthesis

```bash
make syn MODULE=ip/digital/uart RTL_TOP=uart
```

Yosys structural synthesis produces `de/syn/<top>_netlist.v` and `de/syn/synth.log`. Do not claim timing closure (WNS/TNS) from Yosys output; only a real STA report can justify timing closure.

### OpenROAD physical-design handoff

Project-owned handoff files live under:

```text
pd/openroad/<platform>/<design>/
  config.mk
  constraint.sdc
```

Use the `soc-openroad` MCP server (`soc_openroad_init`, `soc_openroad_run`, `soc_openroad_status`). Do not run OpenROAD-flow-scripts or OpenROAD directly. Keep ORFS source trees outside this repository.

### Pipeline state

Each independent module tracks its state in `pipeline_state.json`. Use the state scripts:

```bash
python3 .agents/scripts/init_state.py <workspace> <module>
python3 .agents/scripts/query_state.py <workspace>
python3 .agents/scripts/update_state.py <workspace> rtl in_progress
python3 .agents/scripts/update_state.py <workspace> rtl done \
  --artifacts "de/rtl/mod.v,de/rtl/filelist.f,de/syn/mod.sdc" \
  --check "soc_lint:passed" \
  --check "soc_sim:passed"
```

A stage is `done` only when its artifacts exist, are non-empty, and every recorded check passes. `verif` and `syn` may run in parallel after `rtl` is `done`. If RTL changes after a downstream stage completes, that downstream stage must be reset to `pending` and re-run.

## Tool contract for stage agents

For RTL/verification/synthesis work, stage agents must call the registered MCP servers. Do not use direct shell `make`, `iverilog`, `vvp`, `vcs`, `yosys`, or OpenROAD fallbacks.

| Task | Server | Tool |
|---|---|---|
| scaffolding | `soc-build` | `soc_init`, `soc_add_chip`, `soc_add_ip` |
| filelist | `soc-build` | `soc_flist` |
| lint | `soc-build` | `soc_lint` |
| compile / single simulation | `soc-build` | `soc_comp`, `soc_sim` |
| regression / coverage | `soc-build` | `soc_regress`, `soc_coverage` |
| synthesis | `soc-build` | `soc_syn` |
| OpenROAD handoff | `soc-openroad` | `soc_openroad_init`, `soc_openroad_run`, `soc_openroad_status` |
| ports / top / wrapper / snapshots | `soc-integrate` | `soc_extract`, `soc_instantiate`, `soc_integrate`, `soc_update`, `soc_snapshot`, ... |
| YAML regfile RTL | `yml2reg` | `yml2reg` |
| Excel regfile RTL | `excel-yml-gen` | `excel_yml_gen` |
| CRG requirement → design tables | `crg-req-to-design` | `crg_req_to_design` |
| clock/reset diagrams | `cr-tree-diag-gen` | `cr_tree_diag_gen*` |

`crg-gen` is not yet registered; do not schedule CRG RTL generation workflows until it is available.

## Coding and style defaults

- Default language is synthesizable Verilog-2005; use SystemVerilog only if the project/module explicitly does.
- Match module name and filename; use `lower_snake_case`.
- Use parameters for configurable values, `localparam` for derived constants.
- Avoid inferred latches unless explicitly justified in the design spec.
- Make width extension/truncation, signedness, CDC, and reset behavior explicit.
- Match reset polarity and sync/async reset behavior exactly as specified.
- Do not suppress lint warnings solely to pass a gate.

## Repository hygiene

Before committing, run:

```bash
make check-repo
git diff --check
git status --short
```

Do not commit `scripts/local.mk`, `scripts/local.sh`, `scripts/local.csh`, simulation/PD run artifacts, waveforms, or unreviewed generated caches. `pd/openroad/work*/`, `pd/openroad/local/`, and `**/config.local.mk` are gitignored.

## Where to look for more detail

- `README.md` covers full workflow, module layout, OpenROAD handoff, register/CRG generation, and coverage details.
- `Makefile` is the unified top-level entry.
- `scripts/common.mk`, `scripts/config.mk`, `scripts/toolchains/*.mk` define the build rules.
- `chip/top/README.md` explains the OpenTitan vendor-island setup.
- `.agents/rules/` contains the gated flow, toolchain, pipeline-state, exception, and coding-style contracts.
