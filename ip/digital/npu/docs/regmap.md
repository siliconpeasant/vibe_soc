# npu Register Map

## Address Map

All addresses are local byte offsets from the NPU aperture base. Register accesses are 32-bit little-endian and word aligned. Register writes require `mm_wstrb=4'b1111`.

| Offset/range | Name | Access | Reset | Description |
|---|---|---|---:|---|
| `0x0000` | `CTRL` | RW/pulse | `0x0000_0000` | Start, soft reset, interrupt enable, clear pulses. |
| `0x0004` | `STATUS` | RO/W1C | `0x0000_0000` | Busy, done, error, saturation, command active. |
| `0x0008` | `CFG` | RW/RO mixed | `0x8000_0300` | K-step count, activation stride, fixed signed INT8 mode advertisement. |
| `0x000c` | `ACT_BASE` | RW | `0x0000_0000` | Activation scratchpad byte base for descriptor. |
| `0x0010` | `WGT_BASE` | RW | `0x0000_0000` | Weight scratchpad byte base for descriptor. |
| `0x0014` | `OUT_BASE` | RW | `0x0000_0000` | Output scratchpad byte base for descriptor. |
| `0x0018` | `ACC_INIT` | RW | `0x0000_0000` | Signed 32-bit accumulator initial value. Use zero for normal inference. |
| `0x001c` | `ACC_RESULT` | RO | `0x0000_0000` | Last output element's signed 32-bit post-bias accumulator. |
| `0x0020` | `ERR_CODE` | RO/W1C | `0x0000_0000` | Encoded most recent error. |
| `0x0024` | `OUT_CFG` | RW | `0x0003_0000` | Output count, output stride, and weight row stride. |
| `0x0028` | `BIAS_BASE` | RW | `0x0000_0000` | Bias scratchpad word base. |
| `0x002c` | `QUANT_MULT` | RW | `0x0000_0001` | Signed INT32 fixed-point multiplier. |
| `0x0030` | `QUANT_CFG` | RW | `0x7f00_0000` | Quant shift, output zero point, activation mode, ReLU6 clamp maximum. |
| `0x0034` | `LAST_OUT_COUNT` | RO | `0x0000_0000` | Number of output bytes stored by the most recent command. |
| `0x0100-0x013f` | `ACT_SPM` | RW | all zero | 64-byte activation scratchpad window. |
| `0x0200-0x023f` | `WGT_SPM` | RW | all zero | 64-byte weight scratchpad window. |
| `0x0300-0x033f` | `OUT_SPM` | RW | all zero | 64-byte output scratchpad window. |
| `0x0400-0x043f` | `BIAS_SPM` | RW | all zero | 16 signed INT32 bias entries. |

Addresses not listed above are illegal and return `mm_error=1`.

## CTRL - Offset `0x0000`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `start` | WO pulse | 0 | Write 1 to start one command. Ignored when written 0. If `busy=1`, aborts the active command and sets `ERR_CODE=START_BUSY`. |
| `[1]` | `soft_reset` | WO pulse | 0 | Write 1 to synchronously reset NPU registers, FSM, and scratchpads. Wins over `start` if both are written. |
| `[2]` | `irq_en` | RW | 0 | Enables level interrupt assertion for sticky `done` or `error`. |
| `[3]` | `clear_done` | WO pulse | 0 | Write 1 to clear `STATUS.done`. |
| `[4]` | `clear_error` | WO pulse | 0 | Write 1 to clear `STATUS.error` and `ERR_CODE`. |
| `[31:5]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

Reads of pulse bits return zero. `irq_en` retains its programmed value until reset, soft reset, or another write.

## STATUS - Offset `0x0004`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `busy` | RO | 0 | Command is active. |
| `[1]` | `done` | RO/W1C | 0 | Sticky successful command completion. |
| `[2]` | `error` | RO/W1C | 0 | Sticky command or host access error. |
| `[3]` | `sat_overflow` | RO/W1C | 0 | Sticky indication that final signed INT8 saturation clipped at least one output element. |
| `[4]` | `cmd_active` | RO | 0 | Mirrors `busy` in this implementation. |
| `[31:5]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

