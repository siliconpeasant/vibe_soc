# Staged SoC delivery flow

Daily work has one stage owner (`dev`). `merge` and `signoff` dispatch only stale
stages reported by `loop_context.py`. Side lanes are not pipeline stages.

| Stage | Owner | Completion evidence |
|---|---|---|
| architecture (conditional, pre-pipeline) | `soc-architect` | approved `docs/architecture*.md` |
| doc | `soc-doc-engineer` | complete module documents and passing document audit |
| rtl | `soc-rtl-designer` or specialized generator/integrator | RTL/filelist/constraints and registered checks |
| verif | `soc-verification-engineer` | testbench plus immutable `soc_sim` evidence |
| syn | `soc-synthesis-engineer` | immutable `soc_syn` evidence; STA only from a real report |
| formal (optional) | `soc-synthesis-engineer` | `soc_formal`; skip with note |
| integrate (optional) | `soc-integrator` | top filelist; skip on leaf modules |
| handoff | `soc-synthesis-engineer` | frontend pack + handoff check |
| low-power / CDC/RDC / DFT (side lanes) | `soc-low-power-engineer` / `soc-cdc-engineer` / `soc-dft-engineer` | UPF/CLP; SpyGlass CDC (default) or VC Static CDC/RDC; DFT SGDC + optional `soc_dft` |
| delivery review | `soc-reviewer` | findings and outcome; never a state transition |

Dependencies are `doc -> rtl -> {verif, syn} -> formal -> handoff` (integrate
after rtl). In `dev`, do not fan out every owner per edit. During delivery,
parallel work must have disjoint write ownership and one stage owner must
integrate and validate it.

A downstream owner may repair RTL while its stage is `in_progress`. After its
final registered run, invalidate the opposite downstream stage once. If both
downstream owners need RTL changes in the same RTL epoch, stop the ping-pong:
reopen `rtl in_progress`, settle RTL under its owner, then rerun both consumers.

Architecture is required before affected doc stages when a chip, subsystem,
technology/process, or multi-module contract is not already approved. Generated
tops use `soc-integrator`; generated CRG uses its registered generator. A
missing required role or registered capability is a blocker, not permission to
hand-write generated output.
