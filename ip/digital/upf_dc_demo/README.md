# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler UPF demo with exactly two domains:

- `PD_AO` uses `VDD_AO` at 1.8 V and contains `u_aon_ctrl`, `u_pll_macro`, `u_sram_macro`, `u_pad_in`, and `u_pad_out`.
- `PD_SW` uses switched `VDD_SW` at 1.2 V and contains only `u_sw_core`.

PLL, SRAM, and IO rails are associated with `PD_AO` as numbered additional supplies: `VDD_PLL` 1.8 V, `VDD_MEM` 1.8 V, and `VDDIO` 3.3 V. Their functional RTL models contain no PG ports; synthesis blackbox Liberty views provide `pg_pin` objects bound by explicit hierarchical `connect_supply_net`. `VDD_SW_IN` and `VDD_SW` remain UPF supply objects, with `VDD_SW` as `PD_SW.primary`, but neither is a switch-macro `PD_AO` extra supply. All grounds use `VSS`. These behavioral models and the Sky130 HD teaching DB are not foundry IP or signoff evidence.

The switch is backend-owned. UPF retains only abstract `create_power_switch PSW_SW` intent: input `VDD_SW_IN`, output `VDD_SW`, always-on control `u_aon_ctrl/sw_en_o`, and its ON condition. RTL and synthesis contain no switch macro or switch PG hookup, and the PG Verilog netlist is not required to retain unloaded switch-rail ports. This matches *Power Compiler User Guide*, U-2022.12-SP3, pp. 358–359: the command creates a virtual/generic switch that Power Compiler does not insert and passes to IC Compiler II for implementation.

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

DC loads the complete canonical `upf_dc_demo.upf` after linking the PLL/SRAM/IO PG-aware macro Liberty views. No RTL-PG reconciliation or `convert_pg` step is needed. `write_file -pg` is not required to emit `VDD_SW_IN`, a switch macro, or switch PG connections; `save_upf -full_upf` must retain abstract `PSW_SW` for backend handoff.

## Tool flow

Agents use registered `soc_lint`, `soc_comp`, and `soc_syn` tools only. `dc_upf_synth.tcl` must reject UPF load errors, link synthesis-only PLL/SRAM/IO PG pins before `load_upf`, preserve only those four approved macro blackboxes, check exactly two domains, require the eight resolved macro PG paths, require abstract `PSW_SW` without a synthesized switch cell, require mapped AO/SW isolation and LS cells, reject unmapped digital GTECH/SEQGEN content, and emit real reports/netlist/saved UPF.

No `soc_sim` run is part of this demo. The PLL output is observation-only and never clocks sequential RTL. There is no retention, bus, address map, characterized physical switch-cell claim, analog electrical model, or tapeout claim.
