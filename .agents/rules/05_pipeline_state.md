# Pipeline state contract

Every independently developed module or IP package owns `pipeline_state.json` at its workspace root. It is a validated coordination signal, not an informal log.

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

Each dispatch prompt must include the absolute workspace, module name, state mode, and requirement to report the `update_state.py` stdout line. A failed stage blocks new dispatch until retried.
