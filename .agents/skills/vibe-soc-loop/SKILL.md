---
name: vibe-soc-loop
description: Coordinate the vibe_soc Codex loop for feature development, RTL/material refactoring, top integration, register generation, CRG design tables, verification recovery, synthesis, OpenROAD physical-design handoff, and independent loop review. Use when a task spans multiple SoC stages, needs pipeline_state.json coordination, asks to "use the loop", or requires choosing among repo skills/MCP tools.
---

# vibe_soc loop

## Overview

Use this skill as the high-level dispatcher for `vibe_soc`. It selects the correct repo rules, skills, MCP tools, and state transitions without duplicating the lower-level skill contracts.

## Preflight

1. Read repository `AGENTS.md`.
2. Read required rules before planning:
   - always for pipeline work: `../../rules/01_swarm_flow.md`, `../../rules/02_toolchain.md`, `../../rules/05_pipeline_state.md`
   - material RTL change: `../../rules/10_rtl_change_gate.md`
   - verification failure/recovery: `../../rules/11_verif_recovery_gate.md`
   - synthesis or PD: `../../rules/12_syn_pd_gate.md`
   - review or commit readiness: `../../rules/13_review_gate.md`
   - manual RTL style: `../../rules/04_coding_style.md`
   - design decisions: `../../rules/06_design_knowledge.md`
3. Resolve the absolute project root, workspace, state module name, RTL top, and testbench top separately. For `chip/top`, the state module is `vibe_soc_top` while the current RTL top is `chip_earlgrey_asic`; never infer one from the other.
4. Query existing `pipeline_state.json` before stage work. Initialize only when absent and only through the validated state helper.
5. For review requests, select `review_mode=quick|normal|strict`; default to `normal`, use `quick` for dry-run planning, and use `strict` before commit or PR.

## Classification

Classify ownership before selecting an executor. Any generated top, wrapper, register RTL, CRG RTL, RTL/filelist, interface, or constraint change is pipeline-governed and must be owned by `soc-pipeline` plus the applicable stage role. Lower-level skills and MCP tools execute work for that owner; they do not bypass state gates.

| Task class | Owner | Executor |
|---|---|---|
| architecture, material RTL, generated RTL/top/wrapper, multi-stage recovery | `soc-pipeline` / stage role | matching generator, `soc-integrate`, or `soc-build` |
| standalone lint/compile/simulation/regression/coverage/synthesis request | applicable stage role | `soc-build` |
| read-only port extraction, snapshot, or interface diff | coordinator | `soc-integrate` |
| OpenROAD physical-design handoff | `soc-pd-engineer` | `soc-openroad` |
| loop audit, validation evidence, commit readiness | `soc-reviewer` | `check_loop_state.py` and read-only inspection |
| approved source-table conversion with no RTL output | coordinator | `excel-yml-gen`, `crg-req-to-design`, or `cr-tree-diag-gen` |

If a required owner role or executor is missing, stop with a precise blocker. Do not hand-roll generated tops, generated CRG logic, direct simulator runs, direct synthesis runs, or OpenROAD shell fallbacks.

## Loop Contract

For pipeline-governed work:

1. Mark the owned stage `in_progress` before editing stage artifacts.
2. Keep artifacts under the approved roots: `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, and `dv/sim/`.
3. Run required checks through registered MCP tools. Treat MCP unavailability as a stage blocker or failure, not permission to bypass the flow.
4. On failure, read the real log/report, classify the failure, update state when applicable, and loop back to the earliest affected stage.
5. Close a stage only when artifacts exist, all recorded checks pass, and `pipeline_state.json` records the real evidence.
6. If a downstream stage repairs RTL, apply the invalidation rules from `01_swarm_flow.md` and `05_pipeline_state.md` before declaring closure.
7. For post-stage review or commit readiness, dispatch `soc-reviewer` after the stage owner finishes. Treat review findings as follow-up work; do not add a `review` stage to `pipeline_state.json`.
8. When a module workspace is available, run `.agents/scripts/check_loop_state.py <workspace> --mode <review_mode>` as read-only evidence for the reviewer or final response.
9. Reviewer dispatches include the implicated review domains, available reports/deliverables, `knowledge_scope`, and requested top-risk count. Require the structured report sections from `13_review_gate.md`. If `soc-ai-kb` is unavailable, require explicit knowledge gaps and `Need Human Confirmation` rather than invented rules.

## Reporting

Final responses for loop work must include:

- task classification and selected lower-level skill/tool
- files changed
- state transition or reason no state transition was needed
- checks run with pass/fail evidence, or why checks were not run
- reviewer outcome when review was run or why review was not needed
- next blocked or recommended stage

## Evidence Summary

For completed loop work, include a compact evidence block:

```text
loop_evidence:
  module: <workspace or module>
  task_class: <classification>
  review_mode: <quick|normal|strict|not_run>
  state: <stage/status summary>
  tools: [<registered MCP tools or checker scripts>]
  artifacts: [<relative evidence paths>]
  result: <pass|needs-fix|needs-validation|blocked|not_run>
```
