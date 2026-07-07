# npu Design Specification

## Scope

`npu` is a tiny software-managed INT8 inference-layer accelerator. It keeps the existing `npu` top module and local memory-mapped target interface, and evolves the prior single-output dot-product demo into a minimal quantized linear/GEMV tile engine.

The IP computes one command at a time. A command may produce one or more signed INT8 output elements from a shared activation vector, row-strided signed INT8 weights, signed INT32 bias values, fixed-point requantization, output zero-point addition, optional clamp activation, and signed INT8 saturation.

The implementation target remains portable Verilog-2005. The IP does not include an APB, AHB, AXI, TileLink, external DMA master, clock/reset generator, top-level address decoder, interrupt controller, SRAM macro wrapper, test wrapper, SDC, RTL, or testbench in this doc stage.

## Knowledge-Base Evidence

- `documents/integrated-circuit/Google/Quantization-and-Training-of-Neural-Networks-for-Efficient-Integer-Arithmetic-Only-Inference.pdf:page 4` describes a typical quantized fused layer as INT8/UINT8 operands, signed INT32 accumulation, INT32 bias, fixed-point multiplier with rounding and right shift, saturating cast to 8-bit output, and clamp-style activations such as ReLU/ReLU6.
- The same Google paper page states that bias is represented as INT32 with zero-point 0 and accumulator scale because bias quantization error can shift outputs.
- `tutorials/npu/zsc_v2_npu_tutorial/markdown/chapter5.md:314` identifies INT8 quantization, zero-point/scale, per-channel quantization, and fused activation as key inference-accelerator techniques, and notes that ReLU6/clamp is simple in hardware.
- Earlier NPU knowledge-base evidence selected scratchpad-dominant storage for predictable tensor data with software/DMA scheduling, and required a preserved datapath/controller partition.

## Functional Blocks

| Block | Responsibility |
|---|---|
| Memory-mapped frontend | Samples one host request when `mm_valid && mm_ready`, decodes register and scratchpad addresses, returns `mm_rdata`, `mm_ready`, and `mm_error`. |
| Register file | Stores control, descriptors, quantization controls, status, interrupt enable, accumulator seed/result, and last error code. |
| Scratchpads | Four local windows: 64-byte activation, 64-byte weight, 64-byte output, and 16-entry signed INT32 bias. |
| Load/store sequencer | Latches descriptors on `start`, validates ranges, and generates activation, weight, output, and bias addresses for each output element and K step. |
| MAC datapath | Multiplies four signed INT8 activation values by four signed INT8 weight values and adds the four signed products into a signed INT32 accumulator. |
| Bias and requantization | Adds signed INT32 bias, multiplies by signed INT32 quant multiplier in a signed 64-bit temporary, applies deterministic rounding/right shift, then adds signed INT8 output zero point. |
| Activation and saturation | Applies optional quantized ReLU or ReLU6-style clamp, then saturates to signed INT8 `[-128, 127]`. |
| Controller FSM | Owns command acceptance, busy/done/error sequencing, start-while-busy abort, output stores, and sticky status. |

## Operation

Software uses the IP as follows:

1. Write activation bytes to `ACT_SPM`, weight bytes to `WGT_SPM`, and signed INT32 bias words to `BIAS_SPM` if bias is used.
2. Program `CFG`, `ACT_BASE`, `WGT_BASE`, `OUT_BASE`, `OUT_CFG`, `BIAS_BASE`, `QUANT_MULT`, `QUANT_CFG`, and optionally `ACC_INIT`.
3. Set `CTRL.start`.
4. Poll `STATUS.done` or wait for `irq` if `CTRL.irq_en` is set.
5. Read output bytes from `OUT_SPM`, `ACC_RESULT` for the last output element's signed INT32 post-bias accumulator, and `LAST_OUT_COUNT`.
6. Clear sticky `done`, `error`, and `sat_overflow` status with W1C writes or the matching `CTRL` clear pulse.

One command computes:

```text
k_count     = CFG.k_count_m1 + 1
act_stride  = CFG.act_stride_bytes_m1 + 1
out_count   = OUT_CFG.out_count_m1 + 1
wgt_stride  = OUT_CFG.wgt_stride_bytes_m1 + 1
out_stride  = OUT_CFG.out_stride_bytes_m1 + 1

for out_idx in 0 .. out_count-1:
  acc = ACC_INIT
  for k in 0 .. k_count-1:
    act_addr = ACT_BASE.act_base + k * act_stride
    wgt_addr = WGT_BASE.wgt_base + out_idx * wgt_stride + k * 4
    acc += signed8(ACT_SPM[act_addr + 0]) * signed8(WGT_SPM[wgt_addr + 0])
    acc += signed8(ACT_SPM[act_addr + 1]) * signed8(WGT_SPM[wgt_addr + 1])
    acc += signed8(ACT_SPM[act_addr + 2]) * signed8(WGT_SPM[wgt_addr + 2])
    acc += signed8(ACT_SPM[act_addr + 3]) * signed8(WGT_SPM[wgt_addr + 3])

  post_bias = acc + signed32(BIAS_SPM[BIAS_BASE.bias_base + out_idx])
  scaled64 = round_shift(signed64(post_bias) * signed64(QUANT_MULT.multiplier),
                         QUANT_CFG.quant_shift)
  with_zp = scaled64 + signed8(QUANT_CFG.out_zero_point)
  activated = apply_activation(with_zp, QUANT_CFG)
  OUT_SPM[OUT_BASE.out_base + out_idx * out_stride] = saturate_int8(activated)

ACC_RESULT = post_bias of the last completed output element
LAST_OUT_COUNT = number of output bytes stored by the command
```

`round_shift(value, shift)` is exact:

```text
if shift == 0:
  round_shift(value, shift) = value
else:
  round_shift(value, shift) = (value + (1 << (shift - 1))) >>> shift
```

`>>>` is an arithmetic right shift. `quant_shift` values above 31 are illegal descriptor values. The fixed-point multiplier is signed INT32; software may use a positive multiplier for normal quantized inference or `1` for compatibility behavior.

Activation modes are exact:

| Mode | Name | Behavior before final INT8 saturation |
|---:|---|---|
| `0` | none | No clamp. |
| `1` | ReLU | Clamp lower bound to signed `out_zero_point`. |
| `2` | ReLU6-style clamp | Clamp lower bound to signed `out_zero_point` and upper bound to signed `relu6_max`. `relu6_max` must be greater than or equal to `out_zero_point`. |

The ReLU lower bound uses the quantized output zero point because zero in the real-valued domain maps to that code point. The ReLU6-style upper bound is programmable because the quantized representation of 6 depends on output scale, which is not stored in this minimal hardware.

## Backward-Compatible Dot-Product Profile

The previous single-output dot-product behavior is preserved as a degenerate command when software programs:

- `OUT_CFG.out_count_m1 = 0`
- `OUT_CFG.out_stride_bytes_m1 = 0`
- `OUT_CFG.wgt_stride_bytes_m1` to any legal value because only one output row is used
- `BIAS_SPM[BIAS_BASE.bias_base] = 0`
- `QUANT_MULT.multiplier = 1`
- `QUANT_CFG.quant_shift = 0`
- `QUANT_CFG.out_zero_point = 0`
- `QUANT_CFG.activation_mode = 0`
- `ACC_INIT = 0` for pure dot-product compatibility

With those settings, `ACC_RESULT` equals the signed INT32 dot product and `OUT_SPM[OUT_BASE]` equals the signed INT8 saturated accumulator. `CFG.k_count_m1` is the previous vector-count-minus-one field, and `CFG.act_stride_bytes_m1` defaults to packed four-byte groups.

## Scratchpad Organization

| Scratchpad | Address window | Size | Internal index |
|---|---:|---:|---|
| Activation | `0x0100-0x013f` | 64 bytes | `mm_addr - 0x0100` |
| Weight | `0x0200-0x023f` | 64 bytes | `mm_addr - 0x0200` |
| Output | `0x0300-0x033f` | 64 bytes | `mm_addr - 0x0300` |
| Bias | `0x0400-0x043f` | 16 signed INT32 words | `(mm_addr - 0x0400) >> 2` |

Activation, weight, and output scratchpad host transfers are 32-bit word transfers at word-aligned addresses. Byte writes are supported through `mm_wstrb[3:0]`, where lane `n` updates byte `word_base+n`. Reads return four bytes in little-endian lane order.

Bias scratchpad host transfers are 32-bit word transfers at word-aligned addresses. Bias writes require `mm_wstrb=4'b1111` and store one signed INT32 word. Bias reads return one signed INT32 word. Bias values are treated as INT32 with zero point 0 and accumulator scale.

While a command is busy, host accesses to any scratchpad window stall by holding `mm_ready=0`. Register accesses still complete. Software must hold `mm_valid`, `mm_write`, `mm_addr`, `mm_wdata`, and `mm_wstrb` stable while `mm_ready=0`.

## Controller State and Sequence