Writing 1 to bits `[1]`, `[2]`, or `[3]` clears the matching sticky bit. Writing 1 to bit `[2]` also clears `ERR_CODE`. Writes to RO bits have no effect. A STATUS write still requires `mm_wstrb=4'b1111`.

## CFG - Offset `0x0008`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `k_count_m1` | RW | `0x00` | Number of four-lane MAC groups minus one. This is the previous dot-product vector-count field. |
| `[15:8]` | `act_stride_bytes_m1` | RW | `0x03` | Byte stride between activation four-lane groups minus one. Reset value gives packed four-byte groups. |
| `[30:16]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |
| `[31]` | `signed_int8_mode` | RO | 1 | Fixed advertisement that activation and weight operands are signed INT8. Writes ignored. |

`k_count = k_count_m1 + 1`. `act_stride = act_stride_bytes_m1 + 1`.

## ACT_BASE - Offset `0x000c`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `act_base` | RW | `0x00` | Activation scratchpad byte base. Start range check requires the final accessed activation byte to be `<= 63`. |
| `[31:8]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

## WGT_BASE - Offset `0x0010`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `wgt_base` | RW | `0x00` | Weight scratchpad byte base for output row 0, K group 0. |
| `[31:8]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

## OUT_BASE - Offset `0x0014`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `out_base` | RW | `0x00` | Output scratchpad byte base for output element 0. |
| `[31:8]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

## ACC_INIT - Offset `0x0018`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `acc_init` | RW | `0x0000_0000` | Signed 32-bit accumulator seed latched on accepted start. Program zero for normal inference and backward-compatible pure dot product. |

## ACC_RESULT - Offset `0x001c`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `acc_result` | RO | `0x0000_0000` | Signed 32-bit post-bias accumulator for the last output element completed by the most recent successful command. Descriptor or start-busy errors do not update it. |

Writes to `ACC_RESULT` are illegal and return `mm_error=1` with `ERR_CODE=RO_WRITE`.

## ERR_CODE - Offset `0x0020`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[4:0]` | `err_code` | RO/W1C | 0 | Encoded most recent error. Any nonzero W1C write clears the code and `STATUS.error`. |
| `[31:5]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

| Code | Name | Meaning |
|---:|---|---|
| `0` | `NONE` | No sticky error. |
| `1` | `START_BUSY` | `CTRL.start` written while a command was busy. |
| `2` | `DESC_ACT_RANGE` | Activation descriptor exceeded `ACT_SPM[0:63]`. |
| `3` | `DESC_WGT_RANGE` | Weight descriptor exceeded `WGT_SPM[0:63]`. |
| `4` | `DESC_OUT_RANGE` | Output descriptor exceeded `OUT_SPM[0:63]`. |
| `5` | `INVALID_ADDR` | Host accessed an unimplemented address. |
| `6` | `REG_UNALIGNED` | Host accessed register space with an unaligned address. |
| `7` | `BAD_REG_WSTRB` | Host wrote a writable register without full-word write strobes. |
| `8` | `SPM_UNALIGNED` | Host accessed a scratchpad window with an unaligned transfer start. |
| `9` | `DESC_BIAS_RANGE` | Bias descriptor exceeded `BIAS_SPM[0:15]`. |
| `10` | `DESC_QUANT_SHIFT` | `QUANT_CFG.quant_shift > 31`. |
| `11` | `DESC_ACTIVATION` | Activation mode or ReLU6 clamp configuration is illegal. |
| `12` | `RO_WRITE` | Host wrote a read-only register. |
| `13` | `BIAS_BAD_WSTRB` | Host wrote `BIAS_SPM` without full-word write strobes. |

If a new error occurs while a previous error is still sticky, the latest error code overwrites `ERR_CODE`.

## OUT_CFG - Offset `0x0024`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `out_count_m1` | RW | `0x00` | Number of output elements minus one. Reset value produces one output element. |
| `[15:8]` | `out_stride_bytes_m1` | RW | `0x00` | Byte stride between output elements minus one. Reset value gives contiguous byte outputs. |
| `[23:16]` | `wgt_stride_bytes_m1` | RW | `0x03` | Byte stride between weight rows for consecutive output elements minus one. Reset value gives four-byte rows. |
| `[31:24]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

