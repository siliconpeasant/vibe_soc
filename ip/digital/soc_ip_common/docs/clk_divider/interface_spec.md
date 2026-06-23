# clk_divider Interface Spec

## Module Identification

| Item | Value |
|---|---|
| Module | `clk_divider` |
| RTL path | `de/rtl/clk_gen/clk_divider.v` |
| Workspace | `ip/digital/soc_ip_common` |
| Language | Synthesizable Verilog |
| Function | Programmable generated-clock divider |

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `DIV_WIDTH` | integer | `8` | Width of `div_ratio` and internal divider counters. Supports unsigned ratios from `0` to `2**DIV_WIDTH - 1`. |

Parameter constraints:

- `DIV_WIDTH >= 1`.
- Integration should choose `DIV_WIDTH` large enough for the maximum required divider ratio.

## Ports

| Signal | Direction | Width | Description |
|---|---|---|---|
| `clk` | input | 1 | Source clock. Internal positive-edge state updates on `posedge clk`; odd-ratio support may also use `negedge clk` phase state. |
| `rst_n` | input | 1 | Active-low asynchronous reset. Assertion clears divider state and forces `clk_out` low. |
| `div_ratio` | input | `DIV_WIDTH` | Synchronous unsigned divider ratio. `0` forces low, `1` bypasses `clk`, values `>= 2` select divided-clock operation. |
| `clk_out` | output | 1 | Generated clock output. Low during reset and ratio-0 mode, passthrough in ratio-1 mode, divided output for ratios `>= 2`. |

## Clocks

| Clock | Source | Description |
|---|---|---|
| `clk` | input port | Source clock for divider sampling, ratio-change detection, and positive-edge counter state. |
| `clk_out` | output port | Generated clock derived from `clk`; divide factor is selected by sampled `div_ratio`. |

`clk_out` should be declared as a generated clock by integration constraints for the divide ratios used in a specific SoC configuration.

## Reset

| Reset | Polarity | Type | Affected state |
|---|---|---|---|
| `rst_n` | active low | asynchronous assert | Ratio sample registers, change-detection state, counters, and generated phase flops |

Reset assertion forces `clk_out = 0`. Reset deassertion is observed by the internal sequential logic on subsequent `clk` edges.

## Timing

- `div_ratio` is synchronous to `clk` and must meet setup and hold timing at the module boundary.
- A sampled ratio change restarts the divider sequence from a cleared low phase.
- In divide-by-1 mode, `clk_out` follows `clk` through combinational bypass logic.
- In even divided modes, `clk_out` transitions are aligned to `posedge clk`.
- In odd divided modes, `clk_out` transitions may be aligned to both `posedge clk` and `negedge clk` to support balanced duty cycle.
- `rst_n` assertion is asynchronous. Reset recovery and removal requirements apply to internal flops and are handled by STA/reset constraints.

## Integration Notes

- No bus, register interface, interrupt, or status output is present.
- `clk_out` is a clock output and should not be consumed as ordinary data without clock-domain planning.
- Downstream logic using `clk_out` needs generated-clock constraints and reset strategy consistent with the selected divider mode.
- Dynamic `div_ratio` changes are supported, but each change restarts the divider and may create a phase discontinuity. Firmware or control logic should change `div_ratio` only when the downstream clocking plan allows such a restart.
