---
name: soc-pipeline
description: Orchestrate SoC architecture planning plus gated RTL creation, refactoring, verification, synthesis, OpenROAD physical-design handoff, CRG routing, and top integration. Use when Codex must plan chip/subsystem architecture, select SoC IP, select technology/process assumptions, create or materially change Verilog/SystemVerilog modules, coordinate stage agents, prepare physical-design handoff, or recover a failed silicon-crew pipeline.
---

# SoC Pipeline

Coordinate delivery work. A `dev` request uses one stage owner; `merge` and
`signoff` coordinate only the stages marked stale by the compact context packet.
Do not implement RTL or testbench content in the coordinator.

## Preflight

1. Run `loop_context.py <workspace>` and read only the returned rules. Never
   lower its selected `dev`, `merge`, or `signoff` mode.
2. Resolve the absolute module workspace and module name.
3. Query compact state; initialize only when absent. Never overwrite state.
4. For chip-level, subsystem-level, or multi-module requirements without an approved architecture handoff, dispatch `soc-architect` first for IP selection, technology/process selection, and the overall SoC integration architecture plan. Treat it as pre-doc planning, not a `pipeline_state.json` stage.
5. Select the RTL role:
   - normal logic: `soc-rtl-designer`
   - top integration: `soc-integrator`
   - CRG: `soc-crg-engineer`, only when `crg-gen` is registered
   - OpenROAD physical-design handoff: `soc-pd-engineer`
6. Do not select a reviewer for `dev`. Select `soc-reviewer normal` once for
   `merge` and `strict` for `signoff`; it never closes a pipeline stage.
7. Reviewer dispatch includes relevant review domains, reports and delivery inputs, knowledge-base scope, and the structured output contract from `13_review_gate.md`. Missing knowledge-base rules require `Need Human Confirmation`; they are never synthesized from memory.

## Delegation

Use one named RTL role in `dev` when supported. Otherwise use a generic
subagent with the matching contract. Do not fan out doc, verification,
synthesis, and review roles until `merge/signoff` requires their stale stages.
Respect host delegation policy and do not replace a required role with
coordinator-authored RTL.

For large stage tasks, the coordinator may split work across multiple agents automatically when the host allows it. Keep one role agent as the stage owner. Sidecar agents must have explicit, disjoint write ownership and may not independently close the stage. The stage owner integrates sidecar work, runs the required registered MCP checks, validates artifacts, and updates `pipeline_state.json`.

Every dispatch prompt includes:

- absolute `workspace`
- `task_name`
- objective and approved assumptions
- single- or multi-module state mode
- for pipeline-stage agents only, requirement to update state and quote the `update_state.py` stdout line

In `dev`, query again only after failure or transition to delivery. In
`merge/signoff`, query after each stale-stage owner returns and verify status,
artifacts, and checks. Dispatch the mapped reviewer after closure. Do not
dispatch downstream work after failure.

## Execution contract

- Canonical artifact paths: `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, `dv/sim/`.
- Architecture handoff artifacts stay under `docs/` and must cover IP selection, technology/process selection, and the integration architecture before the doc stage consumes them.
- EDA execution uses registered MCP tools. Verification calls `soc-build.soc_sim`; synthesis calls `soc-build.soc_syn`; physical-design handoff calls `soc-openroad.soc_openroad_*`. No direct EDA shell fallback.
- `doc -> rtl`; verification and synthesis may run independently after RTL passes.
- Treat estimated timing and synthetic PASS markers as failures of validation integrity.
- For an approved doc-stage exception, record `doc skipped` with a concrete note before starting RTL.

Stop and report a precise blocker if required MCP capability, an approved interface decision, or an EDA dependency is unavailable.
