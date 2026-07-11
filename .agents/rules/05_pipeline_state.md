# Pipeline state contract

Every independently developed module or IP package owns `pipeline_state.json` at its workspace root. It is a validated coordination signal, not an informal log.

Architecture planning by `soc-architect` is a pre-doc handoff and is not represented as a `pipeline_state.json` stage. Architecture artifacts live under `docs/architecture*.md`; affected modules enter this state machine only when their doc-stage handoff is ready.

## Initialization

Single module:

```bash
python3 <project_root>/.agents/scripts/init_state.py <workspace> <module>
```

Multi-module package:

```bash
python3 <project_root>/.agents/scripts/init_state.py <workspace> <package> \
  --submodules "module_a,module_b"
```

Initialization refuses to overwrite existing state unless `--force` is explicitly supplied.

## Transitions

```text
blocked -> pending -> in_progress -> done
                                \-> fail -> in_progress
pending -> skipped              (documented doc-stage exception only)
done/in_progress/fail -> pending (explicit invalidation with --note)
done -> in_progress            (RTL reopen with --note; downstream stages are invalidated)
```

- Dependencies are `doc -> rtl -> {verif, syn}`; `done` and `skipped` satisfy dependencies. `verif` and `syn` may run independently after RTL, but each result is tied to the RTL snapshot used for that run.
- Do not add ad hoc stages such as `architect`, `architecture`, `pd`, or `release` to satisfy this contract. Use role-specific artifacts and reports outside this module-stage state machine unless a rule explicitly defines a transition.
- Agents mark their stage `in_progress` before work.
- If the verification stage changes any RTL source or RTL filelist, it may do so multiple times while `verif` is `in_progress`. It must finish simulation on the final modified RTL, then the coordinator moves `syn` to `pending` once with a note such as `RTL changed during verif; synthesis rerun required`.
- If the synthesis stage changes any RTL source or RTL filelist, it may do so multiple times while `syn` is `in_progress`. It must finish synthesis on the final modified RTL, then the coordinator moves `verif` to `pending` once with a note such as `RTL changed during syn; simulation rerun required`.
- Within one RTL epoch, only one downstream stage may own RTL repair. If the other downstream stage also needs RTL edits after the first repair, reopen `rtl in_progress` with a note; do not continue alternating `verif` and `syn` RTL edits. Reopening completed RTL automatically invalidates `verif` and `syn`.
- A stage moved from `done`, `fail`, or `in_progress` back to `pending` is an explicit invalidation and requires `--note`; stale artifacts and check results are cleared.
- `done` requires existing, non-empty relative artifact paths and at least one passing check. Any failed check makes `done` invalid.
- A successful `soc_sim` or `soc_syn` response ends with `LOOP_EVIDENCE=<json>`. Pass that JSON object's `source_fingerprint` and `run_id` to the matching `verif done` or `syn done` update. State closure rejects a stale fingerprint, a missing run ID, or RTL that changed during the MCP run.
- If `verif` or `syn` changed RTL, rerun `soc_lint`, `soc_comp`, and `check_rtl_quality.py` on the final source snapshot and include all three passing checks in the downstream-stage closure. The sibling downstream stage is invalidated once.
- `fail` requires a failed check and remediation note.
- `blocked` is dependency-derived and cannot be set manually.
- Writes are locked and atomic. Repeated `--check` options are preserved.

Example:

```bash
python3 <project_root>/.agents/scripts/update_state.py <workspace> rtl in_progress
python3 <project_root>/.agents/scripts/update_state.py <workspace> rtl done \
  --artifacts "de/rtl/mod.v,de/rtl/filelist.f,de/syn/mod.sdc" \
  --check "soc_lint:passed:0 warning" \
  --check "rtl_quality:passed"
```

For multi-module mode add `--module <module>`.

Verification and synthesis closure additionally use the values emitted by the
successful MCP call:

```bash
python3 <project_root>/.agents/scripts/update_state.py <workspace> verif done \
  --artifacts "dv/tb/tb_mod.sv,dv/sim/sim.log" \
  --check "soc_sim:passed" --check "sim_log:passed" \
  --source-fingerprint <source_fingerprint> --run-id <run_id>
```

Before dispatching a stage and immediately after a role agent returns, the coordinator runs:

```bash
python3 <project_root>/.agents/scripts/query_state.py <workspace>
```

Each pipeline-stage dispatch prompt must include the absolute workspace, module name, state mode, and requirement to report the `update_state.py` stdout line. `soc-architect` dispatch prompts instead include the project root, architecture objective, required handoff documents, and explicit instruction not to update `pipeline_state.json`. A failed stage blocks new dispatch until retried.
