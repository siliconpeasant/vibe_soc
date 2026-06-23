# clk_divider Design Spec

## Overview

`clk_divider` is a programmable clock divider in `de/rtl/clk_gen/clk_divider.v`. It accepts a source clock `clk`, an active-low asynchronous reset `rst_n`, and a synchronous divider setting `div_ratio[DIV_WIDTH-1:0]`. The output `clk_out` is driven according to the programmed ratio:

- `div_ratio = 0`: force `clk_out` low.
- `div_ratio = 1`: pass through `clk` to `clk_out`.
- `div_ratio >= 2`: generate a divided clock whose period is `div_ratio` input-clock cycles.

The module supports even and odd divide ratios. Internal divider state is reset when `rst_n` is asserted or when the sampled divider ratio changes.

## Functional Behavior

### Reset

`rst_n` is an asynchronous, active-low reset. When `rst_n = 0`, all internal state is cleared and `clk_out` is forced low. After `rst_n` deasserts, the module samples `div_ratio` in the `clk` domain and starts from a known low output phase.

### Divider Ratio Handling

`div_ratio` is treated as a synchronous input in the `clk` domain. The implementation shall sample the ratio before using it for counter control and shall detect changes relative to the previously sampled value.

When the sampled ratio changes:

- positive-edge and negative-edge divider counters are cleared;
- internal generated clock phases are cleared to `0`;
- the next divided sequence starts from a low output phase using the new ratio.

### Ratio 0

When the sampled `div_ratio` is `0`, `clk_out` shall be held at `0`. Counters and generated internal phases shall remain cleared while this mode is active.

### Ratio 1

When the sampled `div_ratio` is `1`, `clk_out` shall follow `clk` directly. The divided-clock counters shall remain cleared while this mode is active. This mode intentionally behaves as a clock bypass rather than a registered copy.

### Even Ratio Division

For even `div_ratio >= 2`, `clk_out` shall toggle every `div_ratio / 2` input-clock cycles. The resulting output period is `div_ratio` input-clock cycles with a 50% duty cycle, subject to normal clock-to-output and combinational delay through the implementation.

Examples:

| `div_ratio` | Output behavior |
|---|---|
| `2` | Toggle every 1 `clk` cycle, divide-by-2 |
| `4` | Toggle every 2 `clk` cycles, divide-by-4 |
| `8` | Toggle every 4 `clk` cycles, divide-by-8 |

### Odd Ratio Division

For odd `div_ratio >= 3`, the divider shall generate a period of `div_ratio` input-clock cycles while balancing duty cycle at half-cycle resolution. The implementation may use both `posedge clk` and `negedge clk` generated phases and combine them to form `clk_out`.

For odd ratios, output transitions may align to both input-clock rising and falling edges. The intended duty cycle is balanced to within one half input-clock cycle, giving equal high and low duration over a full output period when both-edge phase generation is used.

Examples:

| `div_ratio` | Output behavior |
|---|---|
| `3` | Divide-by-3 with high and low durations balanced at half-cycle resolution |
| `5` | Divide-by-5 with high and low durations balanced at half-cycle resolution |
| `7` | Divide-by-7 with high and low durations balanced at half-cycle resolution |

## State and Sequence

The module has no externally visible FSM. Its internal state consists of:

- the sampled divider ratio;
- a previous sampled ratio for change detection;
- a positive-edge counter and generated positive-edge phase;
- a negative-edge counter and generated negative-edge phase for odd-ratio support.

Operating sequence:

1. Reset assertion clears all internal state and drives `clk_out = 0`.
2. Reset release allows `div_ratio` sampling in the `clk` domain.
3. Ratio `0` keeps output low and counters cleared.
4. Ratio `1` bypasses `clk` to `clk_out` and counters remain cleared.
5. Ratio `>= 2` starts counting from zero and toggles internal phase at the programmed half-period points.
6. Any sampled ratio change clears counters and phases, then restarts from the new ratio.

## Error Behavior

There is no bus protocol, no register access path, and no error response output.

Unsupported or exceptional input values are handled as defined operating modes:

- `div_ratio = 0` is a legal force-low mode.
- `div_ratio = 1` is a legal bypass mode.
- all nonzero values represent unsigned divider ratios.

If `div_ratio` changes frequently, the divider is allowed to repeatedly restart and hold or return `clk_out` low during restart cycles. The module does not debounce, qualify, or handshake `div_ratio`.

## Assumptions

- `div_ratio` is synchronous to `clk` and meets setup and hold requirements at the module input.
- `DIV_WIDTH` is at least 1.
- The sink clocking architecture accepts `clk_out` as a generated clock. For odd ratios, sinks must tolerate transitions derived from both source-clock edges.
- Clock gating, generated-clock declaration, and clock-tree implementation are handled by integration and physical-design constraints outside this RTL block.

## Synthesis Constraints

- The RTL shall remain synthesizable Verilog and shall avoid unsynthesizable delays, force/release constructs, or simulation-only clock generation.
- `clk_out` is a generated clock output and should be constrained as such in synthesis and STA.
- `rst_n` to asynchronous reset pins should be treated as an asynchronous reset path.
- Generated-clock constraints should cover divide-by-1 passthrough and divided modes used by integration.
- Internal divider counters and phase flops should not be retimed across ratio-change clear behavior if that would alter restart phase or divide period.
