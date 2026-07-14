# npu Verification Plan

## Scope

Verification covers the standalone `npu` IP defined by `design_spec.md`, `interface_spec.md`, and `regmap.md`. It must use the project Make/MCP flow through registered `soc-build` tools during later verification stages; this doc stage does not create a testbench or run simulation.

The verification target is the minimal INT8 inference-layer behavior plus the NPU v2 phase-1 parameterized scratchpad contract: default-capacity compatibility, legal reduced capacities inside fixed apertures, capacity-aware descriptor checking, and the behavioral register-array baseline. The future 1R1W macro boundary is a specification target for later replacement verification; phase 1 must not claim memory inference.

## Testbench Model

The verification environment should include:

- A clock/reset driver for `clk` and active-low asynchronous `rst_n`.
- A local memory-mapped bus functional model that can issue reads, writes, hold requests stable across `mm_ready=0`, and check `mm_error`.
- A software-visible register model for reset values, sticky status, W1C behavior, read-only write errors, and `irq`.
- Parameter-aware scratchpad models for `ACT_SPM_BYTES`, `WGT_SPM_BYTES`, `OUT_SPM_BYTES`, and `BIAS_SPM_WORDS`, with default models of 64 bytes, 64 bytes, 64 bytes, and 16 signed INT32 entries.
- A reference model for signed INT8 multiply, signed INT32 accumulation, signed INT32 bias addition, signed 64-bit multiplier, rounding/arithmetic right shift, signed output zero point addition, activation clamp, and signed INT8 saturation.
- Scoreboards for `ACC_RESULT`, `LAST_OUT_COUNT`, `OUT_SPM`, sticky status, `ERR_CODE`, `mm_error`, and `irq`.

## Directed Test Matrix

