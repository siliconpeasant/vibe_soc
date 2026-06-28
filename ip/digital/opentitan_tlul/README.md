# opentitan_tlul

OpenTitan native ownership package for vibe_soc. This package currently owns the canonical filelist boundary for its OpenTitan block while RTL sources remain referenced from `chip/top/de/rtl/vendor/opentitan`. Physical source promotion is intentionally gated by the module doc/rtl/verif workflow.

Validation is chip-level first: compile `chip_earlgrey_asic` and run `chip_sw_uart_smoketest` after filelist ownership changes. Standalone DV can be added after the package interface document is approved.
