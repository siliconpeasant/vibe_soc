# UPF/DC Low-Power Demo Architecture

## 1. Purpose and scope

`upf_dc_demo` is a bounded teaching design for exercising Synopsys Design Compiler/Power Compiler UPF elaboration and low-power-cell insertion. It demonstrates one always-on 1.8 V digital domain, one switchable 1.2 V digital domain, a 3.3 V IO interface, and explicit power/ground connectivity for PLL, SRAM, and IO-pad macro stubs.

The PLL, SRAM, and IO pads are behavioral models for simulation and black-box interfaces for synthesis. They are not foundry IP, are not characterized macro libraries, and must not be interpreted as silicon-ready implementations. The Sky130 HD teaching DB supplies ordinary digital and selected low-power cells only; it does not characterize every 1.2 V/1.8 V/3.3 V crossing or any of these macro stubs. No signoff claim is made.

This document deliberately defines no bus fabric, register map, or address map. Interfaces are point-to-point and small enough to inspect in a synthesized netlist.

## 2. Top hierarchy and domain ownership

```text
upf_dc_demo                             PD_AO, 1.8 V primary
├── u_aon_ctrl                          PD_AO, synthesizable control RTL
├── u_sw_core                           PD_SW, 1.2 V switchable RTL
├── u_pll_macro                         PD_AO extent, PLL black-box/stub
├── u_sram_macro                        PD_AO extent, SRAM black-box/stub
├── u_pad_in                            PD_AO extent, input-pad black-box/stub
└── u_pad_out                           PD_AO extent, output-pad black-box/stub
```

There are exactly two power domains:

- `PD_AO` is created with the top-level extent (or an equivalent explicit element set containing every instance except `u_sw_core`). Its primary supply is `SS_VDD_AO_VSS`. `u_pll_macro`, `u_sram_macro`, `u_pad_in`, and `u_pad_out` remain members of this domain.
- `PD_SW` contains only `u_sw_core`. Its switched 1.2 V primary supply is `SS_VDD_SW_VSS`.

No PLL, memory, IO, or pad power domain is created. Their dedicated rails are additional supply sets associated with `PD_AO`, not domain boundaries. This separation is essential: macro PG connectivity does not imply a new power domain.

## 3. Supply architecture

All rails share `VSS`. The demo does not model ground switching or separate analog ground bounce.

| Supply set | Power net | Ground net | Nominal voltage | Domain association | Purpose |
|---|---|---|---:|---|---|
| `SS_VDD_AO_VSS` | `VDD_AO` | `VSS` | 1.8 V | `PD_AO.primary` | Always-on standard-cell logic |
| `SS_VDD_PLL_VSS` | `VDD_PLL` | `VSS` | 1.8 V | `PD_AO.extra_supplies_1` | PLL stub PG pins |
| `SS_VDD_MEM_VSS` | `VDD_MEM` | `VSS` | 1.8 V | `PD_AO.extra_supplies_2` | SRAM stub PG pins |
| `SS_VDDIO_VSS` | `VDDIO` | `VSS` | 3.3 V | `PD_AO.extra_supplies_3` | IO-pad stub PG pins |
| `SS_VDD_SW_IN_VSS` | `VDD_SW_IN` | `VSS` | 1.2 V | No domain-supply handle | Abstract switch input supply |
| `SS_VDD_SW_VSS` | `VDD_SW` | `VSS` | 1.2 V when on | `PD_SW.primary` | Abstract switch output and switchable logic |

Only the numeric `extra_supplies_1` through `extra_supplies_3` handles are associated with `PD_AO`; they serve the PLL, SRAM, and IO macros. `VDD_SW_IN` and `VDD_SW` remain UPF supply objects used by the abstract switch rule, but neither is an additional `PD_AO` supply. `VDD_SW` is associated with `PD_SW` only as its primary supply. See *Power Compiler User Guide*, U-2022.12-SP3, pp. 227 and 268.

`VDD_SW` is the output of the logical UPF power switch `PSW_SW`, driven by active-high always-on control `sw_en`. `PSW_SW` is only a virtual/generic switch rule: UPF records its input supply, output supply, control, and ON condition, while the physical switch cell and its rail hookup are owned by backend implementation. RTL and synthesis shall not pre-instantiate, map, or preserve a power-switch cell, and UPF shall not use hierarchical `MacroPG` connections for one.

