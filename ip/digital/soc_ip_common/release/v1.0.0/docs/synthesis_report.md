# rstn_test_mux Synthesis Report

## Tool & Environment
- **Tool**: Yosys 0.9 (git sha1 UNKNOWN, clang 11.0.3)
- **Command**: `make syn RTL_TOP=rstn_test_mux`
- **Yosys Script**: `de/syn/syn.ys`
- **Date**: 2026-05-17

## Synthesis Command Flow
```
read_verilog <rtl_files>
hierarchy -check -top rstn_test_mux
proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
write_verilog rstn_test_mux_netlist.v
stat
```

## Netlist Statistics

| Metric | Value |
|--------|-------|
| Number of wires | 8 |
| Number of wire bits | 8 |
| Number of public wires | 8 |
| Number of public wire bits | 8 |
| Number of memories | 0 |
| Number of memory bits | 0 |
| Number of processes | 0 |
| **Number of cells** | **1** |
|   - `$_MUX_` | 1 |
| **Number of latches** | **0** |
| **Number of flip-flops** | **0** |

## Area Estimate

| Cell Type | Count | Est. GE (per cell) | Total GE |
|-----------|-------|-------------------|----------|
| `$_MUX_` (2:1 mux) | 1 | ~4.0 | ~4.0 |
| **Total** | **1** | — | **~4.0 GE** |

> GE = Gate Equivalent (relative to a 2-input NAND gate). A 2:1 mux is approximately 4 GE.

## Timing Analysis

`rstn_test_mux` is a **pure combinational** module (no clocks, no sequential elements).

- **Constraint**: `set_max_delay` = 2.0 ns (from all inputs to `rst_n_out`)
- **Critical Path**: Input (`rst_n` / `test_rst_n` / `test_mode`) -> `$_MUX_` -> `rst_n_out`
- **Estimated delay**: ~0.15 ns (single 2:1 mux, generic cell)
- **WNS**: N/A (combinational module, no clock-based setup check)
- **TNS**: N/A
- **Result**: TIMING MET — combinational delay is well within the 2.0 ns max delay constraint.

## Equivalence Check
- The flattened netlist implements `rst_n_out = test_mode ? test_rst_n : rst_n`, which is functionally equivalent to the RTL.
- The `std_cell_mux` instance has been inlined; the `u_mux` cell boundary is preserved as wires with source attributes.

## Issues & Warnings
- None. No errors, no warnings, no latches inferred.

## Recommendations
1. **DFT**: The original RTL had `set_dont_touch [get_cells u_mux]` in the SDC. In the flattened netlist, the mux cell is no longer a hierarchical instance. If DFT visibility of the mux is required, consider using `synth -flatten 0` or marking the cell with `(* keep_hierarchy *)`.
2. **Reset tree**: This module sits in the reset distribution path. Ensure the `$_MUX_` cell is mapped to a drive-strength-appropriate mux in the target technology library.
3. **Fanout**: The SDC does not explicitly set `set_max_fanout` on `rst_n_out`. If this mux drives a large reset tree, consider adding a buffer tree downstream.