`out_count = out_count_m1 + 1`. `out_stride = out_stride_bytes_m1 + 1`. `wgt_stride = wgt_stride_bytes_m1 + 1`.

## BIAS_BASE - Offset `0x0028`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[3:0]` | `bias_base` | RW | `0x0` | Bias scratchpad word index for output element 0. |
| `[31:4]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

The bias for output element `out_idx` is `BIAS_SPM[bias_base + out_idx]`. Bias is signed INT32, has zero point 0, and is expected to be quantized at accumulator scale.

## QUANT_MULT - Offset `0x002c`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `multiplier` | RW | `0x0000_0001` | Signed INT32 fixed-point multiplier applied after bias addition. |

`multiplier=1` and `QUANT_CFG.quant_shift=0` preserve unscaled dot-product output before zero-point and activation handling.

## QUANT_CFG - Offset `0x0030`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[5:0]` | `quant_shift` | RW | `0x00` | Arithmetic right shift amount after multiplier and rounding. Values above 31 are descriptor errors. |
| `[7:6]` | `reserved0` | RO | 0 | Reads as zero; writes ignored. |
| `[15:8]` | `out_zero_point` | RW | `0x00` | Signed INT8 output zero point added after requantization. |
| `[17:16]` | `activation_mode` | RW | `0x0` | `0` none, `1` ReLU lower clamp to output zero point, `2` ReLU6-style lower/upper clamp. `3` is illegal. |
| `[23:18]` | `reserved1` | RO | 0 | Reads as zero; writes ignored. |
| `[31:24]` | `relu6_max` | RW | `0x7f` | Signed INT8 upper clamp for ReLU6-style activation. Must be greater than or equal to `out_zero_point` in ReLU6 mode. |

The activation clamp operates on the signed value after output zero-point addition and before final signed INT8 saturation.

## LAST_OUT_COUNT - Offset `0x0034`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `last_out_count` | RO | `0x00` | Number of output bytes stored by the most recent command. A descriptor error leaves this field zero. |
| `[31:8]` | `reserved` | RO | 0 | Reads as zero; writes ignored. |

Writes to `LAST_OUT_COUNT` are illegal and return `mm_error=1` with `ERR_CODE=RO_WRITE`.

## Scratchpad Windows

Activation, weight, and output scratchpad windows are byte-addressed arrays accessed by word-aligned 32-bit host transfers.

For a byte scratchpad read at aligned address `A`, where `offset = A - window_base`:

```text
mm_rdata[7:0]   = spm[offset + 0]
mm_rdata[15:8]  = spm[offset + 1]
mm_rdata[23:16] = spm[offset + 2]
mm_rdata[31:24] = spm[offset + 3]
```

For a byte scratchpad write, lane `n` updates `spm[offset+n]` only when `mm_wstrb[n]=1`.

The bias scratchpad is a 16-entry signed INT32 array:

| Address | Entry |
|---:|---:|
| `0x0400` | `BIAS_SPM[0]` |
| `0x0404` | `BIAS_SPM[1]` |
| `...` | `...` |
| `0x043c` | `BIAS_SPM[15]` |

The compute engine reads `ACT_SPM`, `WGT_SPM`, and `BIAS_SPM`. It writes one byte per output element to `OUT_SPM[out_base + out_idx * out_stride]` on successful execution. Host writes to `OUT_SPM` are allowed when idle so software can clear or seed output bytes.
