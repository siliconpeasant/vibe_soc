# UPF/DC five-domain design specification

## Scope

`upf_dc_demo` contains one 1.8 V always-on domain (`PD_AO`) and four independent 1.2 V switchable domains (`PD_SW`, `PD_ACC`, `PD_PERI`, `PD_MEDIA`). Each switchable domain contains one arithmetic core and has a dedicated AO controller instance, input rail, switched rail, virtual power switch, output isolation/low-to-high strategy, and AO-to-domain high-to-low strategy. There are no direct crossings between switchable domains.

The local Sky130 teaching libraries are deliberately non-signoff views. Reusing their 1.8↔1.2 LS/ELS models is an engineering assumption for tool-flow demonstration, not characterized timing, power, or reliability evidence. The strategy rationale follows Power Compiler UG U-2022.12-SP3 pp. 228–229 and p. 210.

## Hierarchy and behavior

| Instances | Domain | Function |
|---|---|---|
| top scope, four `u_*_aon_ctrl`, PLL, SRAM, pads | `PD_AO` | AO sequencing, response capture, hard macros |
| `u_sw_core` | `PD_SW` | `sw_req_data_i + 8'h01` |
| `u_acc_core` | `PD_ACC` | `acc_req_data_i + 8'h01` |
| `u_peri_core` | `PD_PERI` | `peri_req_data_i + 8'h01` |
| `u_media_core` | `PD_MEDIA` | `media_req_data_i + 8'h01` |

Each core uses its dedicated `*_clk`, clears state on active-low reset or behavioral power loss, and pulses response valid for an admitted request. Each AO controller uses `clk`, independently sequences its active-high switch control and active-high isolation release, admits traffic only when both are asserted, and captures the protected response.

Reset disables all four power controls, asserts all four isolation strategies, and clears all responses. Power-up asserts the domain switch control, waits two complete AO edges, then releases isolation. Power-down asserts isolation, waits one AO edge, then removes power.

## Power intent

Exactly five domains and four virtual switches exist. Supply pairs are:

- `PD_AO.primary = SS_VDD_AO_VSS`, with `SS_VDD_PLL_VSS`, `SS_VDD_MEM_VSS`, and `SS_VDDIO_VSS` as its only three additional supplies.
- `PD_SW.primary = SS_VDD_SW_VSS`, fed virtually from `SS_VDD_SW_IN_VSS` by `PSW_SW`.
- `PD_ACC.primary = SS_VDD_ACC_VSS`, fed virtually from `SS_VDD_ACC_IN_VSS` by `PSW_ACC`.
- `PD_PERI.primary = SS_VDD_PERI_VSS`, fed virtually from `SS_VDD_PERI_IN_VSS` by `PSW_PERI`.
- `PD_MEDIA.primary = SS_VDD_MEDIA_VSS`, fed virtually from `SS_VDD_MEDIA_IN_VSS` by `PSW_MEDIA`.

The four `create_power_switch` rules are abstract backend intent only. No RTL module, Liberty hard macro, UPF hard-macro row, MacroPG connection, `map_power_switch`, or ordinary-netlist instance may implement a physical switch.

All four output boundaries clamp to zero and use an always-on isolation supply. Each low-to-high output strategy and isolation strategy share `upf_dc_demo_els_lh_1v2_1v8`; each AO-to-domain input strategy maps to `upf_dc_demo_ls_hl_1v8_1v2`. Each dedicated switchable clock has a driver-supply attribute matching the destination primary supply so it does not receive an LS.

The PLL, SRAM, and pads remain `PD_AO` hard macros with eight exact PG connections. Pad boundary supply attributes and analog exemption remain unchanged.

## System power states

The canonical workbook defines `ALL_ON`, four single-domain-off states, `COMPUTE_ONLY`, `IO_STANDBY`, `MEDIA_MODE`, and `DEEP_SLEEP`. Every row explicitly covers `PD_SW/ACC/PERI/MEDIA`, `VDD_SW/ACC/PERI/MEDIA`, always-on/macro rails, and `VDD_SW/ACC/PERI/MEDIA_IN`. The input rails never turn off in this bounded model; switched rails track their domain RUN/OFF state.

## Timing and synthesis handoff

`clk`, `sw_clk`, `acc_clk`, `peri_clk`, and `media_clk` are independent 10.000 ns clocks with 0.10 ns uncertainty and transition. Digital IO delay is 1.0 ns and output load is 0.05 pF. `pll_clk_mon_o` remains observation-only.

DC shall load PG-aware macro and teaching-cell libraries plus the complete UPF, check exactly five domains, four abstract switches, twelve supply sets, all four cores, four controllers, eight MacroPG paths, and all nine system states. It shall save full UPF and emit ordinary non-PG Verilog. That Verilog must contain functional and inserted low-power cells but no supply rail or named PG-pin connection. Provisional cell expectations are 36 ELS and 44 pure H2L LS; only real synthesis may establish final exact assertions.

## Exclusions

No bus, register map, interrupt, retention, generated-clock endpoint, physical switch cell, direct switchable-domain crossing, analog electrical model, or functional simulation is part of this stage.
