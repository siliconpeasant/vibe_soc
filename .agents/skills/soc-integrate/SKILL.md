---
name: soc-integrate
description: Extract RTL ports, generate instances/wrappers/top modules, and track interface changes through snapshots and integration configs. Use for generated SoC top-level integration and port-change maintenance.
---

# SoC Integrate

Use the registered `soc-integrate` MCP server; do not invoke the Python CLI as a fallback.

Tools:

- `soc_extract`, `soc_instantiate`, `soc_wrap`, `soc_csv`
- `soc_integrate`, `soc_extract_map`, `soc_update`, `soc_remove`
- `soc_snapshot`, `soc_diff`

`soc_integrate` emits the generated top, `.integrate.json`, and review CSV. Preserve manual connection intent through a port-map JSON and refresh with `soc_update`; do not hand-edit generated instances.

Automatic shared-signal rules are suitable only for simple direction/width-compatible ports. Review multiple-driver, width, reset-domain, clock-domain, and protocol connections explicitly.

The built-in parser supports ANSI-style Verilog/SystemVerilog module ports. Unsupported syntax must fail explicitly rather than silently dropping ports. For interfaces, modports, complex package types, or non-ANSI declarations, provide a normalized wrapper before integration.
