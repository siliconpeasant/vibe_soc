# OpenTitan Vendor Migration

## Objective

Import OpenTitan Earlgrey as the temporary `chip/top` implementation for vibe_soc while preserving
the OpenTitan source layout. The first migration step keeps the code as a vendor island so that
include paths, generated package names, and upstream diffs remain traceable. After the bootstrap
case runs through the vibe_soc flow, individual functions can be split into native vibe_soc modules.

## Source

- Source repository: `/project/xuanwu9000/user/silicon/opentitan-master`
- Imported OpenTitan root: `chip/top/de/rtl/vendor/opentitan`
- Imported source classes: `hw/`, `sw/`, `util/`, `third_party/`, top-level metadata/license files
- Excluded source classes: `.git/`, Bazel output/cache directories, `scratch/`, logs, waveform
  databases, and generated runtime artifacts

The OpenTitan repository measured about 15 GB on disk because local Bazel and scratch directories
dominate the checkout. The source-level import is expected to be hundreds of MB, not 15 GB.

## Integration Strategy

The import is intentionally staged:

1. Preserve the OpenTitan tree under `de/rtl/vendor/opentitan`.
2. Add vibe_soc-owned manifests and filelists beside the existing `vibe_soc_top` files.
3. Keep the current `vibe_soc_top` RTL intact until the OpenTitan chip simulation entry compiles.
4. Use `soc-build.soc_sim` for the first bootstrap simulation attempt.
5. Split OpenTitan functionality into native `chip/` and `ip/digital/` modules only after the
   vendor island has a known-good baseline.

## Native Split Candidates

The expected later split is:

- `chip/top`: final integration top and board-level strap policy
- `chip/periph`: OpenTitan-derived UART/SPI/flash bootstrap subsystem attachment
- `chip/bus`: TL-UL or bridge logic once the OpenTitan bus dependency is reduced
- `ip/digital/ot_spi_device`: SPI device and bootstrap ingress
- `ip/digital/ot_flash_ctrl`: flash controller and erase/program datapath
- `ip/digital/ot_flash_mem_model`: simulation flash memory and backdoor utilities
- `ip/digital/ot_prim_subset`: trimmed primitive cells needed by the selected subsystem

## Current Risks

- OpenTitan chip simulation is normally driven by dvsim/FuseSoC/Bazel, not by a flat filelist.
- `chip_sw_uart_tx_rx_bootstrap` needs a software image from `//sw/device/tests:uart_tx_rx_test`.
- The first compile may fail on missing DPI libraries, RAL packages, UVM package order, or generated
  filelist dependencies.
- A failure in the first `soc_sim` run is treated as real dependency discovery, not as a completed
  verification result.
