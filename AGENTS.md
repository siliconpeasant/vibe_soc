# Repository Guidelines

## Project Structure & Module Organization

`vibe_soc` uses a silicon-crew SoC layout. Chip-level modules live under `chip/`, reusable IP under `ip/`, OpenROAD handoff collateral under `pd/openroad/`, and shared Make/tool scripts under `scripts/`. The active chip top is `chip/top`, with OpenTitan vendor-island RTL in `chip/top/de/rtl/vendor/opentitan/`, testbench and software collateral in `chip/top/dv/tb/`, test manifests in `chip/top/dv/tests/`, and per-case outputs in `chip/top/dv/sim/<test>/`.

Each module should follow:

```text
docs/  de/rtl/  de/run/  de/syn/  dv/tb/  dv/tests/  dv/sim/
```

Do not add legacy root-level `rtl/`, `tb/`, `sim/`, `syn/`, or `constraints/` compatibility directories.

## Build, Test, and Development Commands

The Make examples below are for human developers. Agents must use registered MCP tools for EDA stages.

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

Human verification may use the Make flow below. Agent verification must use `soc-build.soc_sim`, never direct Make or simulator commands. Preferred human smoke check is:

```bash
make sim MODULE=chip/top SIMULATOR=vcs TEST=chip_sw_uart_smoketest SEED=1
```

For MCP changes, run:

```bash
.agents/scripts/run_mcp_python.sh .agents/skills/soc-build/tests/test_mcp_server.py
```

## Commit & Pull Request Guidelines

Commit messages are short, imperative summaries, for example `Update simulation toolchain controls` or `Split OpenTitan RTL into native IP filelists`. Keep commits focused and exclude waveforms, simulator caches, local config, and personal files. PRs should describe intent, list affected modules, include commands run, and call out any known tool or license assumptions.

Every new task must use a fresh branch created from the latest remote default
branch. Before making task changes, run:

```bash
scripts/prepare_task_branch.sh <task-slug>
```

Never push new commits to a branch whose pull request has already merged. Do
not reuse a prior `codex/**`, `feature/**`, or `fix/**` branch for another
task. The automatic PR workflow rejects reuse of a previously merged head
branch.

## Agent-Specific Instructions

For RTL creation or material refactoring, enter the repository Loop and update
`pipeline_state.json` when applicable. Daily single-module work uses the `dev`
inner loop; the gated `doc -> rtl -> {verif, syn}` closure runs once in `merge`
or `signoff`. EDA stages must use registered MCP tools such as
`soc-build.soc_sim`, `soc-build.soc_syn`, and `soc-openroad`; do not bypass them
with direct shell simulator or synthesis invocations.

## Codex Loop Workflow

For feature, RTL, integration, verification, synthesis, or physical-design tasks, use the repository loop instead of an ad hoc edit-and-run flow:

1. Run `python3 .agents/scripts/loop_context.py <workspace> --format text` before planning. Its compact packet selects `dev`, `merge`, or `signoff`, automatically raises risky changes, and lists only the rules that must be read.
2. Use `vibe-soc-loop` as the high-level dispatcher and the matching repo skill or registered MCP tool as executor.
3. In `dev`, use one stage owner, keep material RTL work `rtl in_progress`, and run targeted registered lint/compile/simulation. Do not close delivery stages or run synthesis/reviewer on every edit.
4. Before PR or delivery, rerun with `--mode merge`, complete only stale stages, and run `soc-reviewer normal`. Verify readiness afterward with `--review-result pass --check-ready`. High-risk changes automatically use `signoff` and `soc-reviewer strict`.
5. Mark stages `in_progress`, `done`, `fail`, or invalidated `pending` only through the validated state helpers. Use `query_state.py <workspace> --compact` for routine coordination.
6. If a stage fails, inspect the real log/report first and loop back to the earliest affected stage. Never continue from stale evidence or fabricate simulation, synthesis, timing, or PD success.
7. When the same mistake recurs, update the smallest applicable rule, skill, checker, or hook so later sessions inherit the correction.
