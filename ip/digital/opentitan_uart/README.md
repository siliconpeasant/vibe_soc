# OpenTitan UART DE Package

`opentitan_uart` owns the OpenTitan UART RTL slice used by `chip/top` as a native vibe_soc DE package. The UART RTL files are copied under `ip/digital/opentitan_uart/de/rtl/`; the original OpenTitan vendor copy remains as migration source material for now.

## Scope

- Copied UART RTL: `uart.sv`, `uart_core.sv`, `uart_rx.sv`, `uart_tx.sv`, `uart_reg_pkg.sv`, `uart_reg_top.sv`.
- Exposes `OPENTITAN_UART_FILELIST` through `de/rtl/filelist.mk`.
- Standalone include mode automatically pulls in `opentitan_common` first.
- `chip/top` integration disables auto-registration and inserts UART at the frozen OpenTitan UART dependency point.
- No independent UART DV environment yet; chip-level smoke remains the validation point.

## Files

```text
opentitan_uart/
|-- de/
|   |-- Makefile
|   `-- rtl/
|       |-- *.sv
|       |-- filelist.f
|       `-- filelist.mk
|-- Makefile
`-- README.md
```

## Integration

`chip/top/de/rtl/filelist.mk` includes this package `filelist.mk`, sets `OPENTITAN_UART_NO_AUTO_REGISTER=1`, and inserts `OPENTITAN_UART_FILELIST` after the `60_after_tlul_debug_before_uart.f` top fragment. Standalone module use leaves auto-registration enabled, so common dependencies are collected before UART.
