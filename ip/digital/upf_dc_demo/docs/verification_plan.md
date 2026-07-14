# UPF/DC demo verification plan

## Evidence boundary

This run validates document consistency, strict UPF generation, registered lint/compile/synthesis, and real DC/Power Compiler low-power reports. `soc_sim` is explicitly not run, and the pipeline `verif` stage remains pending. Behavioral requirements are reviewed and compiled but are not claimed as simulated.

No RTL shadow clamp, inferred gate, cell-name guess, or hand-written report proves isolation, level shifting, voltage support, PG connectivity, or a physical switch.

## Required execution matrix

| ID | Executor | Evidence | Pass condition |
|---|---|---|---|
| G-01 | `check_doc_completeness.py` | JSON result for the four canonical documents | `passed: true` |
| G-02 | `upf-gen --strict` | Generated UPF and summary | Zero exit; required supplies, memberships, strategies, and PG mappings present |
| G-03 | Registered `soc_lint` | Complete-filelist lint report | Successful structural lint for top `upf_dc_demo` |
| G-04 | Registered `soc_comp` | Real compile/elaboration report | Top and exact macro interfaces elaborate; this is not simulation |
| G-05 | Registered `soc_syn` | Synthesis artifacts and loop evidence | Success for the recorded source fingerprint |
| G-06 | DC/Power Compiler | UPF load/commit log; domain, supply, strategy, connectivity, inserted-cell, constraints, and mapped-netlist reports | All required objects resolve, or unsupported teaching-library mappings are explicitly reported |

EDA checks use registered tools. Direct Make, simulator, or synthesis shell fallbacks are prohibited.

## Domain, supply, and PG checks

| ID | Required result |
|---|---|
| U-01 | Exactly `PD_AO` and `PD_SW` exist |
| U-02 | `u_aon_ctrl`, `u_pll_macro`, `u_sram_macro`, `u_pad_in`, and `u_pad_out` belong to `PD_AO` |
| U-03 | Only `u_sw_core` belongs to `PD_SW` |
| U-04 | `PD_AO.primary = SS_VDD_AO_VSS` using 1.8 V `VDD_AO` and shared `VSS` |
| U-05 | `extra_supplies_1 = SS_VDD_PLL_VSS` using 1.8 V `VDD_PLL` |
| U-06 | `extra_supplies_2 = SS_VDD_MEM_VSS` using 1.8 V `VDD_MEM` |
| U-07 | `extra_supplies_3 = SS_VDDIO_VSS` using 3.3 V `VDDIO` |
| U-08 | `VDD_SW_IN` feeds abstract switch output `VDD_SW`; `PD_SW.primary = SS_VDD_SW_VSS`, nominal 1.2 V ON; neither switch supply is a `PD_AO` extra supply |
| U-09 | `u_pll_macro/VDD -> VDD_PLL` and `u_pll_macro/VSS -> VSS` |
| U-10 | `u_sram_macro/VDD -> VDD_MEM` and `u_sram_macro/VSS -> VSS` |
| U-11 | Both pad `VDDIO` pins connect to `VDDIO`; both `VSSIO` pins connect to `VSS` |
| U-12 | Functional RTL and behavioral macro views contain no PG ports; every PLL/SRAM/IO macro PG terminal resolves from a Liberty `pg_pin` through UPF |
| U-13 | RTL, synthesis macro views, hard-macro declarations, and synthesized hierarchy contain no power-switch cell |
| U-14 | UPF contains no hierarchical switch `MacroPG` connection and no `map_power_switch` implementation mapping |
| U-15 | `PSW_SW` remains an abstract UPF switch with input `VDD_SW_IN`, output `VDD_SW`, control `u_aon_ctrl/sw_en_o`, and an active-high ON state |
| U-16 | The PG netlist is not required to retain `VDD_SW_IN` or a switch-macro `VDD_SW` connection; the saved UPF is the switch-rule evidence |
| U-17 | No retention strategy exists |
| U-18 | Saved UPF contains `PSW_SW`, while synthesis reports confirm that Power Compiler inserted no physical switch cell |
| U-19 | Backend handoff is explicit: IC Compiler II or another implementation flow owns switch-cell selection, array insertion, and physical PG connection |

