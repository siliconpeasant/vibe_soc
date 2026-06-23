# vibe_soc_top OpenROAD handoff

This directory is the design-owned OpenROAD-flow-scripts handoff for `vibe_soc_top`.

OpenROAD-flow-scripts and OpenROAD source trees remain independent. Run from the external ORFS `flow/` directory:

```bash
make DESIGN_CONFIG=<vibe_soc>/pd/openroad/nangate45/vibe_soc_top/config.mk \
     WORK_HOME=<vibe_soc>/pd/openroad/work \
     synth
```

Generated logs, reports, objects, and results should stay under `pd/openroad/work/`, which is ignored by Git.
