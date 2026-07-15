---
name: vibe-soc-loop
description: Route one-sentence vibe_soc feature, RTL, integration, verification, synthesis, register, CRG, low-power, or PD requests into the smallest safe Loop execution packet. Use for SoC work that needs task classification, MCP selection, pipeline state, or delivery closure.
---

# vibe_soc loop

Turn the request into one outcome-first execution packet, then complete it with
the fewest useful tool loops.

1. Resolve the project root and target workspace. Run
   `python3 <root>/.agents/scripts/loop_context.py <workspace> --format text`.
   Use `--mode merge` only when preparing delivery; never lower the returned
   mode or scope.
2. Treat the packet's owner, selected paths, rules, checks, cache, and next
   action as authoritative. Read only listed rules. The packet already contains
   compact state; query full state only after failure or when detailed evidence
   is required.
3. Dispatch one matching owner in `dev`. Use `soc-pipeline` only for
   multi-stage `merge/signoff` closure. Deterministic generators and registered
   MCP tools remain executors, not extra coordinator layers.
4. Complete allowed local edits and validation without pausing. Stop only for a
   failed required check, missing registered capability/evidence, destructive or
   external action, scope expansion, or an unresolved design choice that changes
   an approved contract.
5. In `dev`, leave the owned stage open and report mode, files, checks, and next
   delivery action. In delivery modes, close only stale stages, run the mapped
   reviewer once, then verify readiness with the router.

Do not hand-write generated tops/CRG logic, bypass registered EDA tools, add a
review/signoff pipeline stage, or narrate routine tool calls.
