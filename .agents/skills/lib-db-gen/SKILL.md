---
name: lib-db-gen
description: >
  Generate Synopsys .db technology or stub libraries for early synthesis, low-power
  link, and bring-up. Owners: soc-synthesis-engineer and soc-low-power-engineer.
  Convert Liberty .lib to .db with dc_shell (enable_write_lib_mode), or create a
  minimal black-box Liberty/.db from a Verilog top module port list.
---

# Lib DB Gen

**Owner roles:** `soc-synthesis-engineer`, `soc-low-power-engineer`.
MCP tools `lib_db_convert` and `lib_db_stub` are connected at the project
parent for routing; execution remains restricted to those owners through named
MCP inheritance.

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

Use `--no-run` to only emit the `.lib` and convert Tcl. Use `--work-dir <dir>`
for command files, logs, and any vendor crash snapshots (default
`<db-output-dir>/lc_work`). Never launch `dc_shell` or `lc_shell` from the
repository root; direct diagnostics must use a module `de/run/<tool>/` directory
or a gitignored `tmp/eda/<tool>/` directory as the process working directory.

### Shell backend (default: dc_shell)

**Default is `dc_shell` + `enable_write_lib_mode`** (env `LIB_DB_SHELL_MODE=dc`).
This is the supported convert path: same `.db` as Library Compiler, **exit 0**
cleanly.

```tcl
enable_write_lib_mode
read_lib "/path/to/input.lib"
write_lib <lib_name> -format db -output "/path/to/output.db"
exit
```

Set `DC_SHELL` or `--dc-shell` if `dc_shell` is not on `PATH`.

Optional backends (not recommended for day-to-day):

- `--shell-mode auto` — prefer DC, fall back to LC if DC is missing
- `--shell-mode lc` — use `lc_shell` (on some RHEL 8 + LC X-2025.06 hosts,
  `write_lib` succeeds then **SIGSEGV in exit handlers**; the wrapper may still
  accept a non-empty staged `.db` after a crash exit)

MCP tools accept `shell_mode` / `dc_shell` / `lc_shell` knobs; omit them to use
the DC default.

The generated `<db-stem>.lc.tcl` is temporary by default: remove it only after a
non-empty current-run `.db` is atomically installed at the requested output
path, and retain it when conversion fails or `--no-run` is selected. Use
`--keep-tcl` to preserve a reusable final-output command file after success.
Use `--tcl <path>` only to override its location. Reject resolved-path
collisions among Tcl, DB, Liberty, and Verilog inputs before writing any file.

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
