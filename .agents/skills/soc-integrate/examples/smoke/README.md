# Filelist and smoke example

From the skill directory (use an output directory outside the checkout):

```bash
mkdir -p /tmp/soc-smoke
python3 scripts/soc_integrate.py integrate examples/smoke/counter.sv \
  -o /tmp/soc-smoke/top.sv --flist --smoke-tb
python3 scripts/soc_integrate.py smoke-tb /tmp/soc-smoke/top.sv --cycles 8 --run
```

The first command writes `top.f`, `top_smoke_tb.sv`, and `top_smoke_tb.f` and
prints a Verilator build/run command. The second actually builds/runs and prints
`PASS: top smoke (8 cycles)`. `enable_i` is tied low; `rst_ni` starts low and
releases after two cycles. This exercises wiring, initialization and scheduling.

For discovery, `flist top.sv --search-path rtl/` delegates scanning to the sibling
`soc-build` filelist generator. Packages precede consumers even when filenames
sort in the opposite order. Pass `--package`, `-I`, `-D`, and `-y` as needed.
