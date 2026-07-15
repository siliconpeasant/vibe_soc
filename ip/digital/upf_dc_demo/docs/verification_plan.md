# UPF/DC five-domain verification plan

## Stage evidence

This owner runs document completeness, registered strict UPF generation, registered Verilator lint, registered VCS compile/elaboration, RTL quality, and static UPF/Tcl scans. `soc_sim` and synthesis are not run. A compile result is not behavioral simulation evidence.

| ID | Evidence | Pass condition |
|---|---|---|
| D-01 | Canonical document completeness | All five-domain/interface/PST requirements present |
| U-01 | Registered `upf-gen.upf_generate`, strict | Four artifacts, no warning, five domains/four switches/nine states |
| R-01 | Registered `soc_lint` | Complete filelist, no real warning/error |
| R-02 | Registered `soc_comp` | VCS top compile/elaboration succeeds |
| R-03 | RTL quality | Canonical files/modules resolve |
| S-01 | Static source scan | No RTL/UPF physical switch implementation; expected objects present |

## UPF structural checks

- Exactly `PD_AO`, `PD_SW`, `PD_ACC`, `PD_PERI`, and `PD_MEDIA` exist.
- The four core memberships and four AO controller memberships are exact.
- `PD_AO` has only three macro additional supplies; the four switch input/output pairs are separate supply objects.
- Exactly `PSW_SW`, `PSW_ACC`, `PSW_PERI`, and `PSW_MEDIA` exist with input/output/control/ON clauses and no switch-cell mappings.
- Exactly four output isolation rules and four L2H rules map to the teaching ELS view; exactly four AO-to-domain H2L rules map to the teaching LS view.
- The four switchable clock attributes reference their destination supply sets.
- The four hard macros remain in `PD_AO`, visible in both diagrams, with eight exact PG paths.
- There is no retention and no direct switchable-domain crossing.

## PST checks

The system-state names must be exactly `ALL_ON`, `SW_OFF`, `ACC_OFF`, `PERI_OFF`, `MEDIA_OFF`, `COMPUTE_ONLY`, `IO_STANDBY`, `MEDIA_MODE`, and `DEEP_SLEEP`. Each generated `PD_AO` expression must explicitly reference:

- all four domain states (`PD_SW/ACC/PERI/MEDIA == RUN|OFF`),
- all four switched supply states (`SS_VDD_SW/ACC/PERI/MEDIA_VSS == ON|OFF`),
- `SS_VDD_AO_VSS`, three macro supply sets, and four input supply sets as `ON`.

The domain/supply truth table is the one in `architecture.md`; any omitted condition, implicit don't-care, `RET`, or input-rail OFF condition is failure.

## Later synthesis checks

The synthesis owner must inspect real reports before finalizing counts. The source-level structural estimate is 36 ELS and 44 pure H2L LS. DC Tcl may document these as provisional, but must not treat them as validated until a real registered `soc_syn` run supplies the exact hierarchy/netlist counts.

Later synthesis must also prove exactly five domains, four abstract switches, all supplies/states, all eight MacroPG paths, all four cores/controllers, complete saved UPF, no physical switch cell, and ordinary non-PG Verilog with no `VDD*`, `VSS*`, `VGND`, `VPWR`, `VPWRIN`, or other named PG connection.

## Future functional goals

If simulation is later authorized, independently cover power-up, request/response, isolation-before-off, state loss, and recovery for all four cores; exercise all nine system combinations at the control-intent level; and retain SRAM, PLL, and pad behavioral checks. Until then these are unverified goals, not PASS claims.

## Design evidence

Power Compiler UG U-2022.12-SP3 pp. 228–229 requires isolation on switchable-domain outputs and level shifting across differing voltages. Page 210 supports H2L, L2H, dual-rail, and enable-level-shifter implementations. The local teaching views are explicitly non-signoff assumptions used only to exercise these mechanisms.
