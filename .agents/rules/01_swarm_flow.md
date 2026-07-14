# SoC staged design flow

Creating or materially refactoring RTL enters the Loop, but daily iteration does
not repeatedly close the full delivery pipeline. `00_loop_modes.md` selects the
execution mode. One role agent owns a `dev` inner loop; coordinated stage roles
close the final diff in `merge` or `signoff`.

For chip-level, subsystem-level, or multi-module requirements, the router selects
`signoff`; dispatch `soc-architect` before the gated doc stage to select IP,
technology/process assumptions, and the integration architecture. Architecture
remains a pre-doc handoff rather than a `pipeline_state.json` stage.

| Stage | Role | Canonical deliverables |
|---|---|---|
| architecture handoff (conditional pre-doc) | `soc-architect` | `docs/architecture*.md` |
| doc | `soc-doc-engineer` | `docs/*.md` or `docs/<module>/*.md` |
| rtl | `soc-rtl-designer` | `de/rtl/<module>.v`, `de/rtl/filelist.f`, `de/syn/<module>.sdc` |
| verif | `soc-verification-engineer` | `dv/tb/tb_<module>.*`, `dv/sim/sim.log` |
| syn | `soc-synthesis-engineer` | `de/syn/<module>_netlist.v`, `de/syn/synth.log` |
| delivery review (`merge`/`signoff`) | `soc-reviewer` | findings with evidence, no state transition |

## Review gate

Do not dispatch an independent reviewer for ordinary `dev` iterations. Dispatch
`soc-reviewer normal` once for `merge`, `soc-reviewer strict` for `signoff`, or
the requested mode for an explicit audit. The reviewer is not a pipeline stage
and does not update `pipeline_state.json`.

RTL specialization:

- CRG: use `soc-crg-engineer` only when the `crg-gen` MCP server is registered. Otherwise report the missing capability; never hand-write generated CRG logic.
- Top integration: use `soc-integrator` and the `soc-integrate` MCP server. Never hand-write an auto-generated top.

## Large task decomposition

Keep one stage owner in `dev`; do not create doc, verification, synthesis, and
review handoffs for every edit. In `merge` or `signoff`, or when a stage is
genuinely too large for one owner, the coordinator may decompose disjoint work
across agents. One role agent remains responsible for final validation, MCP
gates, and state updates.

Parallel agents must have explicit, disjoint write ownership. For example, an RTL refactor may split ownership by files such as `npu_top.v`, `npu_mac.v`, `npu_requant.v`, and `npu_spm.v`; a verification task may split bus functional model, reference model, and directed-test implementation. Do not let two agents edit the same file unless the stage owner serializes and reviews the merge.

Sidecar agents may research, draft, or implement bounded pieces, but they do not close the pipeline stage independently. The stage owner integrates their work, runs the registered MCP checks required for that stage, records real artifacts, and reports the final `update_state.py` stdout line.

The module pipeline dependencies are `doc -> rtl -> {verif, syn}`. Verification and synthesis may proceed independently after RTL passes, but their results are valid only for the RTL snapshot they consumed. A downstream stage may make multiple RTL edits while it is `in_progress`; those edits are coalesced and settled once when that stage completes or fails, not after every edit. If verification changes any RTL source or RTL filelist, complete the current simulation on that modified RTL, then invalidate `syn` back to `pending` and rerun synthesis. If synthesis changes any RTL source or RTL filelist, complete the current synthesis on that modified RTL, then invalidate `verif` back to `pending` and rerun simulation. Within one RTL epoch, defined as the interval from `rtl done` until `rtl` is reopened, only one downstream stage may own RTL repair. If the opposite downstream stage also needs RTL changes after the first repair, stop ping-pong by reopening `rtl in_progress`; this invalidates both downstream stages, the RTL owner closes RTL again, and both verification and synthesis rerun. Both reruns must use the registered MCP tools and must finish before the module is considered closed. Architecture handoff, when required, must complete before dispatching affected module doc stages. Respect the host runtime's delegation policy; when named agent profiles are unavailable, use the `soc-pipeline` Skill to give a generic subagent the matching role contract.

Only these artifact roots are valid:

- documentation: `docs/`
- RTL/filelists: `de/rtl/`
- transient build output: `de/run/`
- constraints, synthesis and STA: `de/syn/`
- testbench and simulation: `dv/tb/`, `dv/sim/`

Do not create legacy `rtl/`, `constraints/`, root `sim/`, or root `syn/` compatibility directories or symlinks.
