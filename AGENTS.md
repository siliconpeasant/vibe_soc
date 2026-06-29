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
