---
name: crg-req-to-design
description: Convert a CRG requirement table into clock/reset design tables, PLL recommendations, and an architecture report. Use before clock/reset diagram generation when requirements are supplied as Excel or CSV.
---

# CRG Requirement to Design

Call `crg_req_to_design` with an existing `.xlsx`, `.xls`, or `.csv` requirement table and optional output directory. The default is `<input-stem>_design/` beside the input.

Recognized concepts include subsystem/IP, clock/reset signal name, frequency/note, pad sources, integer dividers, and reset roots. Outputs are:

- `clock_design.xlsx`
- `reset_design.xlsx`
- `crg_report.txt`

Review PLL/divider recommendations and missing-frequency signals before treating the design table as approved. Feed reviewed tables to `cr-tree-diag-gen` for visualization.

This Skill creates design tables only. It does not generate CRG RTL; that requires the separate, currently unregistered `crg-gen` server.
