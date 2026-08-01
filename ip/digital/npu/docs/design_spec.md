# npu Design Specification

## Scope

`npu` is a tiny software-managed INT8 inference-layer accelerator. It keeps the existing `npu` top module, local memory-mapped target interface, register offsets, and default software-visible capacities, and evolves the prior single-output dot-product demo into a minimal quantized linear/GEMV tile engine.

NPU v2 phase 1 is limited to a backward-compatible scratchpad baseline. It makes the four local capacities compile-time parameters inside the existing fixed address apertures and defines an internal replacement contract for a future synchronous SRAM implementation. This phase does not add DMA, software-visible banking, larger apertures, external SRAM ports, or MAC-lane changes. The first implementation remains a behavioral register-array model; implementation-only byte-lane banking may reduce read-multiplexer fan-in, but this document does not claim SRAM inference.

The IP computes one command at a time. A command may produce one or more signed INT8 output elements from a shared activation vector, row-strided signed INT8 weights, signed INT32 bias values, fixed-point requantization, output zero-point addition, optional clamp activation, and signed INT8 saturation.

The implementation target remains portable Verilog-2005. The IP does not include an APB, AHB, AXI, TileLink, external DMA master, clock/reset generator, top-level address decoder, interrupt controller, SRAM macro wrapper, test wrapper, SDC, RTL, or testbench in this doc stage.

## Knowledge-Base Evidence

- `documents/integrated-circuit/Google/Quantization-and-Training-of-Neural-Networks-for-Efficient-Integer-Arithmetic-Only-Inference.pdf:page 4` describes a typical quantized fused layer as INT8/UINT8 operands, signed INT32 accumulation, INT32 bias, fixed-point multiplier with rounding and right shift, saturating cast to 8-bit output, and clamp-style activations such as ReLU/ReLU6.
- The same Google paper page states that bias is represented as INT32 with zero-point 0 and accumulator scale because bias quantization error can shift outputs.
- `tutorials/npu/zsc_v2_npu_tutorial/markdown/chapter5.md:314` identifies INT8 quantization, zero-point/scale, per-channel quantization, and fused activation as key inference-accelerator techniques, and notes that ReLU6/clamp is simple in hardware.
- Earlier NPU knowledge-base evidence selected scratchpad-dominant storage for predictable tensor data with software/DMA scheduling, and required a preserved datapath/controller partition.
- `tutorials/npu/zsc_npu_tutorial/markdown/chapter5.md` states that scratchpads provide deterministic access and should be parameterized. This supports compile-time capacity parameters while retaining software-managed local storage.
- `CaliptraIntegrationSpecification.md:137` describes parameterized 1R1W SRAMs with flopped read data and byte write enables. This is reference evidence for the future internal replacement boundary; no Caliptra macro or external memory port is instantiated in phase 1.
- `eda/tool_docs/dc/man/cat3/hdlin_mux_for_array_read_sparseness_limit.3` explains that variable array reads become mux/select operators and that their input population affects area. It supports reducing the fan-in of the behavioral scratchpad read structures. The knowledge base does not prescribe a project-specific bank organization; the four byte-lane implementation is an engineering choice driven by the registered Yosys baseline, where scratchpad logic owns most generic mux cells.

## Functional Blocks

| Block | Responsibility |
|---|---|
| Memory-mapped frontend | Samples one host request when `mm_valid && mm_ready`, decodes register and scratchpad addresses, returns `mm_rdata`, `mm_ready`, and `mm_error`. |
| Register file | Stores control, descriptors, quantization controls, status, interrupt enable, accumulator seed/result, and last error code. |
| Scratchpads | Four parameterized local-capacity prefixes inside fixed 64-byte apertures. Defaults are 64-byte activation, 64-byte weight, 64-byte output, and 16-entry signed INT32 bias. Phase 1 storage is behavioral register arrays. |
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

| Scratchpad | Reserved address aperture | Implemented capacity | Internal index |
|---|---:|---:|---|
| Activation | `0x0100-0x013f` | `ACT_SPM_BYTES`, default 64 bytes | `mm_addr - 0x0100` |
| Weight | `0x0200-0x023f` | `WGT_SPM_BYTES`, default 64 bytes | `mm_addr - 0x0200` |
| Output | `0x0300-0x033f` | `OUT_SPM_BYTES`, default 64 bytes | `mm_addr - 0x0300` |
| Bias | `0x0400-0x043f` | `BIAS_SPM_WORDS`, default 16 signed INT32 words | `(mm_addr - 0x0400) >> 2` |

