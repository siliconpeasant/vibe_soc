# crg_ss generate + compile notes

## Generation

- Source: `.agents/skills/crg-gen/references/crg_demo.xlsx`
- Tool: `crg-gen.crg_gen`
- Raw output: `de/run/crg_gen/`
- Wired RTL top: `demo_crg_top` in `de/rtl/`

## VCS compile smoke

```bash
# via MCP
soc_comp(module_dir=chip/crg_ss, simulator=vcs, top_module=demo_crg_top)
```

Result with generator-compatible stubs under `de/rtl/stubs/`: **PASS** (`dv/sim/simv` built).

## Issues found

1. **Missing library cells** (not in repo):  
   `ss_rst_sequence`, `xstar_por_sequence`, `pulse_sync_h2s`, `sync`, `icg`,  
   `clk_divider_wrap`, `clk_glitch_free_switch`, `clk_buf_for_occ`,  
   and generator-named `std_cell_clk_mux` / `rstn_test_mux` port maps.
2. **Port name mismatch vs `soc_ip_common`**:  
   generator uses `clk_in0/clk_in1/clk_sel` and `test_md/rstn_in/test_rstn/rstn_out`;  
   common cells use different names — cannot drop-in without wrappers.
3. **yml2reg integration broken for this flow**:  
   - top instantiates `DEMO_CRG_apb_reg`  
   - generator emits `DEMO_CRG_apb_regfile`  
   - APB port names differ (`clk/psel` vs `apb_clk/apb_sel`)  
   - functional port names differ (hierarchical prefixes)  
   - syntax: `output regname` missing space after `reg`  
   - port redeclarations in large regfile  
   → regfile **excluded** from filelist; stub used for compile only.
4. **Parameter overrides** (`D_WIDTH`, `DATA_DEFAULT`) warn on stubs (AOUP).

## Next fixes (priority)

1. Provide real CRG cell library matching generator port maps (or adapt generator to `soc_ip_common`).
2. Align yml2reg module/port naming with `crg_gen` top CSV/instance naming.
3. Replace stubs with real cells; re-enable regfile in filelist after yml2reg fix.
