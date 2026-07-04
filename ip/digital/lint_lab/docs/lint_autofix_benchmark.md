# Lint Autofix Benchmark

`lint_lab` is an intentionally bad RTL corpus for comparing SpyGlass lint triage and fix planning with and without the SoC AI knowledge base. It is not product RTL and should not be used for synthesis or simulation signoff.

## Flow

1. Run SpyGlass lint through the project flow:

   ```bash
   make lint MODULE=ip/digital/lint_lab LINT_TOOL=spyglass RTL_TOP=lint_lab
   ```

   Agents must use `soc-build.soc_lint` instead of invoking `make` directly.

2. Parse the SpyGlass `moresimple.rpt` report and create comparison artifacts:

   ```bash
   python3 scripts/lint/lint_autofix_compare.py      --report ip/digital/lint_lab/de/run/lint_spyglass/moresimple.rpt      --outdir ip/digital/lint_lab/de/run/lint_spyglass/autofix_compare
   ```

3. For the With-KB path, query `soc-ai-kb` by lint tag and diagnostic text, then rerun the parser with a JSON note file:

   ```bash
   python3 scripts/lint/lint_autofix_compare.py      --report ip/digital/lint_lab/de/run/lint_spyglass/moresimple.rpt      --kb-notes ip/digital/lint_lab/de/run/lint_spyglass/autofix_compare/kb_notes.json      --outdir ip/digital/lint_lab/de/run/lint_spyglass/autofix_compare
   ```

## Primary Metrics

- repair time per round, measured by `--started-at` and `--ended-at`
- repair rounds to convergence, where convergence means zero error/warning lint violations or no remaining review-approved fixes

## Secondary Metrics

- unique lint tags found
- total violations
- With-KB citation coverage
- tags needing manual review
- whether an attempted fix introduces new lint failures

Grow the corpus incrementally; do not add failures to real IP RTL.
