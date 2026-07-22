# stories260k Register Map

## Address Map

All addresses are local byte offsets from the stories260k aperture base (`mm_addr[19:0]`, 1 MiB). CSR accesses are 32-bit little-endian and word aligned; CSR write strobes are ignored. Read data and error responses are registered and valid in the cycle after acceptance (see `interface_spec.md`).

| Offset/range | Name | Access | Reset | Description |
|---|---|---|---:|---|
| `0x000` | `ID` | RO | `0x5354_4F52` | IP identifier, ASCII `"STOR"`. |
| `0x004` | `VERSION` | RO | `0x0001_0000` | IP version 1.0. |
| `0x008` | `CTRL` | RW/W1S pulse | `0x0000_0000` | Start, soft reset, interrupt enable, chain enable. |
| `0x00C` | `STATUS` | RO/W1C | `0x0000_0000` | Busy, done, error, error code, token valid. |
| `0x010` | `TOKEN_IN` | RW | `0x0000_0000` | Input token id for the next run. |
| `0x014` | `TOKEN_OUT` | RO | `0x0000_0000` | Most recently generated token id. |
| `0x018` | `SEQ_POS` | RO | `0x0000_0000` | Context length within the current run. |
| `0x01C` | `GEN_CFG` | RW | `0x0002_0000` | Generation length minus one, softmax z-domain shift (default 1). |
| `0x020` | `CYCLE_LO` | RO | `0x0000_0000` | Busy-cycle counter `[31:0]`. |
| `0x024` | `CYCLE_HI` | RO | `0x0000_0000` | Busy-cycle counter `[63:32]`. |
| `0x028` | `TOKEN_CNT` | RO | `0x0000_0000` | Tokens completed since last clear. |
| `0x02C` | `MAC_LO` | RO | `0x0000_0000` | MAC-operation counter `[31:0]`. |
| `0x030` | `MAC_HI` | RO | `0x0000_0000` | MAC-operation counter `[63:32]`. |
| `0x034` | `PERF_CLR` | WO | — | Any aligned write clears all performance counters. |
| `0x038` | `DEC_CFG` | RW | `0x0000_0020` | Decode policy: frequency penalty, adaptive ramp, last-K no-repeat. |
| `0x03C` | `ERR_ADDR` | RO | `0x0000_0000` | Code and byte address of the most recent erroring host access. |
| `0x10000-0x373FF` | `WBUF` | RW | power-on zero | 157 KiB mixed-W4/W8 weight/scale/RoPE window (5,024 × 32 B). |
| `0x40000-0x5EFFF` | `KVBUF` | RW | power-on zero | 124 KiB KV-cache window (usage 122,880 B). |
| `0x60000-0x60FFF` | `ACTBUF` | RW | power-on zero | 4 KiB activation window (usage 3,536 B). |
| `0x64000-0x65FFF` | `VECBUF` | RW | power-on zero | 8 KiB vector/requant window (usage 1,704 B). |

Addresses not listed — including CSR offsets `0x040-0xFFF` and all of `0x01000-0x0FFFF`, `0x35000-0x3FFFF`, `0x5F000-0x5FFFF`, `0x61000-0x63FFF`, `0x66000-0xFFFFF` — return `mm_error=1` (`INVALID_ADDR`).

## ID - Offset `0x000`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `id` | RO | `0x5354_4F52` | ASCII `"STOR"` (0x53='S', 0x54='T', 0x4F='O', 0x52='R'). Writes return `RO_WRITE`. |

## VERSION - Offset `0x004`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[15:0]` | `minor` | RO | `0x0000` | Minor version. |
| `[31:16]` | `major` | RO | `0x0001` | Major version. Writes return `RO_WRITE`. |

## CTRL - Offset `0x008`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `start` | W1S pulse | 0 | Write 1 to start a run. Rejected with `mm_error=1` (`BUSY_START`) when `busy=1`; the active run is not affected. An accepted start clears `done`, `error`, and `ecode`. |
| `[1]` | `soft_reset` | W1S pulse | 0 | Write 1 to synchronously reset all CSR state, counters, and engines. Buffer contents are preserved. Preempts `start` in the same write. |
| `[2]` | `irq_en` | RW | 0 | Enables level interrupt assertion. Rewritten from data bit 2 on **every** CTRL write. |
| `[3]` | `chain_en` | RW | 0 | Enables chained decode (token feedback) for runs started after this write. Rewritten from data bit 3 on every CTRL write. |
| `[31:4]` | reserved | RO | 0 | Reads as zero; writes ignored. |

Pulse bits read as zero. A start-only write with the current enables must be issued as `start | (irq_en<<2) | (chain_en<<3)`.

