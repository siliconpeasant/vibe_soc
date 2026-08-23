---
name: vibe-soc-loop
description: Route vibe_soc feature/RTL/integration/verification/synthesis/register/CRG/CDC/RDC/DFT/low-power/PD requests into the smallest safe Loop execution packet; for SoC work needing task classification, MCP selection, pipeline state, or delivery closure.
---

# vibe_soc loop

Turn the request into one outcome-first packet with the fewest useful tool loops.

1. Resolve root and workspace, then run
   `python3 <root>/.agents/scripts/loop_context.py <workspace> --format text`.
   Request `--mode merge` only for delivery. Never lower returned mode or scope.
2. Treat paths, owner, rules, `required_reads`, checks, budget, cache, and next
   action as authoritative. Read listed `rules` and `required_reads` paths
   before owned edits (RTL full coding style injects this way). Use
   compact state; load full state/logs only on failure.
3. Dispatch one matching owner in `dev`. Use `soc-pipeline` only for multi-stage
   delivery. Parallelize only independent work — normally `verif`+`syn` once
   RTL evidence exists — within `max_parallel_owners`.
4. Before listed resource-heavy checks, perform one preflight for registered
   capability, required inputs, and tool/license availability. Record an
   unavailable lane once, skip only that blocked check, and continue independent
   available work. Never blind-retry a missing license.
5. Reuse every fresh stage. Keep full logs in artifact paths; return compact
   evidence: check status, run ID, source fingerprint, artifact paths, short
   failure tail. A changed fingerprint invalidates reuse.
6. Classify a failure before retrying. Respect the same-failure retry limit and
   one review run per unchanged snapshot. After the limit, stop with the blocker,
   evidence path, and concrete remediation instead of looping.
7. In `dev`, leave the owned stage open. In `merge/signoff`, close only stale
   stages, run the mapped reviewer once, then re-run router readiness.

Do not hand-write generated tops/CRG logic, bypass registered EDA tools, add a
review/signoff pipeline stage, or narrate routine tool calls.
