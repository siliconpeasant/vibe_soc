# Verification recovery gate

Use this rule when compile, simulation, regression, or coverage work fails or when a verification task changes RTL.

## Execution boundary

Verification must use the registered `soc-build` MCP server:

- compile or single test: `soc_comp` or `soc_sim`
- regression: `soc_regress`
- coverage: `soc_coverage`

Do not replace these with direct shell simulator commands, direct `make`, `iverilog`, `vvp`, VCS, or ad hoc script fallbacks from a stage agent.

## Failure triage

On failure:

1. Locate the real compile, simulation, regression, or coverage log under the module artifact roots.
2. Classify the failure as environment/tool invocation, filelist/elaboration, RTL behavior, testbench/test expectation, timeout, or license/resource.
3. Record the failed check and remediation note in `pipeline_state.json` when the task is governed by the module pipeline.
4. Loop back to the earliest affected stage. Filelist or RTL behavior failures usually invalidate RTL; testbench-only failures remain in verification.
5. Stop downstream dispatch until the failed stage is retried and the state is valid.

## PASS criteria

Claim verification success only when the registered MCP check completed or produced a real tool artifact that can be inspected, the relevant log contains the project-defined pass condition, and error/fatal counters are clean for that test. A timeout, partial run, stale log, or manually written pass marker is not a pass.

If verification changes any RTL source or RTL filelist while `verif` is `in_progress`, finish simulation on the final modified RTL and invalidate `syn` back to `pending` once with a note.