## STATUS - Offset `0x00C`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `busy` | RO | 0 | A run is active (sequencer not idle). |
| `[1]` | `done` | RO/W1C | 0 | Sticky successful run completion. |
| `[2]` | `error` | RO/W1C | 0 | Sticky **core run** error (`CTX_OVERFLOW`). Host access errors do not set this bit. |
| `[3]` | reserved | RO | 0 | Reads as zero. |
| `[7:4]` | `ecode` | RO | 0 | Last core error code (see table below). Cleared by an accepted start or reset, **not** by STATUS W1C. |
| `[8]` | `token_valid` | RO/W1C | 0 | Sticky per-token indication that `TOKEN_OUT` has been updated. Interrupt source. |
| `[31:9]` | reserved | RO | 0 | Reads as zero; writes ignored. |

Writing 1 to bits `[1]`, `[2]`, or `[8]` clears the matching sticky bit. An accepted start also clears `done`/`error`/`ecode` (not `token_valid`; it clears on reset or W1C).

## TOKEN_IN - Offset `0x010`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[8:0]` | `token_in` | RW | 0 | Token id for the next run (legal 0..511; BOS = 1). Software must keep the value in range — there is no hardware range check. |
| `[31:9]` | reserved | RO | 0 | Reads as zero; writes ignored. |

## TOKEN_OUT - Offset `0x014`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[8:0]` | `token_out` | RO | 0 | Most recently generated token id. Stable until the next token completes. Writes return `RO_WRITE`. |
| `[31:9]` | reserved | RO | 0 | Reads as zero; writes ignored. |

## SEQ_POS - Offset `0x018`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[9:0]` | `seq_pos` | RO | 0 | Context length within the current run: KV entries written per layer, i.e. the position the next token appends at (0..512). Reset to 0 by every accepted start (each run starts a fresh context); increments once per completed token. Writes return `RO_WRITE`. |
| `[31:10]` | reserved | RO | 0 | Reads as zero; writes ignored. |

## GEN_CFG - Offset `0x01C`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[8:0]` | `gen_len_m1` | RW | 0 | Tokens to generate minus one. With `CTRL.chain_en=1` a run emits `gen_len_m1 + 1` tokens (unless `CTX_OVERFLOW` terminates it first); with `chain_en=0` exactly one token is emitted per start regardless of this field. |
| `[16:9]` | reserved | RO | 0 | Reads as zero; writes ignored. |
| `[20:17]` | `sm_shift` | RW | 1 | Softmax z-domain downshift: `z = clamp((s[t] − smax) >>> sm_shift, −128, 0)`, mapping the score-domain delta into the exp LUT's 1/16 input domain. Latched per run. The calibrated default for the shipped QAT mixed-W4/W8 image (v1.3) is 1. |
| `[31:21]` | reserved | RO | 0 | Reads as zero; writes ignored. |

## CYCLE_LO / CYCLE_HI - Offsets `0x020` / `0x024`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `cycle` | RO | 0 | 64-bit count of `clk` cycles with `busy=1` since last clear, split across the two registers. Wraps at 2^64. Writes return `RO_WRITE`. |

## TOKEN_CNT - Offset `0x028`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `token_cnt` | RO | 0 | Tokens completed since last clear. Wraps at 2^32. Writes return `RO_WRITE`. |

## MAC_LO / MAC_HI - Offsets `0x02C` / `0x030`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `mac` | RO | 0 | 64-bit count of issued logical MAC slots: +64 per MVM run cycle and per fused-attention max/exp/V beat (including padded lanes). Wraps at 2^64. Writes return `RO_WRITE`. |

## PERF_CLR - Offset `0x034`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[31:0]` | `perf_clr` | WO | — | Any aligned write (any data) clears `CYCLE`, `MAC`, and `TOKEN_CNT` to zero. This offset is write-only: a read returns `mm_error=1` (`INVALID_ADDR`). |

Counters are also cleared by `rst_n` and `CTRL.soft_reset`. An accepted start does not clear them; hosts measure throughput as `TOKEN_CNT × f_clk / CYCLE` over any interval bounded by `PERF_CLR`.

## DEC_CFG - Offset `0x038`