This boundary follows *Power Compiler User Guide*, U-2022.12-SP3, pp. 358–359: `create_power_switch` creates a virtual instance and tells the tool that a generic switch resides at a scope; Power Compiler does not perform power-switch insertion, but passes the information to IC Compiler II for implementation. The authoritative synthesis handoff is the saved UPF switch object, not a leaf switch macro in the synthesized hierarchy.

## 4. Exact macro PG-pin mapping

Functional RTL and behavioral macro models contain signal ports only. The synthesis macro views come from `macro_pg_stub.db`, where the supply terminals are Liberty `pg_pin` objects; canonical UPF binds those objects hierarchically. The PG mapping below is normative for the in-memory MV database, PG reports, and saved full UPF. It does not appear in source RTL or the delivered ordinary Verilog netlist.

| Instance | Domain membership | PG pin | Connected supply net | Supply-set role |
|---|---|---|---|---|
| `u_pll_macro` | `PD_AO` | `VDD` | `VDD_PLL` | `SS_VDD_PLL_VSS.power` |
| `u_pll_macro` | `PD_AO` | `VSS` | `VSS` | `SS_VDD_PLL_VSS.ground` |
| `u_sram_macro` | `PD_AO` | `VDD` | `VDD_MEM` | `SS_VDD_MEM_VSS.power` |
| `u_sram_macro` | `PD_AO` | `VSS` | `VSS` | `SS_VDD_MEM_VSS.ground` |
| `u_pad_in` | `PD_AO` | `VDDIO` | `VDDIO` | `SS_VDDIO_VSS.power` |
| `u_pad_in` | `PD_AO` | `VSSIO` | `VSS` | `SS_VDDIO_VSS.ground` |
| `u_pad_out` | `PD_AO` | `VDDIO` | `VDDIO` | `SS_VDDIO_VSS.power` |
| `u_pad_out` | `PD_AO` | `VSSIO` | `VSS` | `SS_VDDIO_VSS.ground` |

The `connect_supply_net` object paths must resolve after synthesis links the Liberty macro views. Hierarchical macro PG-pin binding is the intended mechanism described by *Power Compiler User Guide*, U-2022.12-SP3, p. 258. The shared `VSS` connection is repeated explicitly for auditability rather than inferred from naming.

## 5. Bounded functional interfaces

- `u_aon_ctrl` owns reset synchronization, `sw_pwr_en`, `sw_iso_n`, and a small request/response handshake to `u_sw_core`.
- `u_sw_core` has one request bit, a small data input, one valid bit, and a small result output. It contains enough sequential/combinational RTL for inserted boundary cells to be visible.
- `u_pll_macro` accepts a reference clock and reset/power-down control and returns `pll_lock` plus a modeled clock output. The modeled PLL clock is observable only; no sequential RTL in the demo is clocked by it. This avoids generated-clock timing and CDC concerns obscuring the UPF experiment.
- `u_sram_macro` exposes a single-port, shallow teaching interface: clock, chip enable, write enable, a small address, write data, and read data. It is a black box for synthesis; no address mapping is implied.
- `u_pad_in` converts one external pad input to one core-side digital signal. `u_pad_out` converts one core-side digital signal to one external pad output. Pad ESD, slew, drive strength, and physical pad-ring behavior are outside scope.
- No power-switch macro appears in the functional hierarchy. `sw_en` is only the functional control signal referenced by the abstract `PSW_SW` rule; backend owns the physical switch array and PG routing.

The SRAM is always-on in this architecture because it belongs to `PD_AO`. Retention is therefore neither required nor demonstrated.

## 6. Digital crossings and protection

| Crossing | Voltage/state relation | Required strategy | Teaching intent |
|---|---|---|---|
| `PD_AO` → `PD_SW` | 1.8 V to switchable 1.2 V | High-to-low level shifter | Exercise input LS insertion |
| `PD_SW` → `PD_AO` | Switchable 1.2 V to 1.8 V | Isolation clamp 0, plus low-to-high level shifter | Exercise isolation and output LS insertion |
| Pad input → core boundary | 3.3 V IO model to 1.8 V AO | Supply attributes plus analog-net exemption | Real characterized input pad owns conversion; no core LS |
| Core boundary → pad output | 1.8 V AO to 3.3 V IO model | Supply attributes plus analog-net exemption | Real characterized output pad owns conversion; no core LS |

