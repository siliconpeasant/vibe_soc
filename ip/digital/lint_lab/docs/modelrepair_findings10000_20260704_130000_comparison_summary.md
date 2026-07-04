# modelrepair_findings10000_20260704_130000 no-kb vs with-kb Comparison

- Created: 2026-07-04T15:21:17
- Run root: `ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703`
- Shared starting point: identical broken RTL in independent `no_kb_work` and `with_kb_work` branches.
- Baseline SpyGlass: `4781 errors / 5333 warnings / 7 infos` (`10121` total messages).
- Parsed actionable baseline: `9962` violations, `29` tags.
- Per-round upper limit: `100-200 modules or 1200-2500 changed lines, unless the current report has fewer local fixes left`.
- Stop condition: natural SpyGlass clean, `0 errors / 0 warnings`; no fixed round count.

## Result

| arm | rounds | recorded lint time | wall clock | final E/W/I | 0/0 reached |
|---|---:|---:|---:|---:|---|
| no-kb | 14 | 568.01s | 1225s | 0/0/3 | yes |
| with-kb | 15 | 576.69s | ~1500s | 0/0/3 | yes |

## Comparison

- Round count: no-kb used `14` rounds; with-kb used `15` counted rounds. With-kb was `1` round higher.
- Recorded MCP lint wall time: no-kb `568.01s`; with-kb `576.69s`; delta `8.68s` (1.5% with-kb over no-kb).
- In this 10000-violation run with enlarged per-round cap, KB did not show a speed/round advantage. The no-kb arm was slightly ahead on counted rounds and recorded lint time.
- Interpretation: the larger per-round budget let no-kb apply broad report-local fixes across many modules, reducing the value of the prompt KB excerpt. This is a valid outcome for this method, not a failure of the run.

## Constraints Checked

- no-kb reported no KB/RAG/wiki/web use and no with-kb artifact use.
- with-kb reported only prompt-embedded KB excerpt use and no no-kb work access.
- Both used `soc-build.soc_lint` for SpyGlass runs.
- Final reports parse to no actionable error/warning violations in both branches.

## Measurement Caveat

- analysis_seconds and edit_seconds were required by the method but were not consistently instrumented by the two workers in this 10000 run.
- with-kb JSON records analysis_seconds/edit_seconds as null and lint_seconds per round.
- no-kb JSON records per-round E/W/I metrics and aggregate lint/wall time, but not per-round analysis/edit durations.
- Therefore the cleanest quantitative comparison here is natural round count and recorded MCP lint wall time, with wall-clock as approximate/contextual.

Because of that gap, this summary treats `rounds` and recorded MCP lint wall time as the primary comparable metrics. End-to-end wall time is useful context but not strictly normalized between workers.

## Artifacts

- Common summary MD: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_common_summary.md`
- Common summary JSON: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_common_summary.json`
- no-kb result MD: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_no_kb_result_20260704_151748.md`
- no-kb result JSON: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_no_kb_result_20260704_151748.json`
- with-kb result MD: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_with_kb_result_20260704_150326.md`
- with-kb result JSON: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_with_kb_result_20260704_150326.json`
- Comparison JSON: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_comparison_summary.json`
