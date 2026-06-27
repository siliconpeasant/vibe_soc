# OpenTitan Common DE Package

`opentitan_common` owns the shared OpenTitan primitive RTL slices that have been split out of the `chip/top` vendor island into a native vibe_soc package boundary.

## Scope

- OpenTitan `prim` / `prim_generic` base filelist used before TLUL.
- Additional `prim` / `prim_generic` ordered fragments split from the frozen Earlgrey chip dependency graph.
- No independent DV environment yet; chip-level smoke remains the validation point.

## Filelist Layout

```text
de/rtl/filelist.f
  Base common primitive entries.

de/rtl/fragments/10_top00_prim_block1.f
  First prim/prim_generic block formerly embedded in chip/top 00 fragment.

de/rtl/fragments/20_top00_prim_block2.f
  Second prim/prim_generic block formerly embedded in chip/top 00 fragment.

de/rtl/fragments/30_top10_prim_block1.f
  prim/prim_generic block formerly embedded in chip/top 10 fragment.
```

`de/rtl/filelist.mk` exposes each fragment as a named variable. Standalone consumers may include the package normally; `chip/top` still inserts fragments at the original frozen source-order points.

## Integration Contract

This package still references the OpenTitan vendor source tree for shared primitive RTL. It is a filelist ownership split first, not a source-pruning step. The vendor copies remain the source of truth until each primitive block is explicitly promoted to copied native RTL.
