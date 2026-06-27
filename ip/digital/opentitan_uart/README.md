# OpenTitan UART DE package

Owns the OpenTitan UART RTL slice used by `chip/top` and the UART smoke tests as a native vibe_soc DE package. The RTL files are copied under `ip/digital/opentitan_uart/de/rtl/`; the original vendor island copy is kept for now as migration source material until later pruning.

## Scope

- DE RTL split package.
- Owns copied UART `.sv` files under `de/rtl/`.
- Exposes `OPENTITAN_UART_FILELIST` through `de/rtl/filelist.mk`.
- Does not provide an independent DV environment yet.

## Files

```text
opentitan_uart/
├── de/
│   ├── Makefile
│   └── rtl/
│       ├── *.sv
│       ├── filelist.f
│       └── filelist.mk
├── Makefile
└── README.md
```

## Integration

`chip/top/de/rtl/filelist.mk` includes this package `filelist.mk`, disables auto-registration, and inserts `OPENTITAN_UART_FILELIST` at the frozen OpenTitan UART dependency point.
