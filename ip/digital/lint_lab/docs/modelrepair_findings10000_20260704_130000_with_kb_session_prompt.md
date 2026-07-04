You are working in `<repo>`.

First read `.agents/skills/soc-build/SKILL.md` and `.agents/rules/02_toolchain.md`.
Use only registered MCP tool `soc-build.soc_lint` for SpyGlass lint. Do not directly run make, SpyGlass, Verilator, or any EDA shell command.

Common input file:
`ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_common_summary.md`

Machine-readable summary:
`ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_common_summary.json`

Fresh run root:
`ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703`

Baseline scale:
- SpyGlass summary: `4781 errors / 5333 warnings / 7 infos`.
- Parser actionable baseline: `9962` violations, `29` unique tags, `9969` parsed findings including info.

The common summary is the only report context you should load broadly. Use targeted `rg`/`sed` snippets around selected report lines/modules only. Do not load the full RTL or full report into model context.

Repair protocol:
- Model directly generates local patches from the current SpyGlass report.
- No `scripts/lint/lint_report_local_repair.py repair`.
- No generator clean template, no `base_level`, no whole-module replacement.
- Per round budget: 100-200 modules or 1200-2500 changed lines, unless the current report has fewer local fixes left.
- Patch only concrete current-report `file/line/tag` issues in your assigned work branch.
- Same tag can have different root causes; inspect local code before patching.
- A fix may expose secondary warnings; continue based on the next actual report.
- Rerun SpyGlass through `soc-build.soc_lint` after each round.
- Continue until actual `0 errors / 0 warnings`, or stop only with a concrete blocker.
- Record metrics each round: analysis_seconds, edit_seconds, kb_seconds, lint_seconds, actionable violations, total findings, selected tags, patched modules, changed lines, patch diff path, newly introduced errors/warnings if any, failure reason if blocked.

# Session Role: with-kb

You are the with-KB arm of the experiment.

Hard constraints:
- Use only the KB excerpt below. Do not call/query/read `soc-ai-kb`, `kb_context`, wiki/RAG, web, or any extra KB source.
- Do not read the no-KB prompt or `no_kb_work`.
- Work only in this branch:
`ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703/with_kb_work`

Initial current report:
`ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703/with_kb_work/de/run/lint_spyglass/moresimple.rpt`

# Tag-Specific KB Excerpt For with-KB Session Only

Use these as repair-direction guidance only. Do not use them as waivers or as permission to suppress rules.

## sim_race02 / W415: multiple drivers and same-cycle multiple assignments

- `sim_race02` reports signals with multiple assignments in the same simulation cycle; it commonly arises when two `always` constructs can assign the same signal in the same cycle. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 2778`.
- The same source notes that for true multi-driven nets, `W415` is the better tag to use than `sim_race02`. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 2778`.
- `W415` reports variables/signals that do not infer tristate behavior and have multiple simultaneous drivers, including multiple sequential always/process constructs, instances, or concurrent statements. Such cases are errors unless the variable intentionally infers a tristate net. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 1075`.
- Actionable local fix: for a reported `y` or bus with multiple assignments, consolidate to one procedural driver or one continuous driver. Remove duplicate `always` blocks assigning the same reg. Preserve reset/data behavior in a single block. Do not fix by waiver or tag-parameter change.

## NoAssignX-ML / case x-z patterns

- `NoAssignX-ML` flags RHS assignments containing `X`, including case branch/default assignments such as `NextState = 2'bXX` and continuous assignments like `assign z = 1'bx`. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 2134` and `page 2135`.
- `DisallowXInCaseZ-ML` notes that using `x` in `casez` can create simulation/synthesis mismatch. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 1534`.
- Actionable local fix: replace explicit `8'hxx`, `8'hzz`, and case labels relying on x/z wildcards with deterministic synthesizable values or explicit `?` patterns where intentional. Prefer fully specified default assignments and deterministic case defaults.

## InferLatch

- `InferLatch` can be controlled by parameters, but this experiment must fix RTL rather than suppress reporting. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 385` and `page 388`.
- Actionable local fix: in combinational `always @*`, assign every output/reg on every path. Add a deterministic default assignment at block entry or add missing `else/default` branches. Avoid partial assignment patterns such as `if (sel) sticky = ...;` without an else.

## CombLoop / ErrorAnalyzeBBox / SYNTH_5191 root-cause direction

- `CombLoop` reports combinational loops in the compiled RTL. Citation: `eda/spyglass/c_primitives/libCoreRules/vnCombLoop.txt:1`.
- SpyGlass guidance for combinational loops says to break the loop with a flip-flop unless the loop was introduced by mistake; for accidental RTL loops, rewrite to remove feedback. Citation: `eda/VC_SpyGlass_Lint_Rules_Reference.pdf:page 597` and `page 2648`.
- Actionable local fix: replace mutual continuous assignments such as `assign loop_a = loop_b; assign loop_b = loop_a;` with a deterministic source expression, or register the feedback if it is intentional. In this lint lab, treat such loops as accidental and remove the feedback locally.
- `ErrorAnalyzeBBox` / `SYNTH_5191` often reflects synthesis failure in a module; use adjacent concrete tags and the module body to find the actual root cause, such as multiple drivers, initial delays, explicit X/Z assignments, floating RHS, or combinational loops.

Write outputs:
- Markdown report: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_with_kb_result_<timestamp>.md`
- JSON report: `ip/digital/lint_lab/docs/modelrepair_findings10000_20260704_130000_with_kb_result_<timestamp>.json`
- Patch diffs under: `ip/digital/lint_lab/de/run/lint_spyglass/live_compare/modelrepair_findings10000_20260704_130000/seed_20260703/with_kb_work/patch_logs/`

Final answer in Chinese with run dir, report paths, rounds, runtime, final errors/warnings, whether 0/0 was reached, and which prompt KB excerpts were used.
