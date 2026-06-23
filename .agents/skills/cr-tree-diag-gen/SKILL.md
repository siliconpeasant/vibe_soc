---
name: cr-tree-diag-gen
description: Convert reviewed clock/reset Excel design tables into Draw.io and Excalidraw topology diagrams. Use for CRG source, mux, divider, OCC, ICG, and reset-chain visualization.
---

# Clock/Reset Tree Diagram Generator

Use one of the registered tools:

- `cr_tree_diag_gen`: generate both formats
- `cr_tree_diag_gen_drawio`: Draw.io only
- `cr_tree_diag_gen_excalidraw`: Excalidraw only

The default output is `<input-stem>_diagram/` beside the input; plugin example directories are read-only reference assets.

Clock columns include `NAME`, `ATTR`, `SRC0`, optional `SRC1`, `MUX_DFLT`, `DIV*`, `OCC`, `ICG*`, and `NOTE`. Reset tables are detected by `SOFT_DFLT` and may use `SRC0..SRC3`.

The generator validates graph structure, lays out hierarchy, and colors root-source paths. Review reported graph warnings, especially missing sources, cycles, and disconnected nodes, before accepting the diagram.
