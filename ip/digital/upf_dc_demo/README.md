# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler case with five power domains:

- `PD_AO`: always-on 1.8 V, four independent AO controllers, PLL/SRAM/IO hard macros.
- `PD_SW`, `PD_ACC`, `PD_PERI`, `PD_MEDIA`: independent switchable 1.2 V arithmetic cores.

Each switchable domain has a dedicated input rail, switched rail, abstract backend-owned `PSW_*` rule, AO-to-domain H2L strategy, and domain-to-AO clamp-0 isolation/L2H ELS strategy. No physical switch cell is present in RTL, Liberty hard macros, UPF macro bindings, or ordinary Verilog. All switchable-domain communication terminates in `PD_AO`.

The compact local source is ignored `de/syn/power_intent.xlsx`, with exactly seven sheets: `README`, `Supplies`, `Domains`, `PowerStates`, `Isolation_LS`, `HardMacros`, and `PortAttributes`. Registered strict `upf-gen.upf_generate` produces the committed canonical UPF, Draw.io, Excalidraw, and summary; generated files are never hand-edited. The four hard macros stay in `PD_AO` and their eight `PIN=NET` connections remain visible in both diagrams and UPF.

The nine system states are `ALL_ON`, `SW_OFF`, `ACC_OFF`, `PERI_OFF`, `MEDIA_OFF`, `COMPUTE_ONLY`, `IO_STANDBY`, `MEDIA_MODE`, and `DEEP_SLEEP`. Each explicitly covers all four switchable domains, all four switched rails, AO/macro rails, and all four input rails.

Power Compiler UG U-2022.12-SP3 pp. 228–229 requires isolation when signals leave a switchable domain and level shifting across differing voltages. Page 210 describes H2L, L2H, dual-rail, and enable-level-shifter models. This project reuses non-signoff teaching 1.8↔1.2 views solely to exercise the flow; they are not characterized implementation evidence.

## Tool and handoff contract

Agents use registered `soc_lint`, `soc_comp`, `soc_syn`, `soc_formal`, and
`upf-gen` tools only. Formality is a general post-DC stage rather than an
UPF-only stage: a plain synthesis snapshot runs ordinary RTL-to-netlist
equivalence, while a snapshot containing both canonical and saved UPF
automatically runs the UPF-aware mode. Pass `soc_formal` the exact `run_id`
and `source_fingerprint` returned by `soc_syn`; it rejects RTL drift and uses
the immutable netlist, SVF, and optional UPF pair from that synthesis snapshot.
Conformal Low Power remains an independent native IEEE 1801 RTL/UPF
consistency check. This flow does not claim behavioral simulation. DC loads
the PG-aware macro views and full UPF internally, preserves eight MacroPG
connections in reports/saved UPF, writes ordinary non-PG Verilog, saves the
implementation UPF, and emits the SVF consumed by Formality.

Synthesis, Formality, and CLP consume the same immutable `de/syn/rtl.f`;
there is no derived `logic_rtl.f`. The shared synthesis view defines
`SYNTHESIS`, so simulation-only hard-macro behavior is hidden while the
PG-aware Liberty views supply the macro interfaces. Public drivers live under
`scripts/syn/`, `scripts/formal/`, and `scripts/clp/`; this module keeps
only its design-specific UPF assertions in `de/syn/upf_checks.tcl`.

UPF-aware Formality compares synthesizable RTL plus canonical UPF against the
ordinary DC netlist plus DC-saved UPF and accepts only
`verification_status=SUCCEEDED`.
CLP independently elaborates the synthesizable RTL with the canonical UPF in
native 1801 pre-synthesis mode and rejects failed error-level rules. Its XML
and text error summaries are parsed fail-closed by the registered wrapper;
only that wrapper emits `UPF_CLP_PASS`, and an unknown XML schema is rejected.
Fresh reports live under ignored `de/run/formality/` and `de/run/clp/`.

The RTL structure predicts 36 ELS cells (four 9-bit protected outputs) and 44 pure H2L LS cells (four 11-bit AO input boundaries). The registered DC run for the current source fingerprint confirmed exactly those counts: 36 ELS, 44 pure H2L, and 80 total level shifters. These remain teaching-flow evidence rather than characterized signoff data.

The ordinary netlist must omit supply rails and named PG pins. The saved full UPF is the backend power-intent handoff and must retain exactly five domains, four switches, four isolation rules, eight LS rules, twelve supply sets, eight hard-macro PG paths, and all nine system states.

No retention, direct switchable-domain crossing, bus/register map, analog electrical model, physical switch implementation, simulation claim, or tapeout claim is included.
