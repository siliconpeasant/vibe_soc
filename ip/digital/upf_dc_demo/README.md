# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler UPF demo with exactly two domains:

- `PD_AO` uses `VDD_AO` at 1.8 V and contains `u_aon_ctrl`, `u_pll_macro`, `u_sram_macro`, `u_pad_in`, and `u_pad_out`.
- `PD_SW` uses switched `VDD_SW` at 1.2 V and contains only `u_sw_core`.

PLL, SRAM, and IO rails are associated with `PD_AO` as numbered additional supplies: `VDD_PLL` 1.8 V, `VDD_MEM` 1.8 V, and `VDDIO` 3.3 V. Their functional RTL models contain no PG ports; synthesis blackbox Liberty views provide `pg_pin` objects bound by explicit hierarchical `connect_supply_net`. `VDD_SW_IN` and `VDD_SW` remain UPF supply objects, with `VDD_SW` as `PD_SW.primary`, but neither is a switch-macro `PD_AO` extra supply. All grounds use `VSS`. These behavioral models and the Sky130 HD teaching DB are not foundry IP or signoff evidence.

The switch is backend-owned. UPF retains only abstract `create_power_switch PSW_SW` intent: input `VDD_SW_IN`, output `VDD_SW`, always-on control `u_aon_ctrl/sw_en_o`, and its ON condition. RTL and synthesis contain no switch macro or switch PG hookup. This matches *Power Compiler User Guide*, U-2022.12-SP3, pp. 358–359: the command creates a virtual/generic switch that Power Compiler does not insert and passes to IC Compiler II for implementation.

The executable low-power experiment inserts clamp-0 isolation on `PD_SW` outputs and level shifting in both AO/SW directions. The SW-to-AO isolation and low-to-high strategies share a dual-rail enable-level-shifter cell placed inside `PD_SW`: its low-side rail is `VDD_SW`, while its high-side output/control rail is always-on `VDD_AO`. IO voltage intent is represented with port supply attributes inside `PD_AO`; the hard pad macro, powered by `VDDIO/VSS`, owns the 1.8/3.3 V conversion, so no core standard-cell LS is inserted at the analog-exempt pad boundary.

## Reproduce power intent

`de/syn/power_intent.xlsx` is the single power-intent source. Start it from the project-local `upf-gen` template and edit the workbook directly; changing the design does not require generating or modifying a Python overlay. The current case uses:

- `Supplies`, `Domains`, `PowerStates`, `Isolation_LS`, and `Control` for the two domains, all six rails, both LS directions, isolation, and hierarchical controls.
- `DomainSupplies` for `PD_AO.extra_supplies_1` through `extra_supplies_3`.
- `HardMacros` and `MacroPG` for PLL/SRAM/IO macro model attributes, diagram membership, and eight explicit PG-pin bindings; the power switch has no rows in either table.
- `PortAttributes` and `CellMaps` for IO/analog intent and the two teaching-cell mappings.

Generate the complete canonical UPF and diagrams in one strict invocation:

```bash
PYTHON=${SILICON_CREW_PYTHON:-python3}
PROJECT_ROOT=${PROJECT_ROOT:-$(cd ../../.. && pwd -P)}
UPF_GEN=$PROJECT_ROOT/.agents/skills/upf-gen/scripts/generate_upf.py
env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp \
  "$PYTHON" "$UPF_GEN" \
  --input de/syn/power_intent.xlsx --out-dir de/syn/upf \
  --basename upf_dc_demo --strict
```

The local workbook and everything under `de/syn/upf/` are intentionally not committed. Install the enhanced `upf-gen` project-locally and copy `assets/power_intent_filled.xlsx` to `de/syn/power_intent.xlsx` before filling a fresh case. There is no `build_power_intent.py` or `postprocess_generated_upf.py`; the workbook contains all required input information.

DC loads the complete canonical `upf_dc_demo.upf` after linking the PLL/SRAM/IO PG-aware macro Liberty views. That internal database is used for MV checks, all eight macro PG-path audits, isolation/level-shifter insertion, and `save_upf -full_upf` backend handoff.

The delivered `de/syn/upf_dc_demo_netlist.v` is deliberately ordinary non-PG Verilog, written without the `write_file -pg` option. It contains functional logic, four functional macro instances, nine inserted enable-level-shifter (ELS) isolation cells, and eleven pure high-to-low level shifters; the total level-shifter count is therefore twenty when ELS cells are included. It must contain no supply port/net and no PG-pin named connection, including `VDD*`, `VSS*`, `VDDIO`, `VSSIO`, `VGND`, `VPWR`, or `VPWRIN`. MacroPG remains authoritative in UPF and reports, not in the delivered Verilog.

## Tool flow

Agents use registered `soc_lint`, `soc_comp`, and `soc_syn` tools only. `dc_upf_synth.tcl` must reject UPF load errors, link synthesis-only PLL/SRAM/IO PG pins before `load_upf`, preserve only those four approved macro blackboxes, check exactly two domains, require the eight resolved macro PG paths, require abstract `PSW_SW` without a synthesized switch cell, require the documented 9 ELS + 11 pure LS structure, reject unmapped digital GTECH/SEQGEN content, write a non-PG netlist, and save the complete UPF.

Evidence basis: *Power Compiler User Guide*, U-2022.12-SP3, p. 416 states that `write_file -pg` produces complete PG supply connections; pp. 418–419 show PG pin/net emission and switch-supply behavior in that PG form. This demo intentionally omits `-pg` for its Verilog deliverable while retaining the separate full-UPF handoff.

No `soc_sim` run is part of this demo. The PLL output is observation-only and never clocks sequential RTL. There is no retention, bus, address map, characterized physical switch-cell claim, analog electrical model, or tapeout claim.
