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

## Current Result

The run does not pass yet. It reaches VCS compile and fails during SystemVerilog package analysis.
The latest observed failure is:

```text
dv_base_reg_pkg requires prim_mubi_pkg before dv_base_reg_pkg is analyzed
```

Earlier dependency fixes already made in `de/rtl/filelist.opentitan.f`:

- Added explicit VCS UVM package source before OpenTitan UVM code
- Moved `top_pkg` before `bus_params_pkg`
- Moved `str_utils_pkg` before `dv_utils_pkg`
- Moved `dv_test_status_pkg` before `dv_utils_pkg`
- Moved `dv_base_reg_pkg` before `csr_utils_pkg`
- Excluded `top_darjeeling` from the Earlgrey filelist

## Diagnosis

The remaining issue is not a single missing RTL file. OpenTitan chip simulation depends on the
ordered dependency graph encoded in FuseSoC `.core` files and dvsim configuration. The generated
`filelist.opentitan.f` is currently a first-pass vibe_soc filelist, not a complete topological
expansion of OpenTitan's core graph.

## Required Next Step

Add one of these before declaring the OpenTitan RTL stage done:

1. Install/use FuseSoC and generate the official `lowrisc:dv:top_earlgrey_chip_sim:0.1` VCS filelist,
   then adapt that output into `de/rtl/filelist.opentitan.f`.
2. Write a local `.core` dependency expander for the imported OpenTitan tree that emits an ordered
   VCS filelist for `top_earlgrey_chip_sim`.

After the filelist is topologically ordered, the next expected blocker is the missing
`uart_tx_rx_test_sim_dv.64.scr.vmem` software image for `+sw_images=uart_tx_rx_test:1:new_rules`.

## Smoke Baseline Added

A known-good upstream OpenTitan case, `chip_sw_uart_smoketest`, has been added as the first
vendor-island baseline. Its FuseSoC-generated filelist and prebuilt SW/OTP images were copied into
`de/run/opentitan_smoke/`, and `chip/top/Makefile` now uses an OpenTitan-style one-step VCS build
for this case.

This does not yet close `chip_sw_uart_tx_rx_bootstrap`; it gives the migration a passing reference
case before extending the flow to bootstrap-specific SW images and sequences.

## Local Smoke Reproduction

`chip_sw_uart_smoketest` has now been reproduced inside `vibe_soc` using the registered MCP-launched VCS flow. The run builds a local `chip/top/dv/sim/simv`, loads the copied ROM/flash/OTP collateral from `de/run/opentitan_smoke/`, and ends with `SW TEST PASSED`, `TEST PASSED CHECKS`, and zero UVM errors/fatals.

This confirms that the vendor-island OpenTitan structure, FuseSoC-generated file ordering, and vibe_soc Makefile handoff are viable. The bootstrap case should now reuse this known-good path instead of continuing from the hand-written unordered filelist.

