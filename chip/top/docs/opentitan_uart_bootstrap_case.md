# OpenTitan UART Bootstrap Case

## Test

- OpenTitan test name: `chip_sw_uart_tx_rx_bootstrap`
- OpenTitan config: `hw/top_earlgrey/dv/chip_sim_cfg.hjson`
- UVM sequence: `chip_sw_uart_tx_rx_vseq`
- Software image: `//sw/device/tests:uart_tx_rx_test:1:new_rules`
- Run mode: `sw_test_mode_test_rom`

## Required Plusargs

The OpenTitan configuration uses these relevant run options:

```text
+use_spi_load_bootstrap=1
+calibrate_usb_clk=1
+test_timeout_ns=160_000_000
```

In VCS command form the simulation should receive:

```text
+UVM_TESTNAME=chip_base_test
+UVM_TEST_SEQ=chip_sw_uart_tx_rx_vseq
+use_spi_load_bootstrap=1
+calibrate_usb_clk=1
+sw_test_timeout_ns=160_000_000
```

The exact plusarg spelling may be adjusted after the OpenTitan `chip_base_test` argument handling is
confirmed in the migrated tree.

## Expected Dependency Closure

The case is a full-chip bootstrap test, not a standalone UART IP test. The first migrated run is
expected to require:

- `chip_earlgrey_asic` and `top_earlgrey` generated RTL
- UART, SPI device, flash controller, flash memory model, TL-UL, reset, clock, pinmux, and primitive
  dependencies
- chip UVM environment, `chip_sw_uart_tx_rx_vseq`, UART agent, SPI agent, SW logger/status utilities,
  and chip RAL packages
- a generated or prebuilt `uart_tx_rx_test` software image
- VCS/UVM support and any required OpenTitan DPI libraries

## First Run Success Criteria

The first migration step is successful when `soc-build.soc_sim` can invoke the OpenTitan bootstrap
simulation entry from `chip/top` and produce a real `dv/sim/sim.log`. A compile or runtime failure is
acceptable only if the log identifies the next missing OpenTitan dependency to wire in.
