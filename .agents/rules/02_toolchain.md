# SoC tool contract

Use the registered MCP server/tool by logical name. The host may prefix the exposed tool name differently; do not hard-code a product-specific namespace.

| Task | Server | Tool |
|---|---|---|
| project/module scaffolding | `soc-build` | `soc_init`, `soc_add_chip`, `soc_add_ip` |
| filelist | `soc-build` | `soc_flist` |
| lint | `soc-build` | `soc_lint` |
| compile/single simulation | `soc-build` | `soc_comp`, `soc_sim` |
| regression/coverage | `soc-build` | `soc_regress`, `soc_coverage` |
| synthesis | `soc-build` | `soc_syn` |
| physical design | `soc-openroad` | `soc_openroad_init`, `soc_openroad_run`, `soc_openroad_status` |
| ports/top/wrapper/snapshots | `soc-integrate` | corresponding `soc_*` tool |
| YAML registers | `yml2reg` | `yml2reg` |
| Excel registers | `excel-yml-gen` | `excel_yml_gen` |
| CRG requirement design | `crg-req-to-design` | `crg_req_to_design` |
| clock/reset diagrams | `cr-tree-diag-gen` | `cr_tree_diag_gen*` |

`crg_gen`, `io_top_gen`, `gen_asic_memmap`, and `gen_memwrap` belong to the not-yet-registered `crg-gen` server. Do not schedule workflows that require them until it is present.

## Mandatory execution rules

- Lint, compile, simulation, regression, coverage, and synthesis must run through the registered `soc-build` MCP server.
- Direct EDA shell commands and shell `make` fallbacks are forbidden for stage agents. If the MCP tool is unavailable or fails, mark the stage failed and stop.
- MCP process failures must be tool errors, not successful strings containing an exit code.
- Lint uses the complete project filelist and explicit RTL top.
- Simulation compiles before running and records its real log under `dv/sim/`.
- Synthesis uses the complete project filelist. Yosys synthesis is structural evidence, not STA.
- Timing closure may be claimed only from a real STA report. Estimated or hand-written WNS/TNS is invalid.
- OpenROAD-flow-scripts execution must run through the registered `soc-openroad` MCP server. Keep ORFS/OpenROAD source trees independent; design-owned handoff files live under `pd/openroad/`.
