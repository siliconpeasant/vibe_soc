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
| review gate (post-stage or pre-commit) | `soc-reviewer` | findings with evidence, no state transition |

## Review gate

Dispatch `soc-reviewer` after pipeline-governed work when preparing to commit, when a task claims validation success, or when an independent audit is requested. The reviewer is not a pipeline stage and does not update `pipeline_state.json`; use `13_review_gate.md` for the audit contract.

RTL specialization:

- CRG: use `soc-crg-engineer` only when the `crg-gen` MCP server is registered. Otherwise report the missing capability; never hand-write generated CRG logic.
- Top integration: use `soc-integrator` and the `soc-integrate` MCP server. Never hand-write an auto-generated top.

## Large task decomposition

When a stage is too large for one role agent to handle efficiently, the coordinator may decompose the work across multiple agents automatically. One role agent remains the stage owner and is responsible for final artifact validation, required MCP gate execution, and `pipeline_state.json` updates.

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