The legal parameter contract is:

| Parameter | Legal values | Alignment rule |
|---|---:|---|
| `ACT_SPM_BYTES` | 4 through 64 | Multiple of 4 bytes. |
| `WGT_SPM_BYTES` | 4 through 64 | Multiple of 4 bytes. |
| `OUT_SPM_BYTES` | 4 through 64 | Multiple of 4 bytes. |
| `BIAS_SPM_WORDS` | 1 through 16 | Integral 32-bit words; implemented byte capacity is `4 * BIAS_SPM_WORDS`. |

Each implemented region is the contiguous prefix beginning at its fixed aperture base. The four reserved apertures remain fixed and non-overlapping for every legal parameter combination; parameters cannot move a base or consume another aperture. An aligned host transfer is implemented only when all four transferred bytes fall within the selected capacity. An access to an unused tail inside a reserved aperture is an `INVALID_ADDR` access. Default parameter values preserve the full legacy windows and all prior valid addresses.

Activation, weight, and output scratchpad host transfers are 32-bit word transfers at word-aligned addresses. Byte writes are supported through `mm_wstrb[3:0]`, where lane `n` updates byte `word_base+n`. Reads return four bytes in little-endian lane order.

Bias scratchpad host transfers are 32-bit word transfers at word-aligned addresses. Bias writes require `mm_wstrb=4'b1111` and store one signed INT32 word. Bias reads return one signed INT32 word. Bias values are treated as INT32 with zero point 0 and accumulator scale. The last implemented bias word index is `BIAS_SPM_WORDS-1`.

The phase-1 register-array implementation stripes each byte-addressed activation, weight, and output scratchpad across four 8-bit lane banks selected by byte address bits `[1:0]`; each bank has `SPM_BYTES/4` entries. An aligned host read concatenates one entry from each bank. A compute read may start at any legal byte address, so activation and weight reads select the current or next bank word as required and rotate the four bank bytes back into consecutive little-endian order. Host and compute ownership are mutually exclusive and share the activation, weight, and bias read structures. This banking is not visible in the address map, capacity parameters, reset contents, host latency, descriptor arithmetic, or future 32-bit 1R1W replacement boundary.

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
| `ACT_BASE.act_base + CFG.k_count_m1 * (CFG.act_stride_bytes_m1 + 1) + 3 >= ACT_SPM_BYTES` | `DESC_ACT_RANGE` |
| `WGT_BASE.wgt_base + OUT_CFG.out_count_m1 * (OUT_CFG.wgt_stride_bytes_m1 + 1) + CFG.k_count_m1 * 4 + 3 >= WGT_SPM_BYTES` | `DESC_WGT_RANGE` |
| `OUT_BASE.out_base + OUT_CFG.out_count_m1 * (OUT_CFG.out_stride_bytes_m1 + 1) >= OUT_SPM_BYTES` | `DESC_OUT_RANGE` |
| `BIAS_BASE.bias_base + OUT_CFG.out_count_m1 >= BIAS_SPM_WORDS` | `DESC_BIAS_RANGE` |
| `QUANT_CFG.quant_shift > 31` | `DESC_QUANT_SHIFT` |
| `QUANT_CFG.activation_mode > 2`, or ReLU6 mode with signed `relu6_max < out_zero_point` | `DESC_ACTIVATION` |

The fixed `k * 4` weight offset means each output row stores packed four-lane weight groups. The programmable `wgt_stride` selects the byte distance between output rows.

The implementation may realize accepted compute addresses with running registers rather than recomputing the products above every cycle. The registers are seeded from the accepted bases, advance activation by `act_stride` and weight within a row by four bytes for each K step, advance the weight-row base by `wgt_stride`, and advance output by `out_stride`. Descriptor range checks still evaluate the full documented expressions before any array access; running address widths must not weaken overflow or error detection.

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

Only the implemented capacity of each scratchpad has architected contents. Hardware reset and `CTRL.soft_reset` zero every implemented byte or word for the selected parameters. In the phase-1 behavioral register-array baseline, this clear is performed by the existing reset/soft-reset logic and does not introduce an initialization wait state.

## Future SRAM-Replacement Contract

The SRAM boundary is internal to `npu`; phase 1 adds no top-level SRAM ports. A later implementation may replace each behavioral array with one independently addressed, parameterized 1-read/1-write memory having these semantics:

