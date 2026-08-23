# DFT frontend checklist (bootstrap)

Use the project **DFT前端实现规范** as the authoritative standard when
available. This file is a portable bootstrap for agent readiness checks.

## Must-have (module IP / chip slice)

| ID | Category | Typical names | Notes |
|----|----------|---------------|-------|
| M1 | Test mode | `test_mode`, `scan_mode`, `dft_mode` | Constant / controlled in test |
| M2 | Scan enable | `scan_en`, `scan_enable`, `se` | Shift/capture control |
| M3 | Test reset | `test_rst_n`, `test_rstn`, `scan_rst_n` | Separate from functional reset when required |
| M4 | Functional reset controllable in test | `rst_n` + test mux (`rstn_test_mux`) | Document if test overrides functional reset |
| M5 | Clock present for scan | `clk` / primary clocks | Test clocks declared in SGDC |

## Recommended (SoC / subsystem)

| ID | Category | Typical names | Notes |
|----|----------|---------------|-------|
| R1 | DFT reset disable | `dftrstdisable`, `dft_rst_disable` | Async reset isolation in scan |
| R2 | Scan chain ports | `scan_in*`, `scan_out*`, `si`, `so` | May be inserted post-RTL |
| R3 | Shift / capture | `shift_en`, `capture_en` | ATPG protocol |
| R4 | JTAG / TAP | `tck`, `tms`, `tdi`, `tdo`, `trst_n` | Board/chip DFT access |
| R5 | Memory BIST hooks | `mbist_*`, `bist_*` | Compiler / wrap contract |
| R6 | OCC / test clock control | `occ_*`, `test_clk` | At-speed |

## Documentation

- Architecture or design_spec must state DFT assumptions (scan insertion level,
  MBIST ownership, lock-up latches, black-box macros).
- SGDC must list `test_mode`, test resets, and clocks used by SpyGlass DFT.
- Waivers live as reviewed `.awl` under `de/dft/`, never as silent report edits.

## SpyGlass goals

| Goal | When |
|------|------|
| `dft/dft_scan_ready` | Default frontend structural readiness |
| `dft/dft_best_practice` | Optional second pass when packet requests |

## Non-goals of this checklist

- Full ATPG coverage closure
- Post-layout OCC final timing
- Foundry-specific MBIST compiler tape-in
