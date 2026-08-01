# UPF/DC five-domain verification plan

## Stage evidence

This flow runs document completeness, registered strict UPF generation,
registered RTL checks, registered DC/Power Compiler synthesis, UPF-aware
Formality equivalence, and Conformal Low Power native IEEE 1801 RTL/UPF
consistency checking. A compile result is not behavioral simulation evidence.

| ID | Evidence | Pass condition |
|---|---|---|
| D-01 | Canonical document completeness | All five-domain/interface/PST requirements present |
| U-01 | Registered `upf-gen.upf_generate`, strict | Four artifacts, no warning, five domains/four switches/nine states |
| R-01 | Registered `soc_lint` | Complete filelist, no real warning/error |
| R-02 | Registered `soc_comp` | VCS top compile/elaboration succeeds |
| R-03 | RTL quality | Canonical files/modules resolve |
| S-01 | Static source scan | No RTL/UPF physical switch implementation; expected objects present |
| S-02 | Registered `soc_syn`, DC | Fresh netlist, DDC, canonical/saved UPF, timing reports, and SVF are captured under one immutable run ID/fingerprint; DC low-power audits pass |
| F-01 | Registered `upf_formal_verify` | RTL+canonical UPF is equivalent to DC netlist+saved UPF; `verification_status=SUCCEEDED` |
| C-01 | Registered `upf_clp_check` | Native 1801 pre-synthesis RTL/UPF checks complete with zero failed error-level rules |

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

## Synthesis checks

The synthesis owner must inspect real reports before finalizing counts. The source-level structural estimate is 36 ELS and 44 pure H2L LS. DC Tcl may document these as provisional, but must not treat them as validated until a real registered `soc_syn` run supplies the exact hierarchy/netlist counts.

Synthesis must also prove exactly five domains, four abstract switches, all supplies/states, all eight MacroPG paths, all four cores/controllers, complete saved UPF, no physical switch cell, and ordinary non-PG Verilog with no `VDD*`, `VSS*`, `VGND`, `VPWR`, `VPWRIN`, or other named PG connection. The same invocation must emit a non-empty SVF before Formality starts.

The Formality/CLP wrapper must receive the exact `soc_syn` `run_id` and
`source_fingerprint`, reject current-source drift, resolve the netlist,
canonical/saved UPF, and SVF only from that immutable evidence directory, and
record SHA-256 digests for every consumed input and produced report.

## Formality with UPF

- Load all standard-cell, teaching low-power, and PG-aware hard-macro DBs.
- Apply the fresh DC SVF before reading either design container.
- Reference: synthesizable source RTL plus canonical generated UPF.
- Implementation: ordinary DC netlist plus the full UPF saved by that DC run.
- Preserve full `report_upf` output for both containers, setup status, matching,
  and final verification status.
- Accept only a real `verify` return with `verification_status=SUCCEEDED`.
  Missing/stale evidence, inconclusive, failed, or aborted results are failure.

## CLP RTL/UPF consistency

- Use Conformal Low Power native IEEE 1801 with UPF 2.1 and the
  `pre_synthesis` golden analysis style.
- Read the same synthesizable RTL, canonical UPF, low-power Liberty views, and
  PG-aware hard-macro Liberty used by the DC teaching flow.
- Preserve full 1801 rule summary, failed error-rule report, power-intent
  object report, low-power strategy report, design data, and black-box report.
- Any critical read/elaboration issue or any failed error-level 1801 rule is
  failure. The registered wrapper cannot create a waiver or accept a marker
  without fresh non-empty reports.
- Parse both the filtered error-rule XML and text summary fail-closed before
  accepting `UPF_CLP_PASS`; only the registered MCP wrapper emits that marker.
- Reject non-empty or unknown XML schemas until they are validated against a
  real pass/fail fixture from the installed CLP release.

## Future functional goals

If simulation is later authorized, independently cover power-up, request/response, isolation-before-off, state loss, and recovery for all four cores; exercise all nine system combinations at the control-intent level; and retain SRAM, PLL, and pad behavioral checks. Until then these are unverified goals, not PASS claims.

## Design evidence

Power Compiler UG U-2022.12-SP3 pp. 228–229 requires isolation on switchable-domain outputs and level shifting across differing voltages. Page 210 supports H2L, L2H, dual-rail, and enable-level-shifter implementations. The local teaching views are explicitly non-signoff assumptions used only to exercise these mechanisms.