- One synchronous read request and one synchronous write request may be issued in the same cycle.
- Read data is flopped and becomes valid one rising edge after the read request.
- Activation, weight, and output memories use a 32-bit data path with four byte write enables. Bias uses a 32-bit data path; normal bias writes assert all four enables.
- Address width is derived from the selected capacity. Out-of-range addresses must be rejected before a memory request is issued.
- Read-during-write behavior to the same word is not architecturally relied upon. Host scratchpad accesses remain stalled while compute owns the memories, so the controller must avoid such collisions.

A synchronous one-cycle macro cannot be substituted without controller changes. The replacement implementation must pipeline each compute read address one cycle ahead of operand consumption, capture read data only when valid, and delay accumulator, bias, requantization, output-store, `LAST_OUT_COUNT`, and `done` updates as needed. A host scratchpad read must retain its request and return `mm_ready` only when the flopped read data is available. Host/register ordering, descriptor errors, output values, and interrupt semantics must remain unchanged; the specification deliberately does not require a fixed command latency.

The architectural zero-after-reset contract also applies to a macro that has no storage reset. Such an implementation must zero the active capacity with a controller/wrapper initialization sequence after hardware-reset deassertion and after an accepted `CTRL.soft_reset`. During that sequence, `busy`, sticky status, and `irq` remain at reset values, no command or scratchpad access may complete, and `mm_ready` may be held low until clearing is complete. Register contents retain their documented reset values. If the selected macro supplies an equivalent guaranteed initialization mechanism, it may be used instead. Any future implementation that cannot preserve these visible reset and backpressure rules must reopen the doc stage.

## Error Behavior

Errors are deterministic and sticky until explicitly cleared. `mm_error` is a one-transaction response signal; `STATUS.error` and `ERR_CODE` are sticky architectural state.

| Error | Condition | `mm_error` | Sticky effect |
|---|---|---:|---|
| `START_BUSY` | `CTRL.start` written while `busy=1` | 0 | Abort active command, set `STATUS.error`, set `ERR_CODE=1`. |
| `DESC_ACT_RANGE` | Activation descriptor exceeds `ACT_SPM[0:ACT_SPM_BYTES-1]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=2`. |
| `DESC_WGT_RANGE` | Weight descriptor exceeds `WGT_SPM[0:WGT_SPM_BYTES-1]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=3`. |
| `DESC_OUT_RANGE` | Output descriptor exceeds `OUT_SPM[0:OUT_SPM_BYTES-1]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=4`. |
| `INVALID_ADDR` | Address outside implemented registers and scratchpad windows. | 1 | Set `STATUS.error`, set `ERR_CODE=5`. |
| `REG_UNALIGNED` | Register access with `mm_addr[1:0] != 2'b00`. | 1 | Set `STATUS.error`, set `ERR_CODE=6`. |
| `BAD_REG_WSTRB` | Writable register write with invalid strobes. | 1 | Set `STATUS.error`, set `ERR_CODE=7`. |
| `SPM_UNALIGNED` | Scratchpad access with `mm_addr[1:0] != 2'b00`. | 1 | Set `STATUS.error`, set `ERR_CODE=8`. |
| `DESC_BIAS_RANGE` | Bias descriptor exceeds `BIAS_SPM[0:BIAS_SPM_WORDS-1]`. | 0 | Command enters `ERROR`, no output write, set `ERR_CODE=9`. |
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
- A four-lane MAC may use a balanced signed-product reduction tree, but its modulo-`2^32` accumulator result must remain bit-exact.
- Phase 1 implements scratchpads as behavioral resettable register arrays with compile-time capacities and implementation-only byte-lane banking. No memory inference result is assumed or claimed.
- The internal future replacement boundary is 1R1W with one-cycle flopped read data and byte write enables as specified above. Selecting a concrete macro, adding MBIST/repair hooks, or exposing memory ports requires reopening the doc stage.
- No numeric frequency target is approved in this doc stage. Timing constraints are limited to the later SDC stage and must use the SoC-selected process/library assumptions.

## Assumptions

- The local memory-mapped interface is little-endian.
- The upstream bus wrapper, if any, holds request signals stable until `mm_ready=1`.
- `rst_n` is distributed by the SoC as an asynchronous assert reset with safe deassertion relative to `clk`.
- Software owns movement between system memory and the NPU scratchpads; the internal load/store sequencer only addresses local scratchpads.
- Software chooses quantization parameters, including the multiplier, shift, output zero point, and ReLU6 upper clamp, from the model's quantization metadata.
- Per-channel quantization is represented by programming one multiplier/shift for this minimal command. True per-output multiplier arrays are outside this approved scope and require reopening docs.
