# vibe_soc_top OpenROAD handoff

This directory is the design-owned OpenROAD-flow-scripts handoff for `vibe_soc_top`.

OpenROAD-flow-scripts and OpenROAD source trees remain independent. The default MCP flow runs local ORFS with `jobs=1` and keeps generated output under `pd/openroad/work_local/`.

Local ORFS run:

```bash
make DESIGN_CONFIG=<vibe_soc>/pd/openroad/nangate45/vibe_soc_top/config.mk \
     WORK_HOME=<vibe_soc>/pd/openroad/work_local \
     FLOW_VARIANT=base \
     synth
```

Explicit Docker/Podman run:

```bash
docker run --rm -i \
  -u "$(id -u):$(id -g)" \
  -e FLOW_HOME=/OpenROAD-flow-scripts/flow/ \
  -e WORK_HOME=/work/pd/openroad/work \
  -v "<vibe_soc>:/work" \
  --network host \
  openroad/orfs:latest \
  bash -lc 'cd /OpenROAD-flow-scripts/flow && if [ -f ../env.sh ]; then . ../env.sh; fi; make -j1 synth DESIGN_CONFIG=/work/pd/openroad/nangate45/vibe_soc_top/config.mk WORK_HOME=/work/pd/openroad/work FLOW_VARIANT=base'
```

Generated logs, reports, objects, and results should stay under `pd/openroad/work/` or `pd/openroad/work_local*/`, which are ignored by Git.
