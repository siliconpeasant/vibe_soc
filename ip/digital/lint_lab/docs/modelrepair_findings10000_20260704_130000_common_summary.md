# modelrepair_findings10000_20260704_130000 Common Summary

- Created: 2026-07-04T14:31:35
- Run root: `ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703`
- Shared broken RTL profile: `realistic`; seed `20260703`; variants `1260`; holdouts `0`.
- Baseline SpyGlass: `4781 errors / 5333 warnings / 7 infos` (`10121` total messages).
- Parser actionable baseline: `9962` violations, `29` unique tags; `9969` parsed findings including info.
- Per-round budget: `100-200 modules or 1200-2500 changed lines, unless the current report has fewer local fixes left`.

## Branches

- no-kb: `ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703/no_kb_work`
- with-kb: `ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703/with_kb_work`

## Top Tag Distribution

| tag | count | severities |
|---|---:|---|
| `sim_race02` | 1264 | `{"warning": 1264}` |
| `W240` | 1263 | `{"info": 1, "warning": 1262}` |
| `W528` | 932 | `{"info": 1, "warning": 931}` |
| `ErrorAnalyzeBBox` | 714 | `{"error": 714}` |
| `W415` | 639 | `{"error": 638, "info": 1}` |
| `NoAssignX-ML` | 521 | `{"warning": 521}` |
| `W398` | 385 | `{"error": 385}` |
| `InferLatch` | 314 | `{"error": 314}` |
| `W110` | 314 | `{"error": 314}` |
| `W287b` | 314 | `{"warning": 314}` |
| `W336` | 314 | `{"error": 314}` |
| `ParamWidthMismatch-ML` | 312 | `{"warning": 312}` |
| `W442a` | 310 | `{"error": 310}` |
| `bothedges` | 310 | `{"error": 310}` |
| `W123` | 308 | `{"error": 308}` |
| `STARC05-2.3.3.1` | 275 | `{"error": 275}` |
| `W422` | 275 | `{"error": 275}` |
| `mixedsenselist` | 250 | `{"error": 250}` |
| `SYNTH_5191` | 194 | `{"error": 194}` |
| `SYNTH_5035` | 173 | `{"warning": 173}` |
| `CombLoop` | 163 | `{"error": 162, "info": 1}` |
| `W337` | 159 | `{"warning": 159}` |
| `SYNTH_5143` | 141 | `{"warning": 141}` |
| `SYNTH_5034` | 103 | `{"warning": 103}` |
| `UndrivenInTerm-ML` | 18 | `{"error": 18}` |
| `CheckDelayTimescale-ML` | 1 | `{"warning": 1}` |
| `DetectTopDesignUnits` | 1 | `{"info": 1}` |
| `ElabSummary` | 1 | `{"info": 1}` |
| `checkCMD_ignore01` | 1 | `{"info": 1}` |

## Method Constraints

- Both arms start from identical broken RTL content copied into independent work branches.
- Main session does not repair RTL and only schedules workers plus final aggregation.
- No arm may use generator clean templates, base_level replacement, whole-module replacement, waivers, severity downgrades, or scripted repair helpers.
- Each repair round must be derived from the current SpyGlass report file/line/tag findings in that arm only.
- Round count ends naturally when SpyGlass reaches 0 errors / 0 warnings, not a fixed round count.
- No-kb arm may not use KB/RAG/wiki/web/with-kb artifacts.
- With-kb arm may only use the tag-specific KB excerpt embedded in its prompt.

## Report Use

Workers should use this summary as broad context, then inspect only targeted current-report and RTL snippets around selected file/line/tag findings. Do not load the full 1.2 MB RTL or full report into model context.