| State | Description | Exit |
|---|---|---|
| `IDLE` | No command is running. Register and scratchpad host accesses are accepted. | Accepted `CTRL.start` moves to `CHECK`. |
| `CHECK` | Latches and validates all descriptor fields and clears per-command counters. | Descriptor error moves to `ERROR`; otherwise moves to `LOAD`. |
| `LOAD` | Reads four activation bytes and four weight bytes for the current output element and K step. | Moves to `MAC`. |
| `MAC` | Computes four signed products and updates the signed INT32 accumulator. | More K steps move to `LOAD`; final K step moves to `BIAS`. |
| `BIAS` | Adds signed INT32 bias and latches post-bias accumulator for the current output element. | Moves to `REQUANT`. |
| `REQUANT` | Applies multiplier, rounding/right shift, output zero point, activation clamp, and signed INT8 saturation. | Moves to `STORE`. |
| `STORE` | Writes one output byte, updates `LAST_OUT_COUNT`, and sets `sat_overflow` if final INT8 saturation clipped. | More output elements move to `LOAD`; final output moves to `DONE`. |
| `DONE` | Sets sticky `done`, clears `busy`, and returns to `IDLE`. | Automatic return to `IDLE` after status update. |
| `ERROR` | Sets sticky `error`, latches `ERR_CODE`, clears `busy`, suppresses further output stores, and returns to `IDLE`. | Automatic return to `IDLE` after status update. |

`STATUS.busy` is high in all non-idle command states except the terminal status update cycle if the RTL chooses a registered terminal pulse. `STATUS.cmd_active` mirrors `busy`. A `CTRL.start` write while `busy=1` aborts the active command, suppresses any further output stores, clears `done`, sets `error`, sets `ERR_CODE=START_BUSY`, and returns the FSM to `IDLE`.

If an error occurs after one or more output bytes have already been stored, `LAST_OUT_COUNT` reports the number of bytes stored before the error. Descriptor errors are checked before any output store, so they leave `LAST_OUT_COUNT=0`.

## Descriptor Range Checks

Descriptor checks occur on accepted `start` before any scratchpad read or output write. If multiple descriptor errors are present, priority is activation range, weight range, output range, bias range, quant shift, then activation configuration.

| Check | Error |
|---|---|
| `ACT_BASE.act_base + CFG.k_count_m1 * (CFG.act_stride_bytes_m1 + 1) + 3 > 63` | `DESC_ACT_RANGE` |
| `WGT_BASE.wgt_base + OUT_CFG.out_count_m1 * (OUT_CFG.wgt_stride_bytes_m1 + 1) + CFG.k_count_m1 * 4 + 3 > 63` | `DESC_WGT_RANGE` |
| `OUT_BASE.out_base + OUT_CFG.out_count_m1 * (OUT_CFG.out_stride_bytes_m1 + 1) > 63` | `DESC_OUT_RANGE` |
| `BIAS_BASE.bias_base + OUT_CFG.out_count_m1 > 15` | `DESC_BIAS_RANGE` |
| `QUANT_CFG.quant_shift > 31` | `DESC_QUANT_SHIFT` |
| `QUANT_CFG.activation_mode > 2`, or ReLU6 mode with signed `relu6_max < out_zero_point` | `DESC_ACTIVATION` |

The fixed `k * 4` weight offset means each output row stores packed four-lane weight groups. The programmable `wgt_stride` selects the byte distance between output rows.

## Reset and Clear Behavior

Hardware reset `rst_n` is active-low asynchronous assert. On reset assertion:

- All control and status registers reset to zero except documented nonzero reset fields.
- `CFG` advertises signed INT8 mode and resets `k_count_m1=0`, `act_stride_bytes_m1=3`.
- `OUT_CFG` resets to one output, one-byte output stride, and four-byte weight row stride.
- `QUANT_MULT` resets to `1`.
- `QUANT_CFG` resets to shift 0, output zero point 0, activation none, and ReLU6 upper clamp 127.
- `busy`, `done`, `error`, `sat_overflow`, `cmd_active`, `irq`, `ACC_INIT`, `ACC_RESULT`, `LAST_OUT_COUNT`, and `ERR_CODE` reset to zero.
- All activation, weight, output, and bias scratchpad storage resets to zero.
- The FSM resets to `IDLE`.

`CTRL.soft_reset` is a synchronous pulse with the same architected effects as hardware reset. If `CTRL.soft_reset` and `CTRL.start` are written in the same access, soft reset wins and start is ignored.

Sticky bits clear as follows:

