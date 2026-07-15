# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler case with five power domains:

- `PD_AO`: always-on 1.8 V, four independent AO controllers, PLL/SRAM/IO hard macros.
- `PD_SW`, `PD_ACC`, `PD_PERI`, `PD_MEDIA`: independent switchable 1.2 V arithmetic cores.

Each switchable domain has a dedicated input rail, switched rail, abstract backend-owned `PSW_*` rule, AO-to-domain H2L strategy, and domain-to-AO clamp-0 isolation/L2H ELS strategy. No physical switch cell is present in RTL, Liberty hard macros, UPF macro bindings, or ordinary Verilog. All switchable-domain communication terminates in `PD_AO`.

The compact local source is ignored `de/syn/power_intent.xlsx`, with exactly seven sheets: `README`, `Supplies`, `Domains`, `PowerStates`, `Isolation_LS`, `HardMacros`, and `PortAttributes`. Registered strict `upf-gen.upf_generate` produces the committed canonical UPF, Draw.io, Excalidraw, and summary; generated files are never hand-edited. The four hard macros stay in `PD_AO` and their eight `PIN=NET` connections remain visible in both diagrams and UPF.

The nine system states are `ALL_ON`, `SW_OFF`, `ACC_OFF`, `PERI_OFF`, `MEDIA_OFF`, `COMPUTE_ONLY`, `IO_STANDBY`, `MEDIA_MODE`, and `DEEP_SLEEP`. Each explicitly covers all four switchable domains, all four switched rails, AO/macro rails, and all four input rails.

Power Compiler UG U-2022.12-SP3 pp. 228–229 requires isolation when signals leave a switchable domain and level shifting across differing voltages. Page 210 describes H2L, L2H, dual-rail, and enable-level-shifter models. This project reuses non-signoff teaching 1.8↔1.2 views solely to exercise the flow; they are not characterized implementation evidence.

## Tool and handoff contract

Agents use registered `soc_lint`, `soc_comp`, and `soc_syn` tools only. The completed flow ran lint, VCS compile/elaboration, and DC/Power Compiler synthesis; it did not run simulation. DC loads the PG-aware macro views and full UPF internally, preserves eight MacroPG connections in reports/saved UPF, and writes ordinary non-PG Verilog.

The RTL structure predicts 36 ELS cells (four 9-bit protected outputs) and 44 pure H2L LS cells (four 11-bit AO input boundaries). The registered DC run for the current source fingerprint confirmed exactly those counts: 36 ELS, 44 pure H2L, and 80 total level shifters. These remain teaching-flow evidence rather than characterized signoff data.

The ordinary netlist must omit supply rails and named PG pins. The saved full UPF is the backend power-intent handoff and must retain exactly five domains, four switches, four isolation rules, eight LS rules, twelve supply sets, eight hard-macro PG paths, and all nine system states.

No retention, direct switchable-domain crossing, bus/register map, analog electrical model, physical switch implementation, simulation claim, or tapeout claim is included.