Programmable decode policy for the fused streaming argmax. Reset defaults match the R4 QAT golden trail (`rep_pen=32`, adaptive off, no-repeat off) so software that never touches this register remains bit-exact with prior images.

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `rep_pen` | RW | 32 | Base frequency-penalty multiplier. Adjusted logit = raw logit − `count[token] × pen_eff`, with `count` a 4-bit saturating counter cleared at each accepted start. |
| `[8]` | `adapt_en` | RW | 0 | When 0, `pen_eff = rep_pen`. When 1, `pen_eff = rep_pen + tok_cnt[9:4]` (adds `floor(tokens_completed / 16)`, ramping slowly for long stories). |
| `[12:9]` | `norep_win` | RW | 0 | Last-K hard ban: `0` disables; `N` (1..15) excludes the last `N` emitted tokens from argmax (newest first). Vocab size 512 guarantees a legal alternative. |
| `[31:13]` | reserved | RO | 0 | Reads as zero; writes ignored. |

Fields are live: the next argmax uses the current CSR values (no per-run latch). Frequency and recent-token state clear on accepted start and soft reset; `DEC_CFG` itself reloads to reset defaults on soft reset.

## ERR_ADDR - Offset `0x03C`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[19:0]` | `err_addr` | RO | 0 | Local byte address of the **most recent** host access that returned `mm_error=1` (latest error wins). Cleared by reset/soft reset only. Writes return `RO_WRITE`. |
| `[23:20]` | `err_code` | RO | 0 | Error code of that host access (1 `ALIGN`, 2 `RO_WRITE`, 3 `BUSY_START`, 5 `INVALID_ADDR`). |
| `[31:24]` | reserved | RO | 0 | Reads as zero; writes ignored. |

## Error Codes

Two disjoint channels (exact RTL behavior). **Host access errors** return `mm_error=1` on the transfer and latch `ERR_ADDR`/`err_code`; they never set `STATUS.error`/`ecode`. **Core run errors** set sticky `STATUS.error` + `STATUS.ecode` and assert `irq` if enabled.

| Code | Name | Channel | Meaning |
|---:|---|---|---|
| 0 | `NONE` | — | No error. |
| 1 | `ALIGN` | host (`mm_error`) | CSR access with `mm_addr[1:0] != 2'b00`. (Buffer addresses ignore `[1:0]`.) |
| 2 | `RO_WRITE` | host (`mm_error`) | Write to a read-only CSR. |
| 3 | `BUSY_START` | host (`mm_error`) | `CTRL.start` written while `busy=1`; active run unaffected. |
| 4 | reserved | — | Not produced. |
| 5 | `INVALID_ADDR` | host (`mm_error`) | Address outside implemented CSR offsets and buffer windows. |
| 6 | `CTX_OVERFLOW` | core (`STATUS.ecode`) | Defensive error for a request beyond the 512-entry context. Legal `GEN_CFG` values request at most 512 tokens, so normal software cannot produce it. |
| 7-15 | reserved | — | Not produced. |

`STATUS.ecode[3:0]` reports the last core error code. Invalid host accesses never modify the targeted register or buffer location.

## Buffer Windows

Buffer windows are byte-addressed arrays accessed by word-aligned 32-bit host transfers with individual byte strobes; `mm_addr[1:0]` is ignored (aliases to the aligned word). While `busy=1`, buffer transfers see `mm_ready=0` and complete after the run terminates. Buffer contents are **not** cleared by `rst_n` or `CTRL.soft_reset` (behavioral arrays power up at zero).

| Window | Base | Size | Word geometry | Usage | Layout summary (details in `design_spec.md`) |
|---|---:|---:|---|---:|---|
| `WBUF` | `0x10000` | 157 KiB | 5,024 × 32 B | 160,448 B (5,014 words) | Baseline tiles `+0x00000-0x201FF`, scales `+0x20200-0x222BF`, RoPE 4374..4629, INT8 high-halves: L1 QKV/WO 4630..4821, L2 WQ/WO 4822..4949, L3 WQ 4950..5013. |
| `KVBUF` | `0x40000` | 124 KiB | 3,968 × 32 B | 122,880 B (3,840 words) | Layer `l` at word `l×768` (4 KV heads × 512 pos): K data `+0` (`h×64 + t/8`), K scales `+256` (`h×32 + t/16`), V data `+384`, V scales `+640`. |
| `ACTBUF` | `0x60000` | 4 KiB | 512 × 8 B | 3,536 B address envelope (442 words) | X 0, XB 8, Q 16, KT 24, V 32, SCORE/PR legacy-reserved 40..359, ATT 360, HB 368, HB2 390, HB3 412, Y 434. |
| `VECBUF` | `0x64000` | 8 KiB | 1,024 × 8 B | 1,704 B (213 words) | RMSNorm gains 0..175, requant slots 176..212; slots 35 and 36 reserved. |

A later synchronous SRAM macro replacement must preserve this register map and all host-visible rules; macro contents are host-initialized (there is no reset clear in either implementation), and registered read latency is absorbed inside the core per `interface_spec.md`.
