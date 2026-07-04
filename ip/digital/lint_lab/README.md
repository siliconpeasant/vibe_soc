# lint_lab

`lint_lab` is an intentionally bad RTL corpus for SpyGlass lint autofix benchmarking.
It is used to compare two repair workflows:

- No-KB: generate fix plans from the lint report and local RTL context only.
- With-KB: query `soc-ai-kb` by lint tag and diagnostic text before generating fix plans.

Primary comparison metrics are repair time and number of repair rounds to convergence. Real EDA lint must be run through `soc-build.soc_lint`; direct simulator or lint shell invocation is not part of this benchmark.

Current entry points:

```bash
make lint MODULE=ip/digital/lint_lab LINT_TOOL=spyglass RTL_TOP=lint_lab
python3 scripts/lint/lint_autofix_compare.py --help
python3 scripts/lint/lint_strict_live_compare.py --help
python3 scripts/lint/lint_report_local_repair.py --help
```

Generated reports and comparison outputs live under `de/run/` and are intentionally ignored by Git.
