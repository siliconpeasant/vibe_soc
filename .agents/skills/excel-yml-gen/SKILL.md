---
name: excel-yml-gen
description: Generate YAML and Verilog register-file artifacts from a structured Excel register workbook. Use when the approved register source is an Excel sheet.
---

# Excel to YAML/Register RTL

Call the registered `excel_yml_gen` MCP tool with `excel_file`, `sheet_name`, and optional `output_dir`. If omitted, output goes to `<excel-stem>_generated/` beside the workbook, never inside the plugin package.

Workbook sheets:

- `<name>`: component/protocol/base-address configuration
- `<name>_reg`: register definitions
- `<name>_intp`: optional interrupts

Passing `<name>_reg` automatically selects the three-sheet group. Outputs include YAML, bus register-file RTL, an instance wrapper, and a TDR buffer list. Use `references/excel2yml_demo.xlsx` as the format example.

Generation uses argument-vector subprocess execution; never reintroduce shell-string execution for paths supplied by users.