`sw_iso_n` is generated in `PD_AO`; isolation is enabled before `PD_SW` is switched off and released only after power restoration. The SW-to-AO isolation and low-to-high strategies are co-located at `self`/`PD_SW` and map to one dual-rail enable-level-shifter cell. Its low-side data rail is `VDD_SW`; the explicit isolation supply `VDD_AO` powers its high-side output and control, so clamp behavior remains always-on when `VDD_SW` is off. No retention strategy is required.

Sky130 HD low-power cells used for this demo are teaching mappings. Generated 1.2/1.8 V library variants relabel voltage maps only and do not recharacterize timing or power. Their only purpose is to exercise DC insertion. The 3.3 V IO boundary is deliberately left to the hard pad macros and excluded from core-cell insertion.

## 7. Normative UPF shape

The generated UPF may include tool-version-specific options, but it must preserve the following architecture:

```tcl
create_supply_net VSS
create_supply_net VDD_AO
create_supply_net VDD_PLL
create_supply_net VDD_MEM
create_supply_net VDDIO
create_supply_net VDD_SW_IN
create_supply_net VDD_SW

create_supply_set SS_VDD_AO_VSS    -function {power VDD_AO}    -function {ground VSS}
create_supply_set SS_VDD_PLL_VSS   -function {power VDD_PLL}   -function {ground VSS}
create_supply_set SS_VDD_MEM_VSS   -function {power VDD_MEM}   -function {ground VSS}
create_supply_set SS_VDDIO_VSS     -function {power VDDIO}     -function {ground VSS}
create_supply_set SS_VDD_SW_IN_VSS -function {power VDD_SW_IN} -function {ground VSS}
create_supply_set SS_VDD_SW_VSS    -function {power VDD_SW}    -function {ground VSS}

create_power_domain PD_AO -include_scope \
  -supply {primary SS_VDD_AO_VSS} \
  -supply {extra_supplies_1 SS_VDD_PLL_VSS} \
  -supply {extra_supplies_2 SS_VDD_MEM_VSS} \
  -supply {extra_supplies_3 SS_VDDIO_VSS}
create_power_domain PD_SW -elements {u_sw_core} \
  -supply {primary SS_VDD_SW_VSS}

connect_supply_net VDD_PLL -ports {u_pll_macro/VDD}
connect_supply_net VSS     -ports {u_pll_macro/VSS}
connect_supply_net VDD_MEM -ports {u_sram_macro/VDD}
connect_supply_net VSS     -ports {u_sram_macro/VSS}
connect_supply_net VDDIO   -ports {u_pad_in/VDDIO u_pad_out/VDDIO}
connect_supply_net VSS     -ports {u_pad_in/VSSIO u_pad_out/VSSIO}

create_power_switch PSW_SW \
  -domain PD_SW \
  -input_supply_port {TVDD VDD_SW_IN} \
  -output_supply_port {VDD VDD_SW} \
  -control_port {NSLEEPIN u_aon_ctrl/sw_en_o} \
  -on_state {normal TVDD {NSLEEPIN}}
```

The final generated UPF must also define supply states, isolation/level-shifter strategies, control polarity, and cell mappings where compatible teaching cells exist. `PSW_SW` must retain the four abstract rule elements shown above. No switch `HardMacros`, switch `MacroPG`, or `map_power_switch` implementation mapping is part of synthesis. Exact command spelling must be validated against the installed Power Compiler UPF version.

## 8. Synthesis database and deliverables

DC/Power Compiler shall load UPF and the PG-aware Liberty views so that domain ownership, all eight PLL/SRAM/IO MacroPG connections, power-switch intent, and inserted low-power cells can be checked in the internal MV database. It shall save a complete full UPF for backend implementation.

The Verilog handoff has a different purpose. `upf_dc_demo_netlist.v` shall be written as ordinary non-PG Verilog without `write_file -pg`. It contains functional connectivity and the inserted low-power cell instances, but it must omit all supply ports, PG supply nets, and PG-pin named connections. Prohibited Verilog content includes supply objects or pins named `VDD*`, `VSS*`, `VDDIO`, `VSSIO`, `VGND`, `VPWR`, and `VPWRIN`. The eight MacroPG bindings remain visible in UPF/reports only.

