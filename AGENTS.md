# Repository Agent Guide

## Scope and layout

`vibe_soc` uses the silicon-crew layout. Chip modules live under `chip/`, reusable IP under `ip/`, OpenROAD handoff files under `pd/openroad/`, and shared tooling under `scripts/`. Module artifacts belong only under:

```text
docs/  de/rtl/  de/run/  de/syn/  dv/tb/  dv/tests/  dv/sim/
```

Do not create legacy root-level `rtl/`, `tb/`, `sim/`, `syn/`, or `constraints/` compatibility trees. Keep generated logs, caches, waveforms, and local tool configuration out of commits.

## Autonomy

For review, diagnosis, or planning, inspect and report without changing source. For change, build, or fix requests, make in-scope local edits and run non-destructive validation without asking first. Confirmation is required only for external writes, destructive actions, or a material expansion of scope. Design choices that change an unapproved interface, clock/reset behavior, address map, safety boundary, or waiver remain explicit blockers.

## SoC Loop

Use `vibe-soc-loop` for feature, RTL, integration, verification, synthesis, or PD work. Run:

```bash
python3 .agents/scripts/loop_context.py <workspace> --format text
```

The packet is the routing source of truth. `dev` scopes discovery to the target workspace and keeps one owner; `merge` and `signoff` inspect the full delivery diff. Read only rules returned by the packet. Its state summary replaces a separate routine `query_state.py` call; query again only after failure, an intentional delivery transition, or when detailed evidence is needed.

Material RTL follows `doc -> rtl -> {verif, syn}`. In `dev`, keep the owned stage open and run the packet's targeted checks. Close stale stages once in `merge`; high-risk interface, register, clock/reset, constraint, top, multi-module, low-power, or PD work uses `signoff`. Never claim completion from stale or fabricated evidence.

EDA stages must use registered MCP tools. Direct simulator, synthesis, STA, OpenROAD, or EDA Make invocation is blocked by policy. `soc_sim` already compiles: during `dev`, use targeted `soc_sim` when a meaningful test exists, otherwise `soc_comp`; do not run both by default.

## Validation and delivery

Run the closest relevant checker for non-EDA changes. MCP/runtime changes must run their focused Python tests, and commit-ready work must run `make check-repo` or its non-EDA checker equivalent. Every new task uses a unique branch from latest `origin/main`: use `scripts/prepare_task_worktree.sh <slug>` when the current checkout is dirty, or `scripts/prepare_task_branch.sh <slug>` in a clean checkout. Never reuse a merged task branch.

Commits stay focused and use short imperative summaries. PR notes state intent, affected modules, checks, evidence, and tool/license assumptions.
