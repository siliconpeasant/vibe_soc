# Synthesis Report: std_cell_buf

## Module Information
- **Module Name**: `std_cell_buf`
- **Description**: Parameterized width buffer (pass-through) standard cell
- **Function**: Combinational logic, `y = a`

## Tool / Version
- **Tool**: Yosys Open SYnthesis Suite
- **Version**: 0.9 (git sha1 UNKNOWN, clang 11.0.3 -fPIC -Os)

## Synthesis Command
```bash
cd /Users/ninghechuan/vibe_soc/ip/digital/soc_ip_common && make syn RTL_TOP=std_cell_buf
```

The project Makefile auto-generates `syn.ys` and runs:
`read_verilog` (filelist) -> `hierarchy -check -top std_cell_buf` ->
`proc -> flatten -> opt -> fsm -> opt -> memory -> opt -> techmap -> opt` ->
`write_verilog` + `stat`.

## Netlist Statistics

| Metric | Count |
|--------|-------|
| Number of wires | 2 |
| Number of wire bits | 2 |
| Number of public wires | 2 |
| Number of public wire bits | 2 |
| Number of memories | 0 |
| Number of memory bits | 0 |
| Number of processes | 0 |
| **Number of cells** | **0** |
| **Number of latches** | **0** |
| **Number of flip-flops** | **0** |

## Cell Count Breakdown
- No gate-level cells emitted. Yosys recognized the trivial pass-through
  (`assign y = a;`) and reduced it to a direct wire alias during the
  `opt_expr` / `opt_clean` passes. The resulting netlist contains the
  RTL-equivalent `assign y = a;` statement only, which is the intended
  behavior of a buffer cell at the RTL level prior to gate library mapping.

## Latch Check
- **Latch count**: 0
- **Result**: PASS - No unintended latches inferred. Pure combinational logic as expected.

## Warnings
- None. No warnings or errors reported during synthesis.

## Timing (Estimated)
- **Logic depth**: 0 gate (direct wire connection in generic synthesis)
- **WNS**: N/A (combinational only, no register endpoints)
- **TNS**: N/A (combinational only)
- **Critical path**: `a -> y` (wire only; physical buffer delay will be
  inserted during technology mapping with a real standard cell library).

## Equivalence
- RTL: `assign y = a;`
- Netlist: `assign y = a;` (optimized to direct wire)
- Functional equivalence: YES

## Notes
- For a generic (non-technology) synthesis flow, a buffer cell is
  semantically a no-op and is therefore folded away. When mapped to a
  real standard cell library (e.g. via `abc -liberty <lib>`), this would
  be replaced by a `BUFx1`/`BUFx2` cell selected based on the target
  load/drive requirements.

## Conclusion
- Synthesis completed successfully with no errors.
- 0 latch, 0 flip-flop, 0 cell - exactly matches expectation for a
  trivial buffer in generic technology.
- Module is ready for release.
