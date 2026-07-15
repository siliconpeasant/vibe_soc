# Loop modes

`loop_context.py` is the machine source of truth for mode, diff scope, owner,
checks, rules, state freshness, and stop conditions. Do not reconstruct its
routing from prose.

| Mode | Diff scope | Completion bar |
|---|---|---|
| `dev` | target workspace | One owner, targeted validation, stage remains open; no synthesis or independent review. |
| `merge` | repository delivery diff | Close only stale `doc -> rtl -> {verif, syn}` evidence, then `soc-reviewer normal`. |
| `signoff` | repository delivery diff | Merge closure plus routed risk checks and `soc-reviewer strict`. |

`LOOP_MODE` and `--mode` set a minimum. The router may raise risk but never
downgrade it. Ordinary test-manifest, comment, formatting, and non-behavioral
documentation edits use their closest lightweight validation instead of
reopening the full RTL pipeline.

In `dev`, use targeted `soc_sim` when a meaningful test exists; because it
compiles first, do not also run `soc_comp`. Use compile-only validation when no
useful simulation exists. Before delivery, rerun with `--mode merge`; reuse only
fingerprint-bound evidence marked fresh by the packet.