| Sticky state | Set by | Cleared by |
|---|---|---|
| `STATUS.done` | Successful command completion | `STATUS` W1C bit 1, `CTRL.clear_done`, accepted new `start`, `soft_reset`, hardware reset |
| `STATUS.error` | Command error or access error | `STATUS` W1C bit 2, `CTRL.clear_error`, accepted new `start`, `soft_reset`, hardware reset |
| `STATUS.sat_overflow` | Final signed INT8 cast clips above 127 or below -128 | `STATUS` W1C bit 3, accepted new `start`, `soft_reset`, hardware reset |
| `ERR_CODE` | Most recent error event | `ERR_CODE` W1C nonzero write, `CTRL.clear_error`, accepted new `start`, `soft_reset`, hardware reset |

Clearing `error` also clears `ERR_CODE`. Clearing `done` does not clear `ACC_RESULT`, `LAST_OUT_COUNT`, or output scratchpad contents.

## Error Behavior

Errors are deterministic and sticky until explicitly cleared. `mm_error` is a one-transaction response signal; `STATUS.error` and `ERR_CODE` are sticky architectural state.

| Error | Condition | `mm_error` | Sticky effect |
|---|---|---:|---|
| `START_BUSY` | `CTRL.start` written while `busy=1` | 0 | Abort active command, set `STATUS.error`, set `ERR_CODE=1`. |
| `DESC_ACT_RANGE` | Activation descriptor exceeds `ACT_SPM[0:63]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=2`. |
| `DESC_WGT_RANGE` | Weight descriptor exceeds `WGT_SPM[0:63]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=3`. |
| `DESC_OUT_RANGE` | Output descriptor exceeds `OUT_SPM[0:63]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=4`. |
| `INVALID_ADDR` | Address outside implemented registers and scratchpad windows. | 1 | Set `STATUS.error`, set `ERR_CODE=5`. |
| `REG_UNALIGNED` | Register access with `mm_addr[1:0] != 2'b00`. | 1 | Set `STATUS.error`, set `ERR_CODE=6`. |
| `BAD_REG_WSTRB` | Writable register write with invalid strobes. | 1 | Set `STATUS.error`, set `ERR_CODE=7`. |
| `SPM_UNALIGNED` | Scratchpad access with `mm_addr[1:0] != 2'b00`. | 1 | Set `STATUS.error`, set `ERR_CODE=8`. |
| `DESC_BIAS_RANGE` | Bias descriptor exceeds `BIAS_SPM[0:15]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=9`. |
| `DESC_QUANT_SHIFT` | `QUANT_CFG.quant_shift > 31`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=10`. |
| `DESC_ACTIVATION` | Invalid activation mode or invalid ReLU6 clamp range. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=11`. |
| `RO_WRITE` | Host writes a read-only register. | 1 | Set `STATUS.error`, set `ERR_CODE=12`. |
| `BIAS_BAD_WSTRB` | Bias scratchpad write without `mm_wstrb=4'b1111`. | 1 | Set `STATUS.error`, set `ERR_CODE=13`. |

Invalid host accesses do not modify the targeted register or scratchpad location. If a new error occurs while a previous error is still sticky, the latest error overwrites `ERR_CODE`.

## Interrupt Behavior

`irq` is a level output:

```text
irq = CTRL.irq_en && (STATUS.done || STATUS.error)
```

`irq` asserts after a command completes successfully, after a command error, or after a host access error when interrupt enable is set. It deasserts only when interrupt enable is cleared or all sticky source bits are cleared.

## Synthesis Constraints and Implementation Rules

- Use one clock input, `clk`; do not generate internal clocks.
- Use resettable synchronous state elements with asynchronous active-low reset where required by `rst_n`.
- Do not instantiate vendor primitives, clock gates, SRAM macros, PLLs, synchronizers for other domains, or latches.
- Use clock-enable style control for datapath and scratchpad updates.
- Keep arithmetic explicitly signed in RTL to preserve INT8, signed INT32 bias, signed INT32 accumulation, signed multiplier, and signed saturation semantics.
- The small scratchpads may be implemented as resettable register arrays for the first RTL. If an SRAM macro is later required, the doc and RTL stages must be reopened to define macro ports, reset behavior, MBIST hooks, and access latency.
- No numeric frequency target is approved in this doc stage. Timing constraints are limited to the later SDC stage and must use the SoC-selected process/library assumptions.

## Assumptions

- The local memory-mapped interface is little-endian.
- The upstream bus wrapper, if any, holds request signals stable until `mm_ready=1`.
- `rst_n` is distributed by the SoC as an asynchronous assert reset with safe deassertion relative to `clk`.
- Software owns movement between system memory and the NPU scratchpads; the internal load/store sequencer only addresses local scratchpads.
- Software chooses quantization parameters, including the multiplier, shift, output zero point, and ReLU6 upper clamp, from the model's quantization metadata.
- Per-channel quantization is represented by programming one multiplier/shift for this minimal command. True per-output multiplier arrays are outside this approved scope and require reopening docs.
