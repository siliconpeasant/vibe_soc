# Registered tool routing

Use logical MCP names; host namespaces may differ.

| Work | Registered tool |
|---|---|
| scaffold/filelist/lint/CDC/compile/sim/regress/coverage/synthesis/debug | `soc-build.soc_*` |
| ports/snapshots/wrappers/generated top | `soc-integrate.soc_*` |
| physical design | `soc-openroad.soc_openroad_*` |
| YAML or Excel registers | `yml2reg.yml2reg`, `excel-yml-gen.excel_yml_gen` |
| CRG requirements/diagrams | `crg-req-to-design.*`, `cr-tree-diag-gen.*` |
| CRG Excel → RTL / SDC | `crg-gen.crg_gen` |

Only schedule tools currently registered in the context. In particular, do not
substitute hand-written clock/reset trees when `crg-gen.crg_gen` applies, and do
not invent an unregistered IO generator.

Execution invariants:

- EDA execution uses registered MCP tools; shell/Make fallbacks are forbidden.
- Lint and synthesis consume the complete project filelist and explicit RTL top.
- `soc_sim` compiles before running. In a dev iteration, choose it when a useful
  test exists; otherwise choose `soc_comp`. Do not run both by default.
- Process failures are tool errors. Verification success requires a real clean
  log; synthesis is structural evidence; timing closure requires a real STA
  report with WNS/TNS.
- OpenROAD runs only through `soc-openroad`; project-owned handoff files remain
  under `pd/openroad/` and external OpenROAD/ORFS source trees stay independent.
