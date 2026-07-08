# Repository Guidelines

## Project Structure & Module Organization

`vibe_soc` uses a silicon-crew SoC layout. Chip-level modules live under `chip/`, reusable IP under `ip/`, OpenROAD handoff collateral under `pd/openroad/`, and shared Make/tool scripts under `scripts/`. The active chip top is `chip/top`, with OpenTitan vendor-island RTL in `chip/top/de/rtl/vendor/opentitan/`, testbench and software collateral in `chip/top/dv/tb/`, test manifests in `chip/top/dv/tests/`, and per-case outputs in `chip/top/dv/sim/<test>/`.

Each module should follow:

```text
docs/  de/rtl/  de/run/  de/syn/  dv/tb/  dv/tests/  dv/sim/
```

Do not add legacy root-level `rtl/`, `tb/`, `sim/`, `syn/`, or `constraints/` compatibility directories.

## Build, Test, and Development Commands

Run from the repository root unless noted:

```bash
make check-env
make list-modules
make validate-flist MODULE=chip/top
make lint MODULE=ip/digital/uart
make comp MODULE=chip/top SIMULATOR=vcs
make sim MODULE=chip/top SIMULATOR=vcs TEST=chip_sw_uart_smoketest SEED=1
make sim MODULE=chip/top SIMULATOR=vcs TEST=chip_sw_uart_smoketest FSDB=1
make verdi MODULE=chip/top TEST=chip_sw_uart_smoketest
```

Use `FSDB=1` only when waveform debug is needed. Run `make check-repo` before committing to catch local paths and license leaks.

## Coding Style & Naming Conventions

Keep RTL SystemVerilog consistent with nearby OpenTitan/vibe_soc code. Use lowercase snake_case for modules, signals, tests, and directories. Put RTL source lists in `de/rtl/filelist.f` and composition logic in `filelist.mk`. Keep generated or transient logs in `de/run/` and `dv/sim/`; these should not be committed.

## Testing Guidelines

Verification must use the project Make/MCP flow, not direct simulator commands. Preferred smoke check is:

```bash
make sim MODULE=chip/top SIMULATOR=vcs TEST=chip_sw_uart_smoketest SEED=1
```

For MCP changes, run:

```bash
.agents/scripts/run_mcp_python.sh .agents/skills/soc-build/tests/test_mcp_server.py
```

## Commit & Pull Request Guidelines

Commit messages are short, imperative summaries, for example `Update simulation toolchain controls` or `Split OpenTitan RTL into native IP filelists`. Keep commits focused and exclude waveforms, simulator caches, local config, and personal files. PRs should describe intent, list affected modules, include commands run, and call out any known tool or license assumptions.

## Agent-Specific Instructions

For RTL creation or material refactoring, follow the gated `doc -> rtl -> {verif, syn}` workflow and update `pipeline_state.json` when applicable. EDA stages must use registered MCP tools such as `soc-build.soc_sim`, `soc-build.soc_syn`, and `soc-openroad`; do not bypass them with direct shell simulator or synthesis invocations.

## Codex Loop Workflow

For feature, RTL, integration, verification, synthesis, or physical-design tasks, use the repository loop instead of an ad hoc edit-and-run flow:

1. Read the relevant `.agents/rules` files before planning. Pipeline dispatch requires `01_swarm_flow.md`, `02_toolchain.md`, and `05_pipeline_state.md`; read coding style, exception, and design-knowledge rules when the task touches those areas.
2. Classify the request as docs-only, RTL/material refactor, top integration, register generation, CRG design, verification, synthesis, OpenROAD physical-design handoff, or review/commit readiness.
3. Use the matching repo skill or MCP tool. Prefer `vibe-soc-loop` as the high-level entrypoint when the task spans multiple stages.
4. Mark pipeline stages `in_progress`, `done`, `fail`, or invalidated `pending` through the validated `pipeline_state.json` flow when the task is governed by the module pipeline.
5. If a stage fails, inspect the real log/report artifact first, identify the earliest affected stage, and loop back there. Do not continue downstream from a failed or stale stage.
6. A stage is complete only when required artifacts exist, recorded checks pass, and the result was produced by the registered MCP flow. Never claim simulation, synthesis, timing, or physical-design success from estimated or fabricated evidence.
7. After pipeline-governed work, use `soc-reviewer` or the review gate when preparing to commit, when validation success is claimed, or when the loop touched RTL, verification, synthesis, integration, or PD handoff. Do not add a review stage to `pipeline_state.json`.
8. When the same mistake recurs, propose a targeted update to `AGENTS.md`, `.agents/rules`, a repo skill, or a hook so future sessions inherit the correction.