| Test | Stimulus | Expected result |
|---|---|---|
| Reset defaults | Assert/deassert `rst_n`, then read all registers and scratchpad words. | Registers match reset values, all scratchpad bytes/words zero, `busy/done/error/sat_overflow/irq` low, `CFG=0x8000_0300`, `OUT_CFG=0x0003_0000`, `QUANT_MULT=1`, `QUANT_CFG=0x7f00_0000`. |
| Default parameter compatibility | Elaborate with all four defaults and run the existing register, scratchpad, dot-product, multi-output, reset, and error regressions. | All legacy valid addresses, values, status, and timing of the behavioral baseline remain unchanged. |
| Legal reduced capacities | Run at least one aligned reduced configuration and the minimum configuration: byte capacities are multiples of four in `[4,64]`, bias words in `[1,16]`. | Elaboration succeeds; each implemented prefix is accessible and computes correctly without address overlap. |
| Illegal parameter guards | Attempt zero, over-maximum, and non-word-multiple byte capacities, plus zero and over-16 bias entries. | Elaboration/configuration fails clearly; no runtime behavior is claimed for illegal builds. |
| Inactive aperture tails | In a reduced-capacity build, issue aligned reads/writes at the first word beyond each implemented prefix. | Transfer returns `mm_error=1`, target contents do not change, sticky error is set, and `ERR_CODE=INVALID_ADDR`. |
| Reduced-capacity descriptor boundaries | For every scratchpad, run one descriptor ending exactly at the last implemented element and one ending one element beyond it. | Boundary descriptor succeeds; one-past descriptor fails before output store with the matching `DESC_*_RANGE` code. |
| Register read/write | Write and read `CFG`, bases, `ACC_INIT`, `OUT_CFG`, `BIAS_BASE`, `QUANT_MULT`, `QUANT_CFG`, `CTRL.irq_en`, and W1C status bits. | Writable fields update, RO/reserved bits read as specified, pulse bits read zero, W1C clears only targeted sticky bits. |
| Read-only write errors | Write `ACC_RESULT` and `LAST_OUT_COUNT`. | `mm_error=1`, values unchanged, `STATUS.error=1`, `ERR_CODE=RO_WRITE`. |
| Scratchpad byte writes/reads | Write activation, weight, and output windows with selective `mm_wstrb` patterns and read back aligned words. | Only selected byte lanes change; little-endian lane mapping is correct; zero-strobe byte scratchpad write is no-op. |
| Bias scratchpad access | Write/read all 16 bias entries, including negative INT32 values. Also try partial bias write strobes. | Full-word writes store signed values; partial writes fail with `BIAS_BAD_WSTRB` and do not modify the target entry. |
| Backward-compatible dot product | Program one output, zero bias, multiplier 1, shift 0, zero point 0, activation none, `ACC_INIT=0`, and packed K groups. | `ACC_RESULT` equals signed INT32 dot product; output byte equals signed INT8 saturated accumulator; previous dot-product behavior is preserved. |
| Multi-output inference | Program `out_count_m1 > 0`, a shared activation vector, row-strided weights, contiguous outputs, and zero bias/identity quantization. | Each output byte matches the reference dot product for its weight row; `LAST_OUT_COUNT=out_count`; `done=1`, `error=0`. |
| Output stride | Program non-contiguous `out_stride_bytes_m1` and seed output scratchpad with known values. | Only addressed output byte locations are updated; untouched output bytes keep seed values. |
| Weight stride | Program non-default `wgt_stride_bytes_m1` with separated weight rows. | Each output uses the correct row base and packed K groups. |
| Activation stride | Program non-default `act_stride_bytes_m1` with gaps between activation K groups. | The reference model and RTL consume the same activation bytes. |
| Signed operands | Use negative two's-complement INT8 activation and weight values. | Sign extension and signed multiplication match reference model. |
| Bias addition | Program nonzero positive and negative signed INT32 biases for multiple outputs. | `ACC_RESULT` and output bytes include the selected per-output bias; bias range uses `bias_base + out_idx`. |
| Multiplier and shift requant | Use multiplier values other than 1 and shifts 0, 1, and larger legal values. | Signed 64-bit product, rounding offset, arithmetic right shift, and final output match the reference model. |
| Output zero point | Program positive and negative `out_zero_point` values. | Output zero point is added after requantization and before activation/saturation. |
| Activation none | Choose values below and above zero with activation mode 0. | No activation clamp occurs; only final INT8 saturation may clip. |
| ReLU activation | Program activation mode 1 and nonzero output zero point. | Values below signed output zero point clamp to that zero point; higher values pass through before saturation. |
| ReLU6-style clamp | Program activation mode 2, output zero point, and `relu6_max`. | Values below zero point clamp low; values above `relu6_max` clamp high; in-range values pass through. |
| Saturation high | Choose requantized value above 127 after activation. | Output byte is `0x7f`, `sat_overflow=1`. |
| Saturation low | Choose requantized value below -128 after activation. | Output byte is `0x80`, `sat_overflow=1`. |
| Start while busy | Start a legal multi-output command, then write `CTRL.start` again before completion. | Active command aborts, no further output stores occur, `done=0`, `error=1`, `ERR_CODE=START_BUSY`, `busy` clears. |
| Descriptor activation out of range | Program activation base/count/stride so the final activation byte is `>= ACT_SPM_BYTES`. | Command enters error before output store, `LAST_OUT_COUNT=0`, `ERR_CODE=DESC_ACT_RANGE`. |
| Descriptor weight out of range | Program legal activation but weight base/count/stride so the final weight byte is `>= WGT_SPM_BYTES`. | Command enters error before output store, `LAST_OUT_COUNT=0`, `ERR_CODE=DESC_WGT_RANGE`. |
| Descriptor output out of range | Program output base/count/stride so an output byte is `>= OUT_SPM_BYTES`. | Command enters error before output store, `LAST_OUT_COUNT=0`, `ERR_CODE=DESC_OUT_RANGE`. |
| Descriptor bias out of range | Program `BIAS_BASE + out_count_m1 >= BIAS_SPM_WORDS`. | Command enters error before output store, `LAST_OUT_COUNT=0`, `ERR_CODE=DESC_BIAS_RANGE`. |
| Invalid quant shift | Program `QUANT_CFG.quant_shift > 31`. | Command enters error before output store, `ERR_CODE=DESC_QUANT_SHIFT`. |
| Invalid activation config | Program activation mode 3, and separately ReLU6 with signed `relu6_max < out_zero_point`. | Command enters error before output store, `ERR_CODE=DESC_ACTIVATION`. |
| Illegal access | Exercise invalid address, unaligned register access, bad register write strobe, read-only register write, unaligned scratchpad access, and bad bias strobe. | `mm_error=1`, target state is not modified, sticky `error=1`, `ERR_CODE` matches latest error. |
| Scratchpad busy stall | Hold a scratchpad request while a command is busy. | `mm_ready=0` until the command is terminal; the access then completes using idle scratchpad rules. |
| IRQ done behavior | Set `irq_en`, run a successful command, then clear `done`. | `irq` asserts with `done`, remains level while `done=1`, deasserts after `done` clear or `irq_en=0`. |
| IRQ error behavior | Set `irq_en`, cause descriptor or illegal-access error, then clear error. | `irq` asserts with sticky `error`, remains level while `error=1`, deasserts after error clear or `irq_en=0`. |
| Soft reset | Program non-default registers and scratchpads, then write `CTRL.soft_reset`. | Registers, FSM, status, IRQ, and scratchpads return to reset defaults. |
| Reduced-capacity reset | Fill every implemented location in a reduced-capacity build, then apply hardware reset and separately soft reset. | Every implemented location reads zero; inactive tails remain inaccessible; status and IRQ have reset values. |
| Future synchronous-memory latency model | When the later macro replacement is implemented, substitute a 1R1W model with one-cycle flopped read data and byte enables. | Host reads wait for valid data; compute results and status match the register-array reference despite added cycles; no address/data off-by-one errors occur. |
| Future macro zero-fill | When a non-resettable macro model is implemented, apply hardware reset and soft reset after nonzero contents. | No command or scratchpad request completes during initialization; all active locations are zero before access resumes; `busy`, sticky status, and `irq` remain reset. |

