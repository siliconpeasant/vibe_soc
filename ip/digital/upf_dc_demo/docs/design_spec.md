# UPF/DC demo design specification

## Scope

`upf_dc_demo` is a teaching subsystem for strict UPF generation and Synopsys DC/Power Compiler low-power synthesis. It contains an always-on controller, one switchable digital core, and behavioral/synthesis-blackbox stubs for a PLL, a 16 x 8 SRAM, an input pad, and an output pad. The stubs are not foundry IP. The local Sky130 HD teaching DB does not establish characterization for every 1.2 V, 1.8 V, and 3.3 V combination, so this demo makes no signoff claim.

There is no bus, address map, software register, interrupt, generated-clock endpoint, or physical switch implementation.

## Hierarchy and domain ownership

| Instance | Module | Domain | Function |
|---|---|---|---|
| top scope | `upf_dc_demo` | `PD_AO` | Integration glue |
| `u_aon_ctrl` | `upf_dc_demo_aon_ctrl` | `PD_AO` | Power/isolation sequencing and response capture |
| `u_pll_macro` | `upf_dc_demo_pll_macro` | `PD_AO` | PLL teaching stub |
| `u_sram_macro` | `upf_dc_demo_sram_16x8` | `PD_AO` | SRAM teaching stub |
| `u_pad_in` | `upf_dc_demo_pad_in` | `PD_AO` | Input-pad teaching stub |
| `u_pad_out` | `upf_dc_demo_pad_out` | `PD_AO` | Output-pad teaching stub |
| `u_power_switch_macro` | `upf_dc_demo_power_switch_macro` | `PD_AO` | Pre-instantiated PG-netlist retention anchor |
| `u_sw_core` | `upf_dc_demo_sw_core` | `PD_SW` | Switchable arithmetic RTL |

Exactly two power domains exist. `PD_AO` owns the top extent and every instance except `u_sw_core`; `PD_SW` contains only `u_sw_core`. A dedicated macro supply is an additional supply association, not a new power domain.

## Supplies and PG pins

| Supply set | Nets | Nominal voltage | Association |
|---|---|---:|---|
| `SS_VDD_AO_VSS` | `VDD_AO` / `VSS` | 1.8 V | `PD_AO.primary` |
| `SS_VDD_PLL_VSS` | `VDD_PLL` / `VSS` | 1.8 V | `PD_AO.extra_supplies_1` |
| `SS_VDD_MEM_VSS` | `VDD_MEM` / `VSS` | 1.8 V | `PD_AO.extra_supplies_2` |
| `SS_VDDIO_VSS` | `VDDIO` / `VSS` | 3.3 V | `PD_AO.extra_supplies_3` |
| `SS_VDD_SW_IN_VSS` | `VDD_SW_IN` / `VSS` | 1.2 V | Abstract switch input; `PD_AO.extra_supplies_4` for macro `VIN` |
| `SS_VDD_SW_VSS` | `VDD_SW` / `VSS` | 1.2 V ON | `PD_SW.primary`; `PD_AO.extra_supplies_5` for macro `VOUT` |

Active-high `sw_en`, generated in `PD_AO`, controls abstract switch `PSW_SW` from `VDD_SW_IN` to `VDD_SW`. `VSS` is common. Power Compiler preserves this UPF behavior but does not instantiate a switch cell; physical insertion is deferred to implementation.

Behavioral RTL macro views have no PG ports. Synthesis links PG-aware Liberty blackbox views, and UPF shall bind their `pg_pin` objects explicitly with hierarchical `connect_supply_net`:

| Hierarchical pin | Net |
|---|---|
| `u_pll_macro/VDD` | `VDD_PLL` |
| `u_pll_macro/VSS` | `VSS` |
| `u_sram_macro/VDD` | `VDD_MEM` |
| `u_sram_macro/VSS` | `VSS` |
| `u_pad_in/VDDIO` | `VDDIO` |
| `u_pad_in/VSSIO` | `VSS` |
| `u_pad_out/VDDIO` | `VDDIO` |
| `u_pad_out/VSSIO` | `VSS` |
| `u_power_switch_macro/VIN` | `VDD_SW_IN` |
| `u_power_switch_macro/VOUT` | `VDD_SW` |
| `u_power_switch_macro/VSS` | `VSS` |

