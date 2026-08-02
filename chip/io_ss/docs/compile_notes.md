# io_ss generate + compile notes

## Generation

- Source: `.agents/skills/io-top-gen/references/io_top_demo.xlsx`
- Tool: `io-top-gen.io_top_gen` (registered in this branch)
- Raw output: `de/run/io_top_gen/`
- Wired RTL top: `io_top_top` in `de/rtl/`
- SDC: `de/syn/io_top.sdc`

## VCS compile smoke

```bash
soc_comp(module_dir=chip/io_ss, simulator=vcs, top_module=io_top_top)
```

Result with pad-model stubs under `de/rtl/stubs/` + local patches: **PASS** (`dv/sim/simv` built).  
Still emits TFIPC (top does not connect all ring control ports such as `sl/msc/ps/he/pe`).

## Issues found

1. **Missing pad/library models**: `iobuf_model`, `iobuf_s_model`, `clkbuf_model`, `test_tdr_mux`, `std_cell_clk_buf`.
2. **Missing include**: `std_cell_def.h` (provided minimal empty header under `de/rtl/`).
3. **yml2reg integration broken** (same class as CRG):  
   top uses `IO_TOP_apb_reg` with hierarchical port names;  
   file is `IO_TOP_apb_regfile` with short names → stubbed out of filelist.
4. **Generator self-inconsistency**:  
   - `io_top_pin_mux.v` had **truncated ternary** assigns for func_sel paths (compile syntax error).  
     Patched locally for smoke.  
   - `io_top_top` connects `pad_*_pu/pd` while ring originally exposed `sl/msc/ps/he/pe` without `pu/pd`.  
     Ring header patched to accept `pu/pd` and wider `ds/st`.
5. **TFIPC**: ring still has extra control ports not driven by top.

## Next fixes (priority)

1. Fix `io_top_gen.py` ternary emission and top↔ring pad-control field consistency.
2. Align yml2reg naming with generator instance names/ports.
3. Supply real pad cell models from the process library.
4. Remove temporary pin_mux/ring patches once generator is fixed.
