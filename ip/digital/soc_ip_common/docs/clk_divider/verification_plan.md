# clk_divider Verification Plan

## Verification Scope

Verify that `clk_divider` implements the approved programmable clock-divider behavior for reset, force-low, bypass, even division, odd division, and dynamic ratio changes. The plan covers module-level simulation and assertions/checks suitable for the existing `soc_ip_common` verification flow.

## Test Matrix

| Test | Configuration | Stimulus | Expected result |
|---|---|---|---|
| Reset default | `DIV_WIDTH=8` | Assert and deassert `rst_n` with several `div_ratio` values | Internal state clears; `clk_out` is low while reset is asserted; divider restarts after reset release. |
| Ratio 0 force-low | `div_ratio=0` | Run for many `clk` cycles after reset | `clk_out` remains `0`; no divided pulses are produced. |
| Ratio 1 bypass | `div_ratio=1` | Run after reset release | `clk_out` follows `clk` with bypass behavior. |
| Divide-by-2 | `div_ratio=2` | Run for multiple output periods | `clk_out` toggles every 1 input cycle; output period is 2 input cycles. |
| Even ratios | `div_ratio=4, 6, 8` | Run for multiple output periods per ratio | Output period equals `div_ratio` input cycles; high and low durations each equal `div_ratio/2` input cycles. |
| Odd ratios | `div_ratio=3, 5, 7, 9` | Run for multiple output periods per ratio | Output period equals `div_ratio` input cycles; duty is balanced at half-cycle resolution using both-edge phase behavior. |
| Maximum ratio | `div_ratio=(2**DIV_WIDTH)-1` for a practical small `DIV_WIDTH` test instance | Run long enough for at least two output periods | Counters do not overflow early; output period matches programmed ratio. |
| Dynamic ratio change | Sweep between `0`, `1`, even, and odd ratios | Change `div_ratio` while running | Divider state restarts on each sampled ratio change; no stale period from old ratio continues after restart. |
| Reset during active divide | Even and odd active ratios | Assert `rst_n` mid-period and release | `clk_out` is forced low during reset and the divider restarts from low phase after reset release. |
| Parameter width | `DIV_WIDTH=1`, `DIV_WIDTH=4`, default `DIV_WIDTH=8` | Compile and run legal ratio values per width | Width-dependent counters and ratio decode operate without truncation-related failures. |

## Assertions and Checks

- Assert that `clk_out == 0` whenever `rst_n == 0`.
- Assert that sampled `div_ratio == 0` holds `clk_out == 0`.
- Check that divide-by-1 mode follows `clk`.
- For each even ratio `N >= 2`, check that output transitions occur every `N/2` input cycles and full output period is `N` input cycles.
- For each odd ratio `N >= 3`, check that full output period is `N` input cycles and that high/low duration differs by no more than one half input-clock cycle.
- On a sampled ratio change, check that the next divided sequence begins from cleared internal phase and does not complete a stale old-ratio period.
- Assert that no unknown `X` or high-impedance `Z` value appears on `clk_out` after reset release with known inputs.

## Coverage Goals

- Cover `div_ratio` classes: `0`, `1`, even `>= 2`, odd `>= 3`, and maximum representable ratio for tested widths.
- Cover reset assertion in each operating class.
- Cover ratio changes for all class transitions: force-low to bypass, bypass to divided, divided to force-low, even to odd, odd to even, and divided to divided with different values.
- Cover at least three complete output periods for representative even and odd ratios.
- Cover both reset-at-boundary and reset-mid-period scenarios.

## Pass and Fail Criteria

Pass criteria:

- All directed and parameterized tests complete with zero assertion failures and zero scoreboard mismatches.
- Measured output periods match the selected `div_ratio`.
- Reset and ratio-change restart behavior matches the design specification.
- Functional coverage reaches all ratio classes and transition classes listed above.

Fail criteria:

- `clk_out` toggles during reset or ratio-0 mode.
- Divide-by-1 mode does not follow `clk`.
- Any divided mode produces the wrong output period.
- Odd-ratio duty behavior exceeds the allowed half-cycle balance target.
- Ratio changes allow stale counter state to produce an old-ratio output period after restart.
- `clk_out` becomes unknown with known `clk`, `rst_n`, and `div_ratio` inputs.
