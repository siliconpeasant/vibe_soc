# OpenTitan TL-UL DE filelist package

Groups OpenTitan TL-UL RTL entries used by `chip/top` without moving or forking vendor source files. TL-UL has order-sensitive dependencies in Earlgrey, so `chip/top/de/rtl/filelist.f` includes ordered fragment filelists at the original dependency points instead of including the package as one monolithic filelist.

## Scope

- DE-only split package.
- Source files remain under `chip/top/de/rtl/vendor/opentitan`.
- Does not provide native RTL ownership yet.
- Does not provide independent DV yet.

## Files

```text
opentitan_tlul/
├── de/
│   ├── Makefile
│   └── rtl/
│       ├── filelist.f          # manifest only; not the chip/top include point
│       ├── filelist.mk
│       └── fragments/          # order-preserving chip/top include fragments
├── Makefile
└── README.md
```

## Integration

`chip/top/de/rtl/filelist.f` consumes the fragment filelists under `de/rtl/fragments/` with `-f` at the frozen OpenTitan dependency points.