This is an intentional two-artifact contract. *Power Compiler User Guide*, U-2022.12-SP3, p. 416 states that `write_file -pg` writes complete PG supply connections, including leaf-cell connections; pp. 418–419 show that form emitting named PG pins, supply nets, and power-switch output nets. Because this demo's Verilog deliverable must be non-PG, synthesis omits the `-pg` option while retaining the separate saved full UPF.

## 9. DC experiment and acceptance evidence

The synthesis experiment should verify, using DC/Power Compiler reports, saved full UPF, and the ordinary generated netlist:

1. Exactly two domains exist: `PD_AO` and `PD_SW`; no macro-specific domain exists.
2. `PD_AO.primary` resolves to `SS_VDD_AO_VSS`, and only its three macro extra supplies resolve in the documented numbered slots without `UPF-707a`.
3. Every PLL/SRAM/IO macro PG pin resolves to the exact hierarchical supply net in the mapping table, with a common `VSS`.
4. Abstract switch `PSW_SW` is accepted as UPF intent and remains in saved UPF with input/output supplies, control, and ON state; no RTL, DC-instantiated, or mapped physical switch cell is expected.
5. Isolation is inserted on switchable-domain outputs and is powered from the always-on supply.
6. 1.8 V↔1.2 V level-shifter strategies are inserted or produce an explicit, attributable teaching-library mapping limitation.
7. The 3.3 V IO supply attributes and analog exemptions are preserved; no core standard-cell LS is inserted on pad-boundary nets.
8. The PLL, SRAM, and pads remain black boxes, their signal ports link successfully, and their PG connectivity remains provable in the internal reports and saved UPF.
9. No switch macro appears in RTL, linked macro views, hard-macro declarations, hierarchical PG bindings, or the synthesized hierarchy; backend consumes the saved UPF rule for physical implementation.
10. No sequential endpoint uses the PLL stub output as a clock.
11. The ordinary Verilog contains nine ELS isolation instances and eleven pure high-to-low LS instances, for twenty total level-shifter instances when ELS cells are included.
12. The ordinary Verilog contains no supply port/net or PG-pin named connection, including `VDD*`, `VSS*`, `VDDIO`, `VSSIO`, `VGND`, `VPWR`, and `VPWRIN`.
13. The saved full UPF retains all six supply sets, all eight PLL/SRAM/IO MacroPG bindings, isolation/level-shifter strategies, power states, and virtual `PSW_SW`.

This architecture stage does not run simulation. Behavioral macro correctness, pad electrical behavior, analog behavior, CDC, gate-level simulation, formal equivalence, STA signoff, IR/EM, DRC/LVS, and physical implementation are outside this document's acceptance scope.

## 10. Assumptions, limitations, and blockers

- A licensed DC/Power Compiler installation with UPF support is available for the later synthesis stage.
- The generated stub Liberty/DB matches each behavioral macro's functional signal ports and adds the synthesis-only Liberty `pg_pin` objects referenced by UPF.
- The installed tool accepts the documented `extra_supplies_#` association syntax. If it does not, that tool-version diagnostic is a blocker and the UPF must not silently create macro-specific domains as a workaround.
- Exact low-power-cell mapping depends on the local Sky130 HD teaching DB. Missing or voltage-incompatible cells are a known blocker to mapped/signoff-quality results, but not to demonstrating and reporting UPF intent.
- Macro rails are logical UPF supplies only; no real PLL, SRAM, pad, voltage-regulator, or analog model is supplied. No physical or characterized power-switch implementation is part of RTL or synthesis.
- Nominal voltages are pedagogical annotations. They do not establish electrical compatibility.

Reference evidence: *Power Compiler User Guide*, U-2022.12-SP3, p. 227 (power-domain concept and association of multiple supplies), p. 268 (numbered `extra_supplies_#` syntax/restrictions), p. 258 (hierarchical `connect_supply_net` use for PLL/SRAM/IO macro PG connectivity), pp. 358–359 (`create_power_switch` is virtual/generic, Power Compiler does not insert it, and the information is passed to IC Compiler II), and pp. 416, 418–419 (`write_file -pg` emits complete PG supply connections, named leaf PG pins, and relevant supply nets).

## 11. Pipeline handoff

Because this document changes the domain model and invalidates any previously generated RTL/UPF assumptions, the repository `doc` stage must be rerun and accepted before RTL, UPF, synthesis constraints, or DC scripts are regenerated. Downstream stages must remain pending until that gate completes.
