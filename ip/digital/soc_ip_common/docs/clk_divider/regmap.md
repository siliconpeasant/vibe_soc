# clk_divider Register Map

## Register Map Status

Not applicable.

`clk_divider` has no memory-mapped register interface, no bus protocol, no address decode, and no readable or writable registers. The divider ratio is supplied directly through the synchronous input port `div_ratio[DIV_WIDTH-1:0]`.

## Control Fields

| Field | Location | Access | Description |
|---|---|---|---|
| `div_ratio` | input port | external synchronous input | Unsigned divider selection. `0` forces `clk_out` low, `1` bypasses `clk`, and values `>= 2` generate a divided clock. |

Any register-file ownership for driving `div_ratio` belongs to the integrating block and is outside the scope of this module.
