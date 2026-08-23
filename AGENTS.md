# Repository Agent Guide

## Bootstrap

`.agents/` is canonical for roles, rules, skills, MCP config, and Loop scripts;
`.claude/`, `.codex/`, `.grok/` adapters are generated — never hand-edit. After
a fresh clone or agent change: `make agent-setup`. Routing packet:
`python3 .agents/scripts/loop_context.py . --format text`.

Task worktrees: persistent path outside this repo, never `/tmp`:

```bash
export CODEX_WORKTREE_ROOT=/project/xuanwu9000/user/silicon/vibe_soc/tmp/worktrees
scripts/prepare_task_worktree.sh <task-slug>
```

`agent-sync` creates `tmp/worktrees/`; large scratch stays under
gitignored `tmp/`.

## Layout and autonomy

Chip modules under `chip/`, reusable IP under `ip/`, OpenROAD handoff under
`pd/openroad/`, shared tools under `scripts/`. Module artifacts belong only
under `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, `dv/tests/`, or
`dv/sim/`. No legacy root-level artifact trees; never commit logs, caches,
waveforms, local tool config.

Review/diagnosis/planning: inspect without source changes. Change/build/fix:
in-scope edits and non-destructive checks without asking. Confirm external
writes, destructive actions, scope expansion, and changes to unapproved
interface, clock/reset behavior, address map, safety boundary, or waiver.

### Git publish policy

Do **not** auto-publish: default is local-only edit/check/report. No
`git commit`, `git push`, PR, or auto-merge unless the user **explicitly**
asks (上传, push, 提交, commit, 开 PR, open PR, 上库).

- Local commit without push still needs an explicit commit/提交 request.
- Push implies remote visibility; `codex/**`, `feature/**`, `fix/**` pushes
  trigger `auto-pr-automerge`.
- One approval is not a blanket license for later publishes.

## SoC Loop

Use `vibe-soc-loop` for feature, RTL, integration, verification, synthesis, PD
work. The packet is the routing source of truth: `dev` scopes one
workspace+owner; `merge`/`signoff` inspect the delivery diff. Read only
returned rules; re-query state only after failure, intentional delivery
transition, or for detailed evidence.

Material RTL: `doc→rtl→{verif,syn}→formal→handoff` (optional `integrate` after
rtl; formal/integrate skippable with note). EDA work uses registered MCP tools
only. In `dev`, run targeted `soc_sim` when a meaningful test exists, else
`soc_comp`; do not run both by default. Keep the owned stage open. Close stale
stages once in `merge`; `signoff` for high-risk interface, register,
clock/reset, CDC/RDC, DFT, constraint, top, multi-module, low-power, PD work.
Never claim completion from stale or fabricated evidence.

## Validation and delivery

Run the closest checker for non-EDA changes. MCP/runtime changes require
focused Python tests; commit-ready work requires `make check-repo` or its
non-EDA equivalent.

On an explicit publish request, branch off latest `origin/main`
(`prepare_task_worktree.sh` if dirty, `prepare_task_branch.sh` if clean);
never reuse a merged branch. Commits: focused, short imperative. PR
notes: intent, affected modules, checks, evidence, tool/license assumptions.
Until then leave work uncommitted/unpushed and summarize what is local.
