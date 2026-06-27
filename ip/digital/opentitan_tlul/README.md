# OpenTitan TL-UL DE package

Owns the OpenTitan TL-UL RTL slice used by `chip/top` as a native vibe_soc DE package. The RTL files are copied under `ip/digital/opentitan_tlul/de/rtl/`; the original vendor island copy is kept for now as migration source material until later pruning.

TL-UL has order-sensitive dependencies in Earlgrey, so `chip/top/de/rtl/filelist.mk` consumes ordered TL-UL fragment variables from this package instead of including the package as one monolithic filelist.

## Scope

- DE RTL split package.
- Owns copied TL-UL `.sv` files under `de/rtl/`.
- Exposes ordered fragment filelists through `de/rtl/filelist.mk`.
- Does not provide independent DV yet.

## Files

```text
opentitan_tlul/
├── de/
│   ├── Makefile
│   └── rtl/
│       ├── *.sv
│       ├── filelist.f          # full package manifest
│       ├── filelist.mk         # exported fragment variables
│       └── fragments/          # order-preserving chip/top include fragments
├── Makefile
└── README.md
```

## Integration

`chip/top/de/rtl/filelist.mk` includes this package `filelist.mk`, disables auto-registration, and inserts the exported TL-UL fragments at the frozen OpenTitan dependency points.
