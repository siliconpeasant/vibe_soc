# Reset ownership (mandatory)

Approved 2026-08-13. This split is project-wide and is not optional per module.

## Split

| Owner | Owns | Must not own |
|---|---|---|
| **CRG** (`crg-gen`) | Clock sources, dividers, ICG, and **combinational** reset-source combine (`por` / `test_rst` / optional soft or extra sources) | Async-assert / **sync-release** flops or `rst_synchronizer` |
| **IP integration** (`soc-integrate` chip/subsystem top) | One `rst_synchronizer` (`STAGES=2`) **per clock domain** on the **gated** domain clock | Reset-source trees, clock dividers, ICG |
| **Leaf IP** | Consumes the **synced** domain reset as async-assert / sync-released `rst_*_n` | Reset synchronizers, CRG clock/reset trees |

## Required behavior

1. CRG `rst_gen` domain outputs use `SYNC=N` (or empty, which means N). Emitted RTL is `assign rst_<dom>_ni = <sources>;` only.
2. Integrator inserts `rst_synchronizer` between CRG async `rst_<dom>_ni` and every IP/CDC/fabric pin of that domain. Shared domains share one synchronizer.
3. Release clock is the CRG **gated** output (`clk_aon` / `clk_pdm` / …), not the pad. A stopped domain clock must not release that domain's synced reset.
4. Leaf IP must not grow its own reset synchronizer unless a reviewed exception names the IP and the reason.
5. Do not hand-write CRG reset trees. Do not move sync-release back into generated CRG to “simplify” the top.

## Names

- CRG output: `rst_<dom>_ni` — asynchronous, combinational.
- After integrate sync: `rst_<dom>_sync_ni` — what IP instances connect to.

## Evidence

Workbook `rst_gen` shows `SYNC=N`. CRG RTL has no `rst_synchronizer` / reset `always @(posedge`. Top/glue has one `rst_synchronizer` per domain.
