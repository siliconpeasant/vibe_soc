# std_cell_mux Synthesis Report

## Module Info
| Item | Value |
|------|-------|
| Module | `std_cell_mux` |
| Description | Parameterized 2-to-1 multiplexer (std_cell) |
| Top | Yes |
| Technology | Yosys generic (abc -g simple) |

## Synthesis Results

### Area Summary
| Metric | Value |
|--------|-------|
| Wires | 4 |
| Wire bits | 4 |
| Memories | 0 |
| Memory bits | 0 |
| Cells | 1 |
| $_MUX_ | 1 |

### Quality Checks
| Check | Result |
|-------|--------|
| Latch inference | NONE (combinational only) |
| Problems reported | 0 |
| DFF / Latch cells | 0 |

### Notes
- Pure combinational logic; no clock domain or timing path to analyze.
- No WNS/Setup/Hold constraints applicable (no sequential elements).
- Technology mapping produced a single `$_MUX_` gate per bit.
