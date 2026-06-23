# Pipeline state contract

Every independently developed module or IP package owns `pipeline_state.json` at its workspace root. It is a validated coordination signal, not an informal log.

Architecture planning by `soc-architect` is a pre-doc handoff and is not represented as a `pipeline_state.json` stage. Architecture artifacts live under `docs/architecture*.md`; affected modules enter this state machine only when their doc-stage handoff is ready.

## Initialization

Single module:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/init_state.py <workspace> <module>
```

Multi-module package:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/init_state.py <workspace> <package> \
  --submodules "module_a,module_b"
```

Initialization refuses to overwrite existing state unless `--force` is explicitly supplied.

## Transitions

```text
blocked -> pending -> in_progress -> done
                                \-> fail -> in_progress
pending -> skipped              (documented doc-stage exception only)
```

- Dependencies are `doc -> rtl -> {verif, syn}`; `done` and `skipped` satisfy dependencies.
- Do not add ad hoc stages such as `architect`, `architecture`, `pd`, or `release` to satisfy this contract. Use role-specific artifacts and reports outside this module-stage state machine unless a rule explicitly defines a transition.
- Agents mark their stage `in_progress` before work.
- `done` requires existing, non-empty relative artifact paths and at least one passing check. Any failed check makes `done` invalid.
- `fail` requires a failed check and remediation note.
- `blocked` is dependency-derived and cannot be set manually.
- Writes are locked and atomic. Repeated `--check` options are preserved.

Example:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/update_state.py <workspace> rtl in_progress
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/update_state.py <workspace> rtl done \
  --artifacts "de/rtl/mod.v,de/rtl/filelist.f,de/syn/mod.sdc" \
  --check "soc_lint:passed:0 warning" \
  --check "rtl_quality:passed"
```

For multi-module mode add `--module <module>`.

Before dispatching a stage and immediately after a role agent returns, the coordinator runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/query_state.py <workspace>
```

Each pipeline-stage dispatch prompt must include the absolute workspace, module name, state mode, and requirement to report the `update_state.py` stdout line. `soc-architect` dispatch prompts instead include the project root, architecture objective, required handoff documents, and explicit instruction not to update `pipeline_state.json`. A failed stage blocks new dispatch until retried.
