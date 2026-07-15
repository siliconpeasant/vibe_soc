# UPF/DC five-domain architecture

## Purpose and evidence boundary

`upf_dc_demo` is a teaching-only Power Compiler design with one 1.8 V always-on domain and four independently switchable 1.2 V digital domains. It demonstrates abstract backend-owned switches, AO-controlled shutdown sequencing, output isolation combined with low-to-high shifting, high-to-low input shifting, a nine-state system power-state matrix, and four PG-aware hard-macro views in the AO extent. It is not foundry, PVT, electrical, physical, or tapeout signoff evidence.

The architecture follows *Power Compiler User Guide*, U-2022.12-SP3, pp. 228–229: a crossing from a switchable domain requires isolation and a voltage-changing crossing requires level shifting. Page 210 describes high-to-low, low-to-high, dual-rail, and enable-level-shifter models. This project locally assumes its non-signoff teaching 1.8↔1.2 Liberty views can exercise those structures; the views are not recharacterized cells.

## Hierarchy and power-domain ownership

```text
upf_dc_demo                                      PD_AO, 1.8 V, include_scope
├── u_aon_ctrl                                   PD_AO controller for PD_SW
├── u_acc_aon_ctrl                               PD_AO controller for PD_ACC
├── u_peri_aon_ctrl                              PD_AO controller for PD_PERI
├── u_media_aon_ctrl                             PD_AO controller for PD_MEDIA
├── u_sw_core                                    PD_SW, 1.2 V switchable
├── u_acc_core                                   PD_ACC, 1.2 V switchable
├── u_peri_core                                  PD_PERI, 1.2 V switchable
├── u_media_core                                 PD_MEDIA, 1.2 V switchable
├── u_pll_macro                                  PD_AO hard macro
├── u_sram_macro                                 PD_AO hard macro
├── u_pad_in                                     PD_AO hard macro
└── u_pad_out                                    PD_AO hard macro
```

Exactly five domains exist: `PD_AO`, `PD_SW`, `PD_ACC`, `PD_PERI`, and `PD_MEDIA`. All communication between a switchable core and the rest of the design terminates in `PD_AO`; no direct switchable-domain crossing exists. The PLL, SRAM, and pads remain in `PD_AO`; their dedicated supplies are AO additional supplies rather than extra domains.

## Supply and switch architecture

All supplies share `VSS`; ground switching and retention are out of scope.

| Domain/role | Input supply | Switched/primary supply | Abstract switch | AO control |
|---|---|---|---|---|
| `PD_AO` | — | `VDD_AO` 1.8 V | — | — |
| `PD_SW` | `VDD_SW_IN` 1.2 V | `VDD_SW` 1.2 V | `PSW_SW` | `u_aon_ctrl/sw_en_o` |
| `PD_ACC` | `VDD_ACC_IN` 1.2 V | `VDD_ACC` 1.2 V | `PSW_ACC` | `u_acc_aon_ctrl/sw_en_o` |
| `PD_PERI` | `VDD_PERI_IN` 1.2 V | `VDD_PERI` 1.2 V | `PSW_PERI` | `u_peri_aon_ctrl/sw_en_o` |
| `PD_MEDIA` | `VDD_MEDIA_IN` 1.2 V | `VDD_MEDIA` 1.2 V | `PSW_MEDIA` | `u_media_aon_ctrl/sw_en_o` |

`PD_AO.primary` is `SS_VDD_AO_VSS`. Its only additional supplies are `SS_VDD_PLL_VSS`, `SS_VDD_MEM_VSS`, and `SS_VDDIO_VSS` in `extra_supplies_1..3`. Every input and switched rail remains a UPF supply object, but no switch rail is an AO additional supply.

Each `create_power_switch` is virtual/generic intent containing input supply, output supply, AO control, and active-high ON state. RTL, Liberty macro views, generated UPF, and ordinary Verilog must not instantiate, map, or hierarchically connect a physical power-switch cell. Backend implementation owns switch selection, array insertion, and PG routing.

## Macro PG ownership

The four hard macros remain visible in the generated diagrams and use exactly eight hierarchical bindings in the internal MV database and saved UPF:

| Instance | Domain | Bindings |
|---|---|---|
| `u_pll_macro` | `PD_AO` | `VDD=VDD_PLL; VSS=VSS` |
| `u_sram_macro` | `PD_AO` | `VDD=VDD_MEM; VSS=VSS` |
| `u_pad_in` | `PD_AO` | `VDDIO=VDDIO; VSSIO=VSS` |
| `u_pad_out` | `PD_AO` | `VDDIO=VDDIO; VSSIO=VSS` |

Functional RTL has no PG ports. `macro_pg_stub.db` supplies synthesis-only `pg_pin` metadata. The ordinary synthesized Verilog is written without `-pg` and therefore must omit supply rails and named PG-pin connections; the saved full UPF remains the backend power-connectivity handoff.

## Crossing architecture

For each suffix `X ∈ {SW, ACC, PERI, MEDIA}`:

- `PD_AO → PD_X`: reset, power shadow, request valid, and eight request-data bits require high-to-low shifting. `x_clk` is attributed directly to `SS_VDD_X_VSS` and excluded from clock LS insertion.
- `PD_X → PD_AO`: response valid and eight response-data bits require clamp-0 isolation plus low-to-high shifting at `self`, mapped to a dual-rail enable level shifter powered by the switched input side and always-on output/control side.
- The AO controller asserts power first, waits two AO clock edges, then releases active-low isolation. Power-down asserts isolation one edge before removing power.

The structural estimate is therefore 4 × 9 = 36 ELS cells and 4 × 11 = 44 pure high-to-low LS cells. This is a design-derived expectation only. The synthesis owner must replace or confirm exact Tcl assertions from real DC results.

## Nine-state system matrix

All states explicitly hold `PD_AO`, `VDD_PLL`, `VDD_MEM`, `VDDIO`, and all four switch input supplies ON. Each row explicitly covers all four switchable domain states and all four switched-output supply states.

| State | SW | ACC | PERI | MEDIA |
|---|---|---|---|---|
| `ALL_ON` | ON | ON | ON | ON |
| `SW_OFF` | OFF | ON | ON | ON |
| `ACC_OFF` | ON | OFF | ON | ON |
| `PERI_OFF` | ON | ON | OFF | ON |
| `MEDIA_OFF` | ON | ON | ON | OFF |
| `COMPUTE_ONLY` | ON | ON | OFF | OFF |
| `IO_STANDBY` | OFF | OFF | ON | OFF |
| `MEDIA_MODE` | OFF | OFF | ON | ON |
| `DEEP_SLEEP` | OFF | OFF | OFF | OFF |

The generator emits per-rail ON/OFF states, per-domain RUN/OFF states, and these system expressions on `PD_AO`. There is no retention state.

## Acceptance boundary

The doc/RTL owner must produce consistent documents, RTL, SDC, compact workbook, strict generated UPF/diagrams/summary, registered lint, and registered compile/elaboration. No simulation or synthesis is run in this stage. Later DC validation must prove exactly five domains and four switches, preserve eight hard-macro PG paths and all nine PST states, reject physical switch cells and PG content in ordinary Verilog, and measure real low-power-cell counts before finalizing assertions.
