# Repository Agent Guide

## Bootstrap

`.agents/` is canonical for roles, rules, skills, MCP configuration, and Loop
scripts. Claude, Codex, and Grok adapters are generated; never hand-edit them.
After a fresh clone or agent change, prefer:

```bash
make agent-setup
```

The equivalent steps are `make agent-sync`, `make mcp-setup`, and
`make agent-check`. Get the routing packet with:

```bash
python3 .agents/scripts/loop_context.py . --format text
```

Task worktrees must use a persistent path outside this repository and never
system `/tmp`:

```bash
export CODEX_WORKTREE_ROOT=/project/xuanwu9000/user/silicon/vibe_soc/tmp/worktrees
scripts/prepare_task_worktree.sh <task-slug>
```

`make agent-sync` creates `tmp/worktrees/`; other large scratch stays under the
gitignored `tmp/` tree.

## Layout and autonomy

Chip modules live under `chip/`, reusable IP under `ip/`, OpenROAD handoff under
`pd/openroad/`, and shared tools under `scripts/`. Module artifacts belong only
under `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, `dv/tests/`, or
`dv/sim/`. Do not add legacy root-level artifact trees or commit logs, caches,
waveforms, or local tool configuration.

For review, diagnosis, and planning, inspect without source changes. For change,
build, or fix requests, make in-scope edits and non-destructive checks without
asking. Confirm external writes, destructive actions, scope expansion, and
choices that alter an unapproved interface, clock/reset behavior, address map,
safety boundary, or waiver.

## SoC Loop

Use `vibe-soc-loop` for feature, RTL, integration, verification, synthesis, and
PD work. The packet is the routing source of truth: `dev`
scopes one workspace and owner; `merge` and `signoff` inspect the delivery diff.
Read only returned rules. Query state again only after failure, an intentional
delivery transition, or when detailed evidence is needed.

Material RTL follows `doc -> rtl -> {verif, syn}`. EDA work must use registered
MCP tools. In `dev`, run targeted `soc_sim` when a meaningful test exists;
otherwise run `soc_comp`; do not run both by default. Keep the owned stage open.
Close stale stages once in `merge`; use `signoff` for high-risk interface,
register, clock/reset, constraint, top, multi-module, low-power, or PD work.
Never claim completion from stale or fabricated evidence.

## Validation and delivery

Run the closest checker for non-EDA changes. MCP/runtime changes require focused
Python tests; commit-ready work requires `make check-repo` or its non-EDA
equivalent. Start every task on a unique branch from latest `origin/main`, using
`prepare_task_worktree.sh` for a dirty checkout or `prepare_task_branch.sh` for a
clean one. Never reuse a merged branch.

Keep commits focused with short imperative summaries. PR notes state intent,
affected modules, checks, evidence, and tool/license assumptions.