## Assertions and Checks

Recommended SystemVerilog assertions or equivalent checker code:

- `busy` is high only while the FSM is executing a command.
- `irq == irq_en && (done || error)` after reset is deasserted.
- `mm_error` is only sampled as meaningful when `mm_valid && mm_ready`.
- Register writes with bad strobes do not modify the target register.
- Read-only registers are not modified by host writes.
- Activation, weight, and output scratchpad writes update only lanes selected by `mm_wstrb`.
- No host or compute memory request is issued with an address outside the configured capacity.
- Fixed aperture bases remain non-overlapping for all legal parameter combinations.
- Bias scratchpad writes require all byte strobes and preserve the target word on bad strobes.
- A command with descriptor range error never writes `OUT_SPM`.
- `ACC_RESULT` updates only on successful command completion and equals the last output element's post-bias accumulator.
- `LAST_OUT_COUNT` increments only after an output byte store and equals `out_count` after a successful command.
- `sat_overflow` is set if any output element's final cast clips outside signed INT8 range.
- `CTRL.start` while busy clears `busy` through the abort path and sets `ERR_CODE=START_BUSY`.
- Scratchpad requests issued while busy are not accepted until `mm_ready=1`.
- Reserved register bits read zero.
- No X values appear on `mm_rdata`, `mm_ready`, `mm_error`, or `irq` after reset deassertion.

## Functional Coverage Goals

Cover at least:

- All FSM states and legal state transitions.
- All `ERR_CODE` values.
- Default and reduced legal capacity configurations, including minimum, middle, and maximum values.
- `k_count_m1` values for one group, multiple groups, and maximum in-range descriptor for the configured scratchpads.
- `out_count_m1` values for one output, multiple outputs, and maximum in-range output/bias descriptors.
- Reset stride and non-default cases for activation, weight-row, and output strides.
- Positive, negative, and mixed-sign INT8 operands.
- Positive, negative, and zero signed INT32 bias values.
- Multiplier reset value, positive non-one values, negative values if supported by RTL signed arithmetic, and zero.
- Quant shift values 0, 1, middle legal values, 31, and illegal values above 31.
- Output zero point values 0, positive, and negative.
- Activation modes none, ReLU, ReLU6-style clamp, and illegal mode 3.
- Requantized results below -128, within [-128, 127], and above 127.
- Each `mm_wstrb` bit asserted individually and multiple-lane combinations for byte scratchpad writes.
- Each implemented scratchpad prefix: first word, middle word, last aligned word, and first aligned inactive-tail word when present.
- Bias entries 0, a middle implemented entry, the last implemented entry, and the first inactive entry when present.
- `irq` assertion from done and from error, plus deassertion by clearing source and by clearing `irq_en`.
- Reset during idle and reset during busy.

## Pass and Fail Criteria

Pass criteria:

- All directed tests pass with no scoreboard mismatches.
- Assertions/checkers report zero failures.
- Functional coverage hits all required goals or has reviewed waivers for unreachable bins.
- No unknown values are observed on externally visible outputs after reset.
- Simulation logs are produced through the registered project verification flow in the later verification stage.

Fail criteria:

- Any mismatch in accumulator, output byte, last output count, status, error code, interrupt, reset default, or scratchpad contents.
- Any illegal access mutates state that should remain unchanged.
- Any required directed test is missing, especially multi-output inference, bias, multiplier/shift requantization, zero point, activation none/ReLU/ReLU6, bias range, output stride, and previous dot-product regression.
- A legal capacity fails elaboration, an illegal capacity is silently accepted, an inactive aperture tail is accessible, or a descriptor uses a fixed 64-byte/16-word limit instead of the configured capacity.
- Any assertion failure without a documented design change and updated spec.
- Any simulator run bypasses the registered project flow in a gated verification stage.

## Verification Assumptions

- The bus functional model holds request signals stable while `mm_ready=0`.
- Reference model uses two's-complement signed arithmetic and a signed 64-bit temporary for requantization.
- Later RTL keeps the public interface and register map defined in these docs; any RTL-driven interface change requires reopening doc stage.
- Phase 1 uses behavioral register arrays. Memory inference, a concrete SRAM macro, banking, external SRAM ports, DMA, and MBIST are outside this verification claim.
