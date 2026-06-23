# SoC gated design flow

Creating or materially refactoring RTL follows a coordinated flow with an optional architecture handoff followed by the gated module pipeline. The primary agent coordinates; role agents own their stage artifacts and checks.

For chip-level, subsystem-level, or multi-module requirements, dispatch `soc-architect` before the gated doc stage to select IP, select technology/process assumptions, and produce the SoC integration architecture document under `docs/`. This is a pre-doc planning role, not a `pipeline_state.json` stage; the gated dependency chain remains `doc -> rtl -> {verif, syn}`.

| Stage | Role | Canonical deliverables |
|---|---|---|
| architecture handoff (conditional pre-doc) | `soc-architect` | `docs/architecture*.md` |
| doc | `soc-doc-engineer` | `docs/*.md` or `docs/<module>/*.md` |
| rtl | `soc-rtl-designer` | `de/rtl/<module>.v`, `de/rtl/filelist.f`, `de/syn/<module>.sdc` |
| verif | `soc-verification-engineer` | `dv/tb/tb_<module>.*`, `dv/sim/sim.log` |
| syn | `soc-synthesis-engineer` | `de/syn/<module>_netlist.v`, `de/syn/synth.log` |

RTL specialization:

- CRG: use `soc-crg-engineer` only when the `crg-gen` MCP server is registered. Otherwise report the missing capability; never hand-write generated CRG logic.
- Top integration: use `soc-integrator` and the `soc-integrate` MCP server. Never hand-write an auto-generated top.

The module pipeline dependencies are `doc -> rtl -> {verif, syn}`. Verification and synthesis may proceed independently after RTL passes. Architecture handoff, when required, must complete before dispatching affected module doc stages. Respect the host runtime's delegation policy; when named agent profiles are unavailable, use the `soc-pipeline` Skill to give a generic subagent the matching role contract.

Only these artifact roots are valid:

- documentation: `docs/`
- RTL/filelists: `de/rtl/`
- constraints, synthesis and STA: `de/syn/`
- testbench and simulation: `dv/tb/`, `dv/sim/`

Do not create legacy `rtl/`, `constraints/`, root `sim/`, or root `syn/` compatibility directories or symlinks.