Every PLL/SRAM/IO macro PG row requires an explicit hierarchical `connect_supply_net`, not name inference. Their dedicated rails are additional supply associations within `PD_AO`, not domain boundaries. Power-switch intent is checked separately and must have no hard-macro or hierarchical-PG implementation in the synthesis inputs. Evidence basis: *Power Compiler User Guide*, U-2022.12-SP3, p. 227 for domain/multiple-supply concepts, p. 268 for numbered `extra_supplies_#`, p. 258 for hierarchical macro PG binding, and pp. 358–359 for a virtual/generic `create_power_switch` object that Power Compiler does not insert and passes to IC Compiler II.

## Crossing checks

| ID | Crossing | Required evidence |
|---|---|---|
| L-01 | `PD_AO` request/control to `u_sw_core` | 1.8-to-1.2 high-to-low LS strategy covers intended inputs |
| L-02 | `u_sw_core` response to `u_aon_ctrl` | Clamp-0 isolation, active when `sw_iso_n=0`; dual-rail ELS located at the `PD_SW` boundary and high-side powered by `VDD_AO` |
| L-03 | `u_sw_core` response to `u_aon_ctrl` | 1.2-to-1.8 low-to-high LS covers eight data bits plus valid |
| L-04 | Input-pad core path | 3.3 V/1.8 V supply attributes plus analog exemption; no core LS and no additional domain |
| L-05 | Output-pad core path | 1.8 V/3.3 V supply attributes plus analog exemption; no core LS and no additional domain |
| L-06 | Power controls | `sw_en` and `sw_iso_n` originate in `u_aon_ctrl` and remain always-on powered |
| L-07 | Clock handling | `sw_clk` is related to `SS_VDD_SW_VSS`; `pll_clk_mon_o` has no sequential endpoint |

The expected protected switchable response width is nine bits. Reset crossing is shifted; `sw_clk` enters directly at 1.2 V. Generated voltage-map teaching libraries exercise insertion only and are not recharacterized timing/power evidence.

## Compile-time behavioral checks

- Reset disables switchable power, asserts isolation, and clears responses.
- Power-up asserts `sw_en`, waits two complete edges, then releases `sw_iso_n`.
- Power-down asserts isolation one edge before clearing `sw_en`.
- `u_sw_core` performs eight-bit plus-one and loses state on behavioral power loss.
- The SRAM is 16 x 8, single-port, and always-on.
- PLL lock delay is four reference edges and its clock output drives no sequential logic.
- Pad RTL stubs are bounded signal-only pass-through models; their synthesis-only PG interfaces come from the Liberty macro views.
- No switch macro module or instance is permitted in RTL; `sw_en` remains a normal always-on control referenced by the UPF rule.

These receive no functional PASS until a future authorized registered simulation run.

## Future coverage goals

If simulation is later authorized, cover legal power-up, request/response including `8'hff` wraparound, isolation-before-off, state loss/recovery, every SRAM address with read/write, PLL enable/disable and lock delay, and both pad values. Assertions should flag power removal before isolation, traffic before ready, response visibility while isolated, and any PLL-clocked sequential endpoint. These goals do not close or skip `verif` now.

## Pass/fail criteria

The doc stage passes only when all four canonical documents pass completeness and the stale-term scan is empty. Later low-power structural PASS requires exactly the two documented domains, the three numbered `PD_AO` macro supplies, all eight PLL/SRAM/IO hierarchical PG bindings, abstract `PSW_SW`, no switch-cell implementation in RTL or synthesis, and isolation and LS strategies in real tool reports.

An extra domain, wrong membership, missing numbered macro supply, `UPF-707a`, unresolved or multiply connected PLL/SRAM/IO PG pin, missing or incomplete `PSW_SW`, any pre-instantiated/mapped switch cell or hierarchical switch PG connection, wrong isolation polarity/location, missing protected bit, silent unsupported LS claim, or PLL clock used sequentially is failure. Omission of unloaded switch supplies from the PG Verilog netlist is not a failure when the saved UPF retains the complete abstract rule. Tool/license absence is NOT RUN or failure, never synthetic PASS. No result is foundry, PVT, electrical, physical, reliability, or tapeout signoff.
