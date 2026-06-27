# OpenTitan UART DE filelist package

Groups the OpenTitan UART RTL entries used by chip/top and the UART smoke tests. Source files remain under chip/top/de/rtl/vendor/opentitan; this package owns only the vibe_soc DE filelist boundary.

## Scope

- DE-only split package.
- Does not move or fork OpenTitan RTL source files.
- Does not provide an independent DV environment yet.
- Consumed by `chip/top/de/rtl/filelist.f` through `-f $SOC/ip/digital/opentitan_uart/de/rtl/filelist.f`.

## Files

```text
opentitan_uart/
├── de/
│   ├── Makefile
│   └── rtl/
│       ├── filelist.f
│       └── filelist.mk
├── Makefile
└── README.md
```

## Next Step

When this boundary is stable, the package can be promoted from vendor filelist ownership to native RTL ownership by copying or rewriting the selected RTL into `de/rtl/` and adding its own focused `dv/tb/` tests.
