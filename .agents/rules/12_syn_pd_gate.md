# Synthesis and physical-design gate

Use this rule for synthesis, timing, and OpenROAD physical-design handoff.

## Synthesis

Synthesis must use the registered `soc-build` MCP server through `soc_syn`. Use the complete project filelist and explicit RTL top. Do not run Design Compiler, Yosys, OpenROAD, ORFS make targets, or STA tools directly from a stage agent.

Record synthesis results in the module `pipeline_state.json` only when the governed pipeline stage is `syn`. `done` requires non-empty artifacts and at least one passing registered check. A structural Yosys run is useful evidence, but it is not timing closure.

Timing closure may be claimed only from a real STA report with WNS/TNS evidence. Estimated timing, hand-written summaries, or missing report paths are invalid.

If synthesis changes any RTL source or RTL filelist while `syn` is `in_progress`, finish synthesis on the final modified RTL and invalidate `verif` back to `pending` once with a note.

## Physical design

Physical-design handoff uses the `soc-openroad` skill and registered `soc-openroad` MCP tools:

- `soc_openroad_init`
- `soc_openroad_run`
- `soc_openroad_status`

Store project-owned OpenROAD collateral under `pd/openroad/`. Keep OpenROAD-flow-scripts and OpenROAD source trees independent from this repository. Do not add a `pd` stage to `pipeline_state.json`; track PD artifacts and report paths in the handoff summary unless a future state-contract rule explicitly changes this.

For `vibe_soc` top-level handoff, prefer `module_dir=chip/top`, `design_name=vibe_soc_top`, and `platform=nangate45` unless the task states otherwise. Require `chip/top/de/run/rtl.f` as the PD RTL source of truth; do not fall back to `de/rtl/filelist.f` for OpenROAD config generation.
