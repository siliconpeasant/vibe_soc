# Synthesis Report: std_cell_inv

## Module Information
- **Module Name**: `std_cell_inv`
- **Description**: Parameterized width inverter (NOT gate) standard cell
- **Function**: Combinational logic, `y = ~a`

## Tool / Version
- **Tool**: Yosys Open SYnthesis Suite
- **Version**: 0.9 (git sha1 UNKNOWN, clang 11.0.3 -fPIC -Os)

## Synthesis Command
```bash
cd /Users/ninghechuan/vibe_soc/ip/digital/soc_ip_common && make syn RTL_TOP=std_cell_inv
```

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
| **Number of cells** | **1** |
|   - `$_NOT_` | 1 |
| **Number of latches** | **0** |
| **Number of flip-flops** | **0** |

## Cell Count Breakdown
- `$_NOT_`: 1 (inverter gate, WIDTH=1 default)

## Latch Check
- **Latch count**: 0
- **Result**: PASS - No unintended latches inferred. Pure combinational logic as expected.

## Warnings
- None. No warnings or errors reported during synthesis.

## Timing (Estimated)
- **Logic depth**: 1 gate (single inverter)
- **Estimated propagation delay**: ~0.05 ns (single NOT gate, generic technology)
- **Critical path**: `a` -> `$_NOT_` -> `y`

## Equivalence
- RTL: `assign y = ~a;`
- Netlist: `assign y = ~a;` (mapped to `$_NOT_` primitive)
- Functional equivalence: YES

## Conclusion
- Synthesis completed successfully with no errors.
- Expected cell count achieved: 1 NOT gate for WIDTH=1.
- No sequential elements (latches/FFs) inferred.
- Module is ready for release.
