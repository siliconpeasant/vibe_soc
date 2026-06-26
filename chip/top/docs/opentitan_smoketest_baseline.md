# OpenTitan UART Smoke Baseline

## Purpose

`chip_sw_uart_smoketest` is the first OpenTitan vendor-island baseline wired into `chip/top`.
It reuses a known-good upstream OpenTitan VCS run instead of the incomplete hand-written source
ordering used by the bootstrap bring-up attempt.

## Source Run

The baseline was captured from:

```text
/project/xuanwu9000/user/silicon/opentitan-master/scratch/master/chip_earlgrey_asic-sim-vcs/0.chip_sw_uart_smoketest/latest/run.log
```

The upstream log ended with `SW TEST PASSED`, `TEST PASSED CHECKS`, and zero UVM errors/fatals.

## Imported Collateral

Reusable generated inputs were promoted into canonical vibe_soc roots:

```text
chip/top/de/rtl/filelist.opentitan.f
chip/top/de/rtl/generated/opentitan_fusesoc/
chip/top/dv/tb/sw/common/otp/
chip/top/dv/tb/sw/common/test_rom/
chip/top/dv/tb/sw/cases/chip_sw_uart_smoketest/
chip/top/dv/tb/tests/chip_sw_uart_smoketest.yml
```

The copied collateral includes:

- static OpenTitan compile order in `de/rtl/filelist.opentitan.f`
- the small set of FuseSoC-generated SV sources needed outside the vendor tree
- prebuilt `test_rom_sim_dv` ROM images
- prebuilt `uart_smoketest_sim_dv` flash images
- generated OTP images used by the OpenTitan DV environment
- per-directory manifests with file hashes and rebuild triggers

The original `simv`, `simv.daidir`, FSDB waveforms, and runtime database files were not imported as stable inputs.

## vibe_soc Integration

`chip/top/Makefile` selects the OpenTitan vendor path when `TEST=chip_sw_uart_smoketest`.
For this case it:

- uses `chip/top/de/rtl/filelist.opentitan.f`
- uses a static project-owned expansion of the verified FuseSoC dependency order
- overrides VCS to the OpenTitan-style one-step build because the filelist includes C/C++ DPI files
- runs `chip_base_test` with `chip_sw_uart_smoke_vseq`
- points `+sw_images` at `dv/tb/sw/common/test_rom` and `dv/tb/sw/cases/chip_sw_uart_smoketest`
- copies OTP images and SW logger databases from `dv/tb/sw` into the case run directory before launching `simv`

Run through the registered project workflow:

```text
soc_sim module_dir=/project/xuanwu9000/user/silicon/vibe_soc/chip/top/dv simulator=vcs top_module=tb test=chip_sw_uart_smoketest seed=1
```

## Local Result

The baseline now compiles and runs inside `vibe_soc` with the registered MCP simulation flow.
The passing local run was launched through `soc-build.soc_sim`.

Observed result in `chip/top/dv/sim/chip_sw_uart_smoketest/sim.log`:

```text
==== SW TEST PASSED ====
TEST PASSED CHECKS
UVM_ERROR :    0
UVM_FATAL :    0
```

Local host compatibility adjustments are kept in `chip/top/Makefile`:

- C++ DPI compile uses `-std=c++11` because the local `/usr/bin/g++` is GCC 4.8.5.
- OpenSSL AEAD control aliases are defined through `-CFLAGS` for the host OpenSSL headers.
- `libelf` links through `/usr/lib64/libelf.so.1` because the development `libelf.so` symlink is not installed.
- SW logger database files are copied into `dv/sim` before runtime so the logger can resolve the generated `.logs.txt` files.

## Default Top and Waves

`chip/top` now defaults to the OpenTitan vendor path for bring-up. If `TEST` is not specified,
`chip/top/Makefile` selects `chip_sw_uart_smoketest`, the passing FuseSoC-generated baseline.
Use `OT_DEFAULT_TOP=0` to return to the original generated `vibe_soc_top` flow.

For OpenTitan vendor simulations, `FSDB` defaults to `1`, and `WAVES=fsdb` is passed into the
OpenTitan runtime TCL. The expected waveform output is:

```text
chip/top/dv/sim/chip_sw_uart_smoketest/waves.fsdb
```

## FSDB Run Result

The FSDB-enabled smoke run was launched through `soc-build.soc_sim`. The MCP wrapper timed out after
300 seconds, but the underlying VCS process completed and wrote the final result to `dv/sim/chip_sw_uart_smoketest/sim.log`.

Observed artifacts and result:

```text
chip/top/dv/sim/chip_sw_uart_smoketest/waves.fsdb
==== SW TEST PASSED ====
TEST PASSED CHECKS
UVM_ERROR :    0
UVM_FATAL :    0
```

The generated FSDB is a full `tb:0` dump produced by the OpenTitan runtime TCL with `WAVES=fsdb`.

