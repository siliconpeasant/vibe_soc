# OpenTitan UART Bootstrap Bring-up Log

## Command Used

The bootstrap case was run through the registered `soc-build.soc_sim` tool with:

```text
module_dir=/project/xuanwu9000/user/silicon/vibe_soc/chip/top
simulator=vcs
top_module=tb
test=chip_sw_uart_tx_rx_bootstrap
seed=1
```

The MCP tool invoked:

```text
make comp sim SIMULATOR=vcs SEED=1 TEST=chip_sw_uart_tx_rx_bootstrap TOP_MODULE=tb
```

## Bootstrap Historical Result

The run does not pass yet. It reaches VCS compile and fails during SystemVerilog package analysis.
The latest observed failure is:

```text
dv_base_reg_pkg requires prim_mubi_pkg before dv_base_reg_pkg is analyzed
```

Earlier dependency fixes already made in `de/rtl/filelist.f`:

- Added explicit VCS UVM package source before OpenTitan UVM code
- Moved `top_pkg` before `bus_params_pkg`
- Moved `str_utils_pkg` before `dv_utils_pkg`
- Moved `dv_test_status_pkg` before `dv_utils_pkg`
- Moved `dv_base_reg_pkg` before `csr_utils_pkg`
- Excluded `top_darjeeling` from the Earlgrey filelist

## Historical Diagnosis

The original issue was not a single missing RTL file. OpenTitan chip simulation depends on the
ordered dependency graph encoded in FuseSoC `.core` files and dvsim configuration. That order is
now captured as the canonical `de/rtl/filelist.f`.

## Filelist Next Step (Completed for Smoke Baseline)

This was the required filelist-ordering action before the smoke baseline could be declared done:

1. Install/use FuseSoC and generate the official `lowrisc:dv:top_earlgrey_chip_sim:0.1` VCS filelist,
   then adapt that output into `de/rtl/filelist.f`.
2. Write a local `.core` dependency expander for the imported OpenTitan tree that emits an ordered
   VCS filelist for `top_earlgrey_chip_sim`.

For the bootstrap case, the next expected blocker remains the missing
`uart_tx_rx_test_sim_dv.64.scr.vmem` software image for `+sw_images=uart_tx_rx_test:1:new_rules`.

## Smoke Baseline Added

A known-good upstream OpenTitan case, `chip_sw_uart_smoketest`, has been added as the first
vendor-island baseline. Its static filelist is maintained under `de/rtl`, while reusable SW/OTP
collateral is maintained under `dv/tb/sw`, and `chip/top/Makefile` now uses an OpenTitan-style
one-step VCS build for this case.

This does not yet close `chip_sw_uart_tx_rx_bootstrap`; it gives the migration a passing reference
case before extending the flow to bootstrap-specific SW images and sequences.

## Local Smoke Reproduction

`chip_sw_uart_smoketest` has now been reproduced inside `vibe_soc` using the registered MCP-launched VCS flow. The run builds a local `chip/top/dv/sim/chip_sw_uart_smoketest/simv`, loads the copied ROM/flash/OTP collateral from `dv/tb/sw`, and ends with `SW TEST PASSED`, `TEST PASSED CHECKS`, and zero UVM errors/fatals.

This confirms that the vendor-island OpenTitan structure, FuseSoC-generated file ordering, and vibe_soc Makefile handoff are viable. The bootstrap case should now reuse this known-good path instead of continuing from the hand-written unordered filelist.

## Static FuseSoC Filelist Captured

`de/rtl/filelist.f` has been replaced with a static expansion of the known-good
FuseSoC-generated `top_earlgrey_chip_sim` order.

The filelist no longer delegates through `-f ...fusesoc-work/...scr`; it directly lists the
expanded compile options and source files from checked-in RTL roots:

- `$SOC/chip/top/de/rtl/vendor/opentitan/...` for OpenTitan vendor RTL/DV sources.
- `$SOC/chip/top/de/rtl/generated/opentitan_fusesoc/...` for the small set of FuseSoC-generated sources that do not have an exact vendor-tree counterpart.

Software image collateral such as ROM, flash, OTP VMEMs, and SW log databases is now maintained
under `dv/tb/sw`; `de/run/` remains a transient build/cache root and is not used as a stable RTL
or SW input root.

Validation after this change:

- `soc_comp` on `chip/top/de`, top `chip_earlgrey_asic`: passed; generated `de/run/rtl.f` with 859 unique entries.
- `soc_comp` on `chip/top/dv`, top `tb`: passed; generated `dv/sim/chip_sw_uart_smoketest/dut.canonical.f` with 860 unique entries.
- `soc_sim` on `chip/top/dv`, test `chip_sw_uart_smoketest`, seed `1`: completed with `SW TEST PASSED`, `TEST PASSED CHECKS`, `UVM_ERROR: 0`, and `UVM_FATAL: 0`.

Bootstrap is still a separate bring-up item because its software image and sequence settings differ from the smoke baseline.

