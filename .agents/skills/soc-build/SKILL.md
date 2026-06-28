---
name: soc-build
description: Create and operate canonical SoC project/module scaffolds through registered MCP tools for filelists, lint, compile, simulation, regression, coverage, and synthesis. Use for SoC project setup and any EDA Make-target execution.
---

# SoC Build

Use the registered `soc-build` MCP server. Do not import its FastMCP object directly and do not replace EDA tool calls with shell commands.

## Runtime setup

Project `.codex/config.toml` registers the MCP servers for this direct repo install. If the launcher reports missing Python modules, run:

```bash
.agents/scripts/setup_mcp_env.sh
```

This installs the shared runtime under `${XDG_CACHE_HOME:-$HOME/.cache}/silicon-crew/venv`, outside the repository package. Do not package `.venv`.

## Canonical project layout

Every chip module and IP uses the same structure:

```text
<module>/
├── docs/
├── de/rtl/          # RTL + filelist.f/filelist.mk
├── de/lint/         # lint configuration or reviewed collateral
├── de/cdc/          # CDC configuration or reviewed collateral
├── de/formal/       # formal configuration or reviewed collateral
├── de/run/          # transient lint/build output
├── de/syn/          # SDC, synthesis and STA output
├── dv/tb/           # testbench source
├── dv/verif/        # reusable verification source
├── dv/tests/        # regression test lists
├── dv/sim/          # simulation logs/images/waves
├── dv/cov/          # coverage databases/reports
└── Makefile
```

Pipeline artifacts remain restricted to `docs/`, `de/rtl/`, `de/run/`, `de/syn/`,
`dv/tb/`, and `dv/sim/`; the additional directories are reserved for their
specialized flow configuration and collateral.

Create structure with `soc_init`, `soc_add_chip`, or `soc_add_ip`. Do not create legacy root `rtl/`, `sim/`, `syn/`, or `constraints/` directories.

## Tools

| Tool | Purpose |
|---|---|
| `soc_init` | initialize a SoC project |
| `soc_add_chip` | add a chip module |
| `soc_add_ip` | add a digital/third-party IP |
| `soc_flist` | generate a Verilog/SystemVerilog filelist |
| `soc_lint` | project-filelist lint; accepts `rtl_top` |
| `soc_comp` | compile; accepts `top_module` |
| `soc_sim` | compile then simulate; accepts simulator/test/seed/top |
| `soc_regress` | test/seed matrix regression |
| `soc_coverage` | single or regression coverage |
| `soc_syn` | project-filelist Yosys synthesis; accepts `rtl_top` |
| `soc_verdi` | open Verdi; `scope=de` loads RTL/source, `scope=dv` loads sim DB/waves |

All names, simulators, tests, seeds, and job counts are validated. A nonzero process exit or timeout is an MCP tool error.

## Stage use

- RTL agents call `soc_lint`; no direct Verilator/Icarus fallback.
- Verification agents call `soc_sim` or `soc_regress`; no direct Make/simulator fallback.
- Synthesis agents call `soc_syn`; Yosys output is not STA evidence.
- Commercial simulator/license work must remain in the registered MCP process.
- VC Static lint is run in no-GUI mode by default because the local license set may lack the Verdi plugin features. If GUI is explicitly requested and plugin checkout fails, do not block lint triage on the GUI; use the generated text reports under `de/run/lint/`.
- When lint reports any real rule violation at error or warning severity, first query the local SoC AI knowledge base (`soc-ai-kb`) using the rule/tag name and diagnostic text. If the knowledge base has no relevant guidance, reason from the tool report, RTL, and local coding rules.
- Lint fixes are review-gated: propose the root cause, supporting report lines, and a concrete patch plan to the user. Do not apply a final RTL fix, waiver, or severity downgrade until the user confirms. Temporary repro edits must be clearly marked and restored before any commit.

For Verilog code review, read `references/verilog_coding_style.md` and report mandatory, recommended, and advisory findings with file/line evidence.
