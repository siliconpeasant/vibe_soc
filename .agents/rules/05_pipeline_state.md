# Pipeline state contract

Each independently developed module owns `pipeline_state.json`. It is a
validated coordination signal, not a narrative log. `loop_context.py` includes
the routine compact state view; use `query_state.py <workspace> --compact` only
for failure investigation, an intentional delivery transition, or detailed
evidence inspection.

The only stages are `doc`, `rtl`, `verif`, and `syn`, with dependencies
`doc -> rtl -> {verif, syn}`. Architecture, review, PD, release, and signoff are
external handoffs, not additional stages.

```text
blocked -> pending -> in_progress -> done
                                \-> fail -> in_progress
pending -> skipped              # approved doc exception only
done/in_progress/fail -> pending # explicit invalidation with note
done -> in_progress             # RTL reopen; invalidates consumers
```

Use `init_state.py` only when state is absent and `update_state.py` for every
transition. Mark a stage `in_progress` before its work. `done` requires existing
non-empty canonical artifacts, every required check passing, and a current RTL
fingerprint. `verif` and `syn` additionally require the `run_id`,
`source_fingerprint`, and immutable artifact paths emitted by their registered
MCP run. A failure records a failed check and remediation note.

The source fingerprint hashes controlled manifests and resolved RTL sources;
generated `de/run/rtl.f` bytes are resolver input, not source identity. During
an MCP rolling upgrade, a legacy generated-manifest fingerprint may be
normalized only when the state tool independently reproduces that legacy
fingerprint from unchanged current sources and records both values.

In `dev`, targeted checks are task evidence but do not close stages. In
`merge/signoff`, close only stages the packet marks stale. If verification
repairs RTL, finish its final simulation and invalidate synthesis once; the
inverse applies to synthesis repair. If the other consumer also needs RTL
repair, reopen RTL and rerun both consumers after it closes.

Example transition:

```bash
python3 .agents/scripts/update_state.py <workspace> rtl in_progress
python3 .agents/scripts/update_state.py <workspace> rtl done \
  --artifacts "de/rtl/mod.v,de/rtl/filelist.f" \
  --check "soc_lint:passed" --check "soc_comp:passed" \
  --check "rtl_quality:passed"
```

For multi-module state add `--module <name>`. Dispatch inputs contain the
absolute workspace, module, packet mode, objective, and requirement to return
the exact state-update result. Never paste full state JSON into prompts.
