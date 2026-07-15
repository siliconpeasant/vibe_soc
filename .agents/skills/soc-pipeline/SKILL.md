---
name: soc-pipeline
description: Close stale multi-stage SoC delivery evidence for a router-selected merge or signoff packet. Use only when vibe-soc-loop delegates final architecture, doc, RTL, verification, synthesis, integration, or PD closure; do not use for ordinary dev iterations.
---

# SoC delivery coordinator

Coordinate a `merge` or `signoff` packet; do not author RTL or testbench content.

1. Accept the absolute workspace, objective, approved assumptions, packet mode,
   stale stages, rules, checks, and state summary from `vibe-soc-loop`.
2. If a chip/subsystem/multi-module requirement lacks an approved architecture
   handoff, dispatch `soc-architect` before module stages. Architecture is not a
   pipeline stage.
3. Dispatch only stale stages to their narrow owner. Verification and synthesis
   may run independently after RTL. One owner integrates any bounded sidecars;
   write ownership must not overlap.
4. After each owner returns, validate its artifacts, registered checks, current
   fingerprint, run ID, and state-update result. Stop on failure or missing
   evidence and return to the earliest affected stage.
5. Run `soc-reviewer normal` once for `merge` or `strict` for `signoff`, then
   rerun the context packet with the review result and readiness check.

Required capability, evidence, or approved interface decisions are blockers.
Never substitute direct EDA shell execution, fabricated PASS/timing data, or a
coordinator-authored generated design.