RTL shall pre-instantiate `upf_dc_demo_power_switch_macro u_power_switch_macro` with only signal input `en_i`, connected to `sw_en`. The RTL module has no PG ports and no functional supply-transfer model. Its linked Liberty view shall retain the same signal pin and add `VIN`, `VOUT`, and `VSS` as `pg_pin` objects. Canonical UPF shall connect those PG pins as shown above while retaining abstract `PSW_SW`. This is required because DC does not instantiate switch cells and `write_file -pg` omits PG nets and ports that do not feed leaf PG pins; the pre-instantiated macro therefore anchors `VDD_SW_IN` in the PG netlist without duplicating UPF switch behavior.

The implementation contract is therefore conjunctive: saved UPF must retain
the abstract `PSW_SW`, while the synthesized hierarchy must retain exactly the
pre-instantiated `u_power_switch_macro`. A DC-created replacement switch cell
is neither expected nor accepted. The macro's source-level interface remains
`en_i` only; `VIN`, `VOUT`, and `VSS` exist solely as Liberty PG pins connected
by UPF. This contract is based on *Power Compiler User Guide*,
U-2022.12-SP3, p. 359 and pp. 418–419.

No pad core-rail PG pins are added. The 3.3 V IO versus 1.8 V core boundary is described by driver/receiver attributes while the pads remain members of `PD_AO`. The point-to-point pad boundary ports are marked analog so a core standard-cell LS is not inserted in place of a real characterized IO macro.

## Behavior and sequencing

`u_aon_ctrl` accepts `sw_power_req_i` and owns active-high `sw_en` plus active-high isolation release `sw_iso_n`. Reset disables power, asserts isolation, and clears responses. For power-up, it asserts `sw_en`, waits two full `clk` edges, then asserts `sw_iso_n`. For power-down, it clears `sw_iso_n`, waits one `clk` edge, then clears `sw_en`. Requests are admitted only when both signals are high.

`u_sw_core` runs from the dedicated top input `sw_clk`, which is related to the 1.2 V switchable supply. It registers `req_data_i + 8'h01` and pulses response valid when powered and requested. Reset or behavioral power loss clears its state; no retention is used. RTL shadow behavior aids deterministic elaboration but is not evidence of inserted isolation.

The SRAM is always-on and provides synchronous 16 x 8 single-port read/write behavior. The PLL stub copies its reference clock to an observation output when enabled and asserts lock after four reference edges; that output never clocks sequential RTL. Pad stubs are bounded digital pass-through models with no ESD, slew, drive, or analog behavior.

## UPF and synthesis requirements

UPF shall create exactly the memberships and supplies above, use explicit `extra_supplies_1` through `extra_supplies_5`, connect every macro PG pin hierarchically, and retain abstract `PSW_SW` alongside the pre-instantiated switch macro. The last two additional supplies make both switch rails available to the `PD_AO` switch macro; the final MV report must contain no `UPF-707a`. AO-to-SW request/control paths require 1.8-to-1.2 high-to-low level shifting. SW-to-AO response paths require clamp-0 isolation plus 1.2-to-1.8 low-to-high shifting, co-located at the `PD_SW` boundary in one dual-rail enable-level-shifter cell powered by `VDD_SW` and always-on `VDD_AO`. `sw_clk` enters directly at the `PD_SW` voltage. Pad ports retain explicit IO/AO supply attributes but are analog-exempt from core LS insertion.

Later synthesis uses 10.000 ns `clk` and `sw_clk`, 0.10 ns clock uncertainty and transition, 1.0 ns digital IO delays, and 0.05 pF output load. Preserve macro instances, link functional signal ports against PG-aware blackbox DB views, load complete UPF connectivity, and emit the final PG netlist with `write_file -pg`. Validation is document completeness, `upf-gen --strict`, registered `soc_lint`, `soc_comp`, `soc_syn`, and real DC domain/supply/strategy/PG/cell reports. `soc_sim` is not run.

Tool/license absence, an extra domain, unresolved PG pins, wrong supply association, missing isolation coverage, or unsupported LS mapping is reported honestly. Reference evidence: *Power Compiler User Guide*, U-2022.12-SP3, p. 227 for domains with multiple supplies, p. 268 for numbered `extra_supplies_#` syntax/restrictions, p. 258 for hierarchical `connect_supply_net` to macro PG pins, p. 359 for deferring physical power-switch insertion, and pp. 418–419 for non-instantiation of switch cells and omission of PG nets/ports without leaf PG loads.
