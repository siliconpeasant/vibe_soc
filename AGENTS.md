# Repository Agent Guide

## Agent environment bootstrap

Canonical sources: `.agents/` (roles, rules, skills, `mcp-servers.json`, loop scripts).  
Client adapters are generated — do not hand-edit generated files.

| Client | Config / adapters |
|--------|-------------------|
| Claude | `.claude/agents` → `.agents/agents`, `.claude/skills` → `.agents/skills`, `.mcp.json` |
| Codex | `.codex/agents/*.toml`, `.codex/config.toml`, hooks under `.codex/hooks/` |
| Grok | `.grok/config.toml` (hyphen names `silicon-crew-*`, no colon) |

On a fresh machine or after pulling agent changes:

```bash
# Preferred: one-shot
make agent-setup

# Or step-by-step
make agent-sync          # regenerate profiles + MCP configs
make mcp-setup           # silicon-crew Python venv for MCP servers
make agent-check         # fail if any adapter drifted

# Loop routing packet (source of truth for vibe-soc-loop)
python3 .agents/scripts/loop_context.py . --format text
```

Task worktrees **must not** use system `/tmp`. Set:

```bash
export CODEX_WORKTREE_ROOT=/project/xuanwu9000/user/silicon/vibe_soc/tmp/worktrees
# or any persistent path outside this repo
scripts/prepare_task_worktree.sh <task-slug>
```

`make agent-sync` ensures `tmp/worktrees/` exists. Large scratch stays under `tmp/` (gitignored).

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

Task worktrees must not be created under the system `/tmp`. Before running
`scripts/prepare_task_worktree.sh`, set `CODEX_WORKTREE_ROOT` to a writable,
persistent directory outside the repository. Do not silently fall back to
`/tmp` when the configured directory is unavailable.

Commits stay focused and use short imperative summaries. PR notes state intent, affected modules, checks, evidence, and tool/license assumptions.
