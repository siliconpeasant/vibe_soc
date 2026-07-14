# upf_dc_demo

Teaching-only Synopsys DC/Power Compiler UPF demo with exactly two domains:

- `PD_AO` uses `VDD_AO` at 1.8 V and contains `u_aon_ctrl`, `u_pll_macro`, `u_sram_macro`, `u_pad_in`, and `u_pad_out`.
- `PD_SW` uses switched `VDD_SW` at 1.2 V and contains only `u_sw_core`.

PLL, SRAM, and IO rails are associated to `PD_AO` as numbered additional supplies: `VDD_PLL` 1.8 V, `VDD_MEM` 1.8 V, and `VDDIO` 3.3 V. Functional RTL and behavioral macro models contain no PG ports. Their synthesis blackbox Liberty views provide `pg_pin` objects bound by explicit hierarchical `connect_supply_net`. All grounds use `VSS`. These behavioral models and the Sky130 HD teaching DB are not foundry IP or signoff evidence.

The executable low-power experiment inserts clamp-0 isolation on `PD_SW` outputs and level shifting in both AO/SW directions. The SW-to-AO isolation and low-to-high strategies share a dual-rail enable-level-shifter cell placed inside `PD_SW`: its low-side rail is `VDD_SW`, while its high-side output/control rail is always-on `VDD_AO`. IO voltage intent is represented with port supply attributes inside `PD_AO`; the hard pad macro, powered by `VDDIO/VSS`, owns the 1.8/3.3 V conversion, so no core standard-cell LS is inserted at the analog-exempt pad boundary.

## Reproduce power intent

The workbook is rebuilt from the project-local `upf-gen` filled template, then strict generation and deterministic post-processing are run:

```bash
PYTHON=${SILICON_CREW_PYTHON:-python3}
PROJECT_ROOT=${PROJECT_ROOT:-$(cd ../../.. && pwd -P)}
UPF_GEN=$PROJECT_ROOT/.agents/skills/upf-gen/scripts/generate_upf.py
env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp \
  "$PYTHON" de/syn/build_power_intent.py
env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp \
  "$PYTHON" "$UPF_GEN" \
  --input de/syn/power_intent.xlsx --out-dir de/syn/upf \
  --basename upf_dc_demo --strict
env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp \
  "$PYTHON" de/syn/postprocess_generated_upf.py
```

`de/syn/power_intent.xlsx` and everything under `de/syn/upf/` are local generated artifacts and are intentionally not committed. Install `upf-gen` project-locally before running these commands.

`postprocess_generated_upf.py` supplies only schema gaps: numbered additional supplies, macro PG bindings, AO-to-SW LS, IO supply attributes, teaching-cell mappings, and diagram membership annotations. It asserts required tokens and rejects extra domains or retention.

DC loads the complete canonical `upf_dc_demo.upf` after linking PG-aware macro Liberty views. No RTL-PG reconciliation or `convert_pg` step is needed. `write_file -pg` emits the PG-aware netlist and `save_upf -full_upf` writes `upf_dc_demo_synth.upf`.

## Tool flow

Agents use registered `soc_lint`, `soc_comp`, and `soc_syn` tools only. `dc_upf_synth.tcl` rejects UPF load errors, links synthesis-only macro PG pins before `load_upf`, preserves only the four approved macro blackboxes, checks exactly two domains, requires resolved macro PG paths, requires mapped AO/SW isolation and LS cells, rejects unmapped digital GTECH/SEQGEN content, and emits real reports/netlist/saved UPF.

No `soc_sim` run is part of this demo. The PLL output is observation-only and never clocks sequential RTL. There is no retention, bus, address map, physical switch-cell claim, analog electrical model, or tapeout claim.
