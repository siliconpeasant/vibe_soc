# Pipeline state contract

Each independently developed module owns `pipeline_state.json`: a validated
coordination signal, not a narrative log. `loop_context.py` includes the
routine compact view; use `query_state.py <workspace> --compact` only for
failure investigation, intentional delivery transitions, or detailed evidence.

## Stages

Stage | Owner | Notes
---|---|---
`doc` | `soc-doc-engineer` | skip only with approved exception note
`rtl` | `soc-rtl-designer` | material RTL epoch root
`verif` | `soc-verification-engineer` | parallel with syn after rtl
`syn` | `soc-synthesis-engineer` | pre-synthesis / DC snapshot
`formal` | `soc-synthesis-engineer` | optional gate; skip with note
`integrate` | `soc-integrator` | optional; skip on leaf modules
`handoff` | `soc-synthesis-engineer` | frontend pack; needs verif+syn+formal+integrate done/skipped

Architecture, low-power UPF/CLP, CDC/RDC, PD, review remain external
handoffs/side lanes, not replacements for these stages.

Dependencies are machine-enforced in `loop_state_core.py`. `formal`/`integrate`
may be `skipped` with `--note`; `handoff` still requires them `done` or
`skipped` (success set).

```text
blocked→pending→in_progress→done
                        ↘ fail→in_progress
pending→skipped               # doc|formal|integrate only
done/in_progress/fail→pending # explicit invalidation with note
done→in_progress              # reopen; invalidates consumers
```

Use `init_state.py` only when state is absent, `update_state.py` for every
transition; mark `in_progress` before work. `done` requires existing non-empty
canonical artifacts, all required checks passing, and (rtl/verif/syn/formal) a
current RTL fingerprint. `verif`/`syn`/`formal` also require `run_id`,
`source_fingerprint`, and immutable artifact paths from their registered MCP
run (`soc_sim`/`soc_syn`/`soc_formal`). Failure records a failed check +
remediation note.

RTL reopen invalidates `verif`/`syn`/`formal`/`integrate`/`handoff`; new
`syn` done invalidates `formal`/`handoff` when already active or closed.

In `dev`, targeted checks are task evidence but do not close stages; in
`merge/signoff`, close only packet-stale stages. If verification repairs RTL,
finish its final simulation and invalidate synthesis once (inverse for
synthesis repair); if the other consumer also needs RTL repair, reopen RTL and
rerun both consumers after it closes.

Example:

```bash
python3 .agents/scripts/update_state.py <workspace> rtl done \
  --artifacts "de/rtl/mod.v,de/rtl/filelist.f" \
  --check "soc_lint:passed" --check "soc_comp:passed" \
  --check "rtl_quality:passed"
```

Multi-module state: add `--module <name>`. Dispatch inputs carry absolute
workspace, module, packet mode, objective, requirement; return the exact
state-update result. Never paste full state JSON into prompts.
