---
name: lib-db-gen
description: Generate Synopsys .db technology or stub libraries for early synthesis and link. Use when converting Liberty .lib to .db with lc_shell, or when creating a minimal black-box Liberty/.db from a Verilog top module port list.
---

# Lib DB Gen

Use this skill when a flow needs a Synopsys `.db` and only has either a Liberty `.lib` or an RTL top module whose ports should become a black-box stub cell.

## Commands

The bundled script is `scripts/lib_db_gen.py`.

Convert an existing Liberty file to DB:

```bash
python3 .agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
  --lib path/to/input.lib \
  --db path/to/output.db
```

Generate an early black-box Liberty from a Verilog top and compile it to DB:

```bash
python3 .agents/skills/lib-db-gen/scripts/lib_db_gen.py stub \
  --top-v path/to/top.v \
  --top top_module_name \
  --lib path/to/top_stub.lib \
  --db path/to/top_stub.db
```

Use `--no-run` to only emit the `.lib` and the Library Compiler Tcl script. Use `--lc-shell /path/to/lc_shell` when `lc_shell` is not on `PATH`. Use `--work-dir <dir>` to control Library Compiler's command file, `lc_command.log`, and `lc_output.txt`; by default this is `<db-output-dir>/lc_work`, not the repository root.

The generated `<db-stem>.lc.tcl` is temporary by default: remove it only after `lc_shell` produces a non-empty current-run `.db` that is atomically installed at the requested output path, and retain it when conversion fails or `--no-run` is selected. Use `--keep-tcl` to preserve a reusable final-output command file after a successful conversion. Use `--tcl <path>` only to override its location; cleanup semantics remain unchanged. Reject resolved-path collisions among Tcl, DB, Liberty, and Verilog inputs before writing any file.

## Workflow

1. Prefer a real foundry or platform Liberty for timing signoff and mapped synthesis.
2. Use `convert` for real Liberty to `.db` conversion.
3. Use `stub` only for early integration, link, or black-box bring-up. The generated cell has ports and zero-area placeholder attributes; it is not timing or power evidence.
4. Keep generated `.db`, `.lib`, and LC logs out of Git unless they are reviewed release collateral.
5. For Design Compiler setup, point local ignored config such as `scripts/local.mk` at the generated `.db`, for example `SKY130HD_DC_DB := /path/to/lib.db`.

## Notes

- `stub` parses ANSI-style module headers and simple non-ANSI declarations.
- Numeric packed ranges like `[7:0]` become Liberty bus types. Parameterized widths are treated as scalar with a warning; use a resolved wrapper if bus width fidelity matters.
- The generated stub DB is for black-box linking, not cell mapping. It does not replace a standard-cell target library.
