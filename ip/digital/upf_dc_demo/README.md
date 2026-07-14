# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler UPF demo with exactly two domains:

- `PD_AO` uses `VDD_AO` at 1.8 V and contains `u_aon_ctrl`, `u_pll_macro`, `u_sram_macro`, `u_pad_in`, `u_pad_out`, and `u_power_switch_macro`.
- `PD_SW` uses switched `VDD_SW` at 1.2 V and contains only `u_sw_core`.

PLL, SRAM, IO, and switch-macro rails are associated to `PD_AO` as numbered additional supplies: `VDD_PLL` 1.8 V, `VDD_MEM` 1.8 V, `VDDIO` 3.3 V, `VDD_SW_IN` 1.2 V, and `VDD_SW` 1.2 V. The last two make the boundary macro legal in `PD_AO`; `VDD_SW` remains `PD_SW.primary`. Functional RTL and behavioral macro models contain no PG ports. Their synthesis blackbox Liberty views provide `pg_pin` objects bound by explicit hierarchical `connect_supply_net`. All grounds use `VSS`. These behavioral models and the Sky130 HD teaching DB are not foundry IP or signoff evidence.

Power Compiler does not instantiate a cell for abstract UPF switch `PSW_SW`, and it omits supply ports that feed no leaf PG pin. The top therefore pre-instantiates signal-only `u_power_switch_macro` with only `en_i` in RTL. Its linked Liberty view adds `VIN`, `VOUT`, and `VSS`; UPF binds them to `VDD_SW_IN`, `VDD_SW`, and `VSS`. This retains the complete switch rail connection in `write_file -pg` while `PSW_SW` remains the authoritative power behavior.

The executable low-power experiment inserts clamp-0 isolation on `PD_SW` outputs and level shifting in both AO/SW directions. The SW-to-AO isolation and low-to-high strategies share a dual-rail enable-level-shifter cell placed inside `PD_SW`: its low-side rail is `VDD_SW`, while its high-side output/control rail is always-on `VDD_AO`. IO voltage intent is represented with port supply attributes inside `PD_AO`; the hard pad macro, powered by `VDDIO/VSS`, owns the 1.8/3.3 V conversion, so no core standard-cell LS is inserted at the analog-exempt pad boundary.

## Reproduce power intent

`de/syn/power_intent.xlsx` is the single power-intent source. Start it from the project-local `upf-gen` template and edit the workbook directly; changing the design does not require generating or modifying a Python overlay. The current case uses:

- `Supplies`, `Domains`, `PowerStates`, `Isolation_LS`, and `Control` for the two domains, all six rails, both LS directions, isolation, and hierarchical controls.
- `DomainSupplies` for `PD_AO.extra_supplies_1` through `extra_supplies_5`.
- `HardMacros` and `MacroPG` for macro model attributes, diagram membership, and all eleven explicit PG-pin bindings.
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

DC loads the complete canonical `upf_dc_demo.upf` after linking PG-aware macro Liberty views. No RTL-PG reconciliation or `convert_pg` step is needed. `write_file -pg` must emit `VDD_SW_IN`, `u_power_switch_macro.VIN(VDD_SW_IN)`, and `VOUT(VDD_SW)`; `save_upf -full_upf` must retain abstract `PSW_SW`.

## Tool flow

Agents use registered `soc_lint`, `soc_comp`, and `soc_syn` tools only. `dc_upf_synth.tcl` rejects UPF load errors, links synthesis-only macro PG pins before `load_upf`, preserves only the five approved macro blackboxes, checks exactly two domains, requires resolved macro PG paths including both switch rails, requires mapped AO/SW isolation and LS cells, rejects unmapped digital GTECH/SEQGEN content, and emits real reports/netlist/saved UPF.

No `soc_sim` run is part of this demo. The PLL output is observation-only and never clocks sequential RTL. There is no retention, bus, address map, characterized physical switch-cell claim, analog electrical model, or tapeout claim.
