---
name: vibe-soc-loop
description: Coordinate the vibe_soc Codex loop for feature development, RTL/material refactoring, top integration, register generation, CRG design tables, verification recovery, synthesis, OpenROAD physical-design handoff, and independent loop review. Use when a task spans multiple SoC stages, needs pipeline_state.json coordination, asks to "use the loop", or requires choosing among repo skills/MCP tools.
---

# vibe_soc loop

## Overview

Use this skill as the high-level dispatcher for `vibe_soc`. It first builds a
compact context packet, then selects the minimum safe execution mode, rules,
skills, MCP tools, and state transitions.

## Preflight

1. Read repository `AGENTS.md` and `../../rules/00_loop_modes.md`.
2. Resolve the absolute project root and workspace, then run
   `python3 <project_root>/.agents/scripts/loop_context.py <workspace> --format text`.
   `LOOP_MODE` or `--mode` is a minimum; never downgrade the router result.
3. Read only the rule paths returned by the packet. This replaces repeatedly
   loading every pipeline and reviewer contract during `dev`.
4. Resolve the state module, RTL top, and testbench top separately. For
   `chip/top`, the state module is `vibe_soc_top` and the current RTL top is
   `chip_earlgrey_asic`.
5. Query state with `query_state.py <workspace> --compact`. Initialize only when
   absent and only through the validated state helper.
6. Map review depth from mode: `dev=not_run`, `merge=normal`,
   `signoff=strict`. An explicit read-only audit may request `quick`.

## Classification

Classify ownership after mode routing. Lower-level skills and MCP tools execute
work for the selected owner; they never bypass registered-tool or evidence
gates.

| Task class | Minimum mode | Owner | Executor |
|---|---|---|---|
| single-module RTL iteration | `dev` | one RTL stage owner | matching generator or `soc-build` |
| final module delivery | `merge` | `soc-pipeline` / stale stage roles | matching generator, `soc-integrate`, or `soc-build` |
| interface/top/clock/reset/register/constraint/multi-module/PD | `signoff` | `soc-pipeline` / specialized roles | registered integration, build, or PD tool |
| standalone EDA request | router-selected | applicable stage role | `soc-build` |
| read-only port extraction, snapshot, or diff | `dev` | coordinator | `soc-integrate` |
| explicit loop audit | requested review depth | `soc-reviewer` | `check_loop_state.py` and read-only inspection |
| source-table conversion with no RTL output | `dev` | coordinator | matching deterministic generator |

If a required owner role or executor is missing, stop with a precise blocker. Do not hand-roll generated tops, generated CRG logic, direct simulator runs, direct synthesis runs, or OpenROAD shell fallbacks.

## Loop Contract

For pipeline-governed work:

1. Mark the owned stage `in_progress` before editing and keep artifacts under
   `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, and `dv/sim/`.
2. In `dev`, keep one owner and leave `rtl in_progress`. Run the packet's
   registered targeted checks, store optional compact evidence under
   `de/run/loop_evidence/`, and do not claim stage closure.
3. Before delivery, rerun the packet with `--mode merge`. Dispatch only stale
   stages; a fresh fingerprint-bound stage is reused without rerunning it.
4. In `merge` or `signoff`, close a stage only when artifacts and registered
   checks pass and state records current evidence. Run the mapped reviewer once
   after stage closure.
5. On failure, read the real log/report, update state, and loop back to the
   earliest affected stage. MCP unavailability is not permission for a shell
   fallback.
6. If a downstream stage repairs RTL, apply the existing invalidation rules.
   Never add review or signoff as pipeline stages.

## Reporting

Delivery responses must include:

- task classification and selected lower-level skill/tool
- files changed
- state transition or reason no state transition was needed
- checks run with pass/fail evidence, or why checks were not run
- reviewer outcome when review was run or why review was not needed
- next blocked or recommended stage

For `dev`, keep reporting compact: mode, files, targeted checks, current open
stage, and the next delivery action. Do not emit a full reviewer-style report.

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
