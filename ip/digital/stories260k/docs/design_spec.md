# stories260k Design Specification

## Scope

`stories260k` is a fixed-model mixed-W4/W8 inference engine for the llama2.c TinyStories `stories260K` checkpoint. It executes greedy autoregressive decode: token embedding, 5 GQA transformer layers with KV-cache append, fused tiled attention, final RMSNorm, tied-embedding logits, and fused streaming argmax. All weights, the full 512-position checkpoint context, all activations, and all lookup tables reside in four on-chip scratchpad buffers (WBUF/KVBUF/ACTBUF/VECBUF, 284 KiB total). There is no external-memory path at run time. All matrices are signed INT4 except the activation-sensitive layer-1 WQ matrix, which is signed INT8 and uses 2 KiB of the existing WBUF spare; SRAM capacities and public address windows are unchanged.

This document is the engineering contract and is written to match the implemented RTL baseline under `de/rtl/` exactly: model geometry, fixed-point operator semantics (including every shift and rounding constant), buffer layouts word-for-word, sequencer states, MVM and SFU semantics, performance counters, and the error model. The implementation is portable Verilog-2005 with one clock `clk` and one active-low asynchronous reset `rst_n`. Simulation evidence for the performance section is VCS `soc_sim` (see Performance Counters).

## v1.2 Implemented Delta

The v1.2 RTL addresses the measured 512-token throughput and RTL/golden
numerical divergence without changing the public MMIO interface, the
512-token context cap, or any SRAM capacity:

- The sequenced `C_SCORE -> C_SM -> C_AV` chain is replaced by a fused attention
  engine. It processes eight positions per tile: pass 1 reads K plus its scale
  and finds the scaled-score maximum; pass 2 alternates a recomputed K/exp beat
  with a V accumulation beat. Only the final eight-lane INT8 head result is
  written to ACTBUF. The existing SCORE and PR regions become reserved.
- The disjoint KV scale address range is exposed as a second internal read bank so
  a data tile and its scale word are available in the same cycle. This is an
  internal SRAM-macro replacement-contract change only; the 3,968 x 256-bit
  KVBUF capacity, byte layout, host window, and contents remain unchanged.
- The existing softmax formula and 8-bit exp LUT are preserved. The fused engine
  matches the documented round-half-up `p'` fold and final attention
  requant exactly; it keeps the reciprocal local, leaving VEC slot 35 reserved.
- KV append changes from truncating `u >>> s` to signed round-half-up
  `(u + (s ? 2^(s-1) : 0)) >>> s`, matching the fixed-point golden model.
  Resolve argmax ties to the lowest token index globally, matching Python's
  first-maximum rule.
- Layer-1 WQ is stored as INT8 split 4+4 rows across the normal 64 tile words
  and WBUF words 4630..4693. A third logical WBUF read bank supplies the upper
  half in the same cycle, preserving the 64-MAC/cycle schedule. All other
  matrices remain INT4. The calibrated `GEN_CFG.sm_shift` reset default is 2.
- Acceptance is met by first-divergence tracing, a 64-token bit-exact fixed-model
  assertion, and 64/256/512 real-image VCS regressions. The complete 512-token
  run measures 5,716,993 cycles = 8,955.8 token/s at 100 MHz, versus the old
  13,786,113-cycle / 3,713.9-token/s baseline.

The measured 512-token average is 11,166 cycles/token: fused attention consumes
4,740 cycles/token and all other executed states consume 6,426 cycles/token.
Timing closure at 100 MHz and the physical cost of the extra logical read banks
still require fresh synthesis and OpenROAD STA; cycle-accurate simulation is
not timing-closure evidence.

## Knowledge-Base Evidence

- `github.com/karpathy/llama2.c` `run.c`/`model.c`: measured `stories260K` header `{dim, hidden_dim, n_layers, n_heads, n_kv_heads, vocab_size, seq_len} = {64, 172, 5, 8, 4, 512, 512}`, tensor order, tied classifier, RMSNorm pre-norm, RoPE on q/k, SwiGLU, argmax at temperature 0.
- Ainslie et al. 2023 (GQA): 8 query heads share 4 KV heads, `kv_mul = 2`, `kv_dim = 32`; query head `h` reads KV head `h>>1`.
- `documents/integrated-circuit/Google/Quantization-and-Training-of-Neural-Networks-for-Efficient-Integer-Arithmetic-Only-Inference.pdf:page 4`: integer operands, INT32 accumulation, fixed-point multiplier with shift, saturating cast.
- AWQ (Lin et al. 2023): per-64-group INT4 weight scales.
- RoFormer (Su et al. 2021): rotary embedding over adjacent pairs, base-10000, q/k only.
- FlashAttention (Dao et al. 2022): running-max softmax, deferred denominator.

## Model Definition

### Geometry

| Symbol | Value | Meaning |
|---|---:|---|
| DIM | 64 | Model width; NHEADS × HEAD_DIM. |
| HID | 172 | FFN hidden width (tiles pad M to 176 rows, w2 pads K to 176). |
| NLAYERS | 5 | Transformer layers. |
| NHEADS | 8 | Query heads. |
| NKVH | 4 | KV heads (GQA, `kv_mul = 2`); query head `h` attends KV head `h>>1`. |
| HEAD_DIM | 8 | Elements per head; 4 RoPE pairs per head. |
| KV_DIM | 32 | NKVH × HEAD_DIM — width of the k/v vectors. |
| VLEN | 512 | Vocabulary; BOS = 1 per llama2.c convention. |
| Checkpoint seq | 512 | `seq_len` field in the checkpoint header. |
| **Chip context cap** | **512** | Matches the checkpoint `seq_len`; no shorter hardware-only cap. |

### Parameter Count

| Tensor group | Shape | Count |
|---|---|---:|
| `token_embedding` (also the tied classifier) | 512 × 64 | 32,768 |
| `rms_att_gain` (5 layers) | 5 × 64 | 320 |
| `wq` | 5 × (64 × 64) | 20,480 |
| `wk` + `wv` | 5 × 2 × (32 × 64) | 20,480 |
| `wo` | 5 × (64 × 64) | 20,480 |
| `rms_ffn_gain` (5 layers) | 5 × 64 | 320 |
| `w1` + `w3` | 5 × 2 × (172 × 64) | 110,080 |
| `w2` | 5 × (64 × 172) | 55,040 |
| `rms_final_gain` | 64 | 64 |
| **Total** | | **260,032** |

There are no biases. The classifier shares `token_embedding` rows (tied weights).

### Per-Token Dataflow Order

```text
x      = embed(token)                                # SFU: INT4 row dequant -> INT8, lands on x8 grid
for l in 0..4:
  xb      = rmsnorm(x, gain[l].att)                  # SFU
  q       = mvm(wq, xb)                              # MVM 64 out (requant q slot folds 1/sqrt(8))
  k       = mvm(wk, xb)                              # MVM 32 out (GQA)
  v       = mvm(wv, xb)                              # MVM 32 out
  q,k     = rope(q, k, pos)                          # SFU, q (8 words) and k (4 words)
  kvbuf.append(l, pos, k, v)                         # SFU quantize INT8 -> INT4 + pow2 scale, 4 KV heads
  for h in 0..7:                                     # query heads; kvh = h>>1
    att_h   = fused_attn(q_h, K,V,sk,sv,sm_shift)    # 8 positions/tile; no SCORE/PR spill
  y       = mvm(wo, att)                             # MVM, INT8 out
  x       = sat8(x + y)                              # SFU residual (x8 grid)
  xb      = rmsnorm(x, gain[l].ffn)
  hb      = mvm(w1, xb)                              # 172 out, x16 grid
  hb2     = mvm(w3, xb)                              # 172 out, x16 grid
  hb3     = swiglu(hb, hb2)                          # SFU
  y       = mvm(w2, hb3)                             # 64 out, K=176 padded, back to x8 grid
  x       = sat8(x + y)                              # SFU residual
xb     = rmsnorm(x, gain_final)
token' = argmax_t( mvm_logits(embedding, xb) )       # streaming, fused at MVM writeback
```

## Quantization and Number Formats

| Quantity | Format | Notes |
|---|---|---|
| Weights | signed INT4 except layer-1 WQ signed INT8; 8×8-tile interleaved | W4 range -8..7, W8 range -128..127. Packer: `q = round(v/scale)` with per-format saturation and zero K/M padding. |
| Weight group scales | unsigned INT16, Q4.12 | One per 64 K-elements per row; packer: `scale = round(max|seg|/7 × 4096 × 2^k_x)` clamped to [1, 32767]. Only the embedding uses `k_x = 3`, establishing the **×8 residual grid**; every other matrix consumes an already-gridded input (`k_x = 0`). |
| Activations | signed INT8 | Residual stream `x` lives on the ×8 grid end to end; FFN intermediate grid is ×16 (see structural requant). |
| MAC accumulators | signed INT32 main + signed 25-bit group partial | Group partial folds into main at group boundaries, round-half-up. |
| KV data | signed INT4, 8 elements = 4 B per (layer,kv-head,pos) | K and V separately. |
| KV scales | unsigned INT16, Q4.12, **power of two** | `scale = 1<<(s+9)`, `s = max(0, msb(amax)-2)`, `s ∈ 0..5`; never enters the MAC array. |
| RMSNorm gains | signed INT16, Q2.14 | 11 vectors of 64 in VECBUF. |
| RoPE cos/sin | signed INT16, Q2.14 | Two 8 B vectors per position (cos then sin), packed two positions per 32 B WBUF word; 512 positions. |
| Softmax exp output | Q0.7 (unsigned) | 129-entry LUT, input domain z ∈ [-128, 0] in steps of 1/16. |
| Sigmoid output | Q0.15 (unsigned) | 129-entry LUT, input domain |x| ∈ [0, 128] in steps of 1/16. |
| Requant entry | 8 B word: `[31:0]` signed INT32 mult, `[39:32]` unsigned 8-bit shift, `[63:40]` zero | 37 slots in VECBUF; slots 35 and 36 are reserved. |

Exact shared primitives:

```text
sat8(v) = clamp(v, -128, 127)
sat4(v) = clamp(v,   -8,   7)
">>>"   = arithmetic (sign-preserving) right shift
```

**Rounding rule (exact RTL behavior):** every cross-domain shift in the design is **round-half-up** — `(v + 2^(n-1)) >>> n` — except the documented softmax z-domain downshift `>>> sm_shift`. KV append, the MVM INT8 requant writeback, the fused-attention `p'` fold, and final attention requant all use round-half-up. (Round-half-up in the MAC group fold specifically removed a systematic negative-floor bias that collapsed the full chain — see the design story in `architecture.md`.)

## Functional Blocks

| Block | Responsibility |
|---|---|
| Memory-mapped frontend / regs | CSR decode (incl. `GEN_CFG.sm_shift`), buffer windows, CTRL/STATUS/token/perf registers, `irq`, `mm_error` responses, start/soft-reset pulses. |
| Core sequencer | 20 executed token states plus two reserved legacy state encodings; all SPM address generation; GQA KV-head mux (`kvh = head[2:1]`); MVM/attention configuration; chain feedback; CTX_OVERFLOW detection. |
| MVM engine + MAC array | 8×8 = 64 signed MAC/cycle; tile/KV weight source select; fused group dequantization (round-half-up); three writeback modes (INT8 requant / raw INT32 / streaming argmax); per-block accumulator-clear beat. |
| Fused attention | Eight positions per tile; parallel K-data/K-scale read, two-pass max/exp, alternating V accumulation, local 32-iteration reciprocal, one final INT8 head write. SCORE/PR never spill to ACTBUF. |
| SFU | Core-invoked ops: EMBED, RMSNORM, ROPE, SWIGLU, RESADD, KVAPPEND; shared isqrt (4 iterations/cycle, 4 cycles) and restoring divider (2 iterations/cycle, 16 cycles = 32 iterations); sigmoid LUT. The legacy SOFTMAX opcode is not sequenced. |
| SPM | WBUF 4,736×256b (weight, scale, and W8-upper-half read banks), KVBUF 3,968×256b (data/V-transpose plus independent scale read), ACTBUF 512×64b, VECBUF 1,024×64b behavioral arrays. |

## Operation

Host sequence (contract details in `interface_spec.md`):

1. Write WBUF: weight tile region in checkpoint tensor order, then the scale region and the 512-position RoPE table.
2. Write VECBUF: RMSNorm gains and structural requant slots 0..34; slots 35 and 36 are reserved.
3. Write `TOKEN_IN` = BOS (1), `GEN_CFG.gen_len_m1` and `GEN_CFG.sm_shift` (2 for the calibrated mixed-W4/W8 image default).
4. Write `CTRL.start` (keeping `irq_en`/`chain_en` at the intended values — every CTRL write rewrites both). `STATUS.busy` rises after acceptance. A start written while `busy=1` is rejected with `mm_error=1` (`BUSY_START`) and does **not** disturb the active run.
5. Per generated token: `TOKEN_OUT` updates, `STATUS.token_valid` sets (W1C), `TOKEN_CNT` and `SEQ_POS` increment. With `chain_en=1`, the token feeds back automatically until `gen_len_m1 + 1` tokens complete. `gen_len_m1` can request at most 512 tokens, exactly matching the 512-entry context; `SEQ_POS` therefore reaches 512 after a full-length successful run.
6. `STATUS.done` sets at successful run end. `irq` reflects `irq_en && (done || error || token_valid)`. Host reads `CYCLE_*`, `MAC_*`, `TOKEN_CNT` and computes tokens/s = `TOKEN_CNT × f_clk / CYCLE`.

`SEQ_POS` resets to 0 on every accepted start: each run begins a fresh context at position 0, and `SEQ_POS` reports the context length within the current run. There is no cross-run context continuation.

## Fixed-Point Definitions of SFU Operations

All formulas below match `stories260k_sfu.v` operation-for-operation. `rnd(v,n) = (v + 2^(n-1)) >>> n` (round-half-up) is written out explicitly. Internal loops process 8 elements (one ACTBUF word) per step unless noted.

### EMBED

Reads the token's embedding row out of the 8×8 tile region and dequantizes it onto the ×8 residual grid (the embedding's group scales carry the `k_x = 3` bump):

```text
escale = emb_scale_unit[token / 8].row[token % 8]        # INT16 Q4.12 (16 rows per 32 B scale word)
for k0 in 0..7 (8 tile words):
  for l in 0..7:
    w4   = signed4(tile[token/8][k0].row[token%8].nibble[l])
    x[8*k0 + l] = sat8( (w4 * escale + 2048) >>> 12 )    # round-half-up
```

### RMSNORM (gain, no mean subtraction)

Input `x[0..63]` INT8, gain `g[0..63]` Q2.14:

```text
sumsq = sum_i( x[i] * x[i] )                  # signed sq8 per word; <= 64 * 16384 = 2^20
root  = isqrt(sumsq)                          # 16 iterations, 4 per cycle = 4 cycles; floor integer root
den   = (root == 0) ? 1 : root
inv   = min( floor(131072 / den), 16383 )     # restoring divider: 32 iterations, 2 per cycle = 16 cycles;
                                              # 32 iterations are required for the exact quotient
                                              # (26 would return quotient >> 6)
y[i]  = sat8( ( ((x[i]*g[i] + 8192) >>> 14) * inv + 1024 ) >>> 11 )
```

The mean factor of RMSNorm proper (`1/64`) is not divided in hardware; the resulting constant scale factor is absorbed by the ×8 grid analysis and the structural requant table.

### ROPE (q/k only, adjacent pairs)

Processes 12 words: 8 words of `q` then 4 words of `kt` (kv_dim = 32). Per word, pairs `(a, b) = (elem[2i], elem[2i+1])`, `i = 0..3`; position `pos`; tables `cosw = COS[pos]`, `sinw = SIN[pos]` (pair `i` at bits `[16i +: 16]`, Q2.14; pair frequency `10000^(-2i/8)`, `theta = pos × freq`):

```text
a' = sat8( (a*cos_i - b*sin_i + 8192) >>> 14 )
b' = sat8( (a*sin_i + b*cos_i + 8192) >>> 14 )
```

`v` is untouched. The attention `1/sqrt(HEAD_DIM)` factor is folded into each layer's `q` requant slot (mult 5793, shift 14 — `5793 = round(2^14/√8)`), so no runtime score scale exists.

### FUSED ATTENTION (per query head, eight positions per tile)

Inputs are query `q[0..7]`, selected-head INT4 K/V tiles, their per-position Q4.12 scales, and `sm_shift = GEN_CFG[20:17]` (0..15, default 2). K data and K scale are read together. The engine never materializes scores or probabilities in ACTBUF:

```text
# pass 1: one tile/cycle, K-scale folding + running max
for t in 0..pos:
  score[t] = sum_j(q[j] * K4[t][j])
  s[t] = (score[t] * sk[t] + 1024) >>> 11
  smax = max(smax, s[t])
# pass 2: alternating K/exp and V-accumulate beats per tile
for t in 0..pos:
  z    = clamp((s[t] - smax) >>> sm_shift, -128, 0)   # truncating shift into the 1/16 exp domain
  e    = EXP_LUT[z + 128]                     # 129 entries, Q0.7
  p'[t] = sat8( (e * sv[t] + 16384) >>> 15 )  # V scale folded into softmax output (round-half-up)
  av[j] += p'[t] * V4[t][j]
  sum_exp += e
recip = floor( 2^28 / max(sum_exp, 1) )       # 32-iteration restoring divider; att lands on the x8 grid
att[j] = sat8((av[j] * recip + 2^21) >>> 22)
```

Tail lanes above `pos` are masked. `1/sum_exp` is applied once after the V product, mathematically identical to per-position division (FlashAttention identity). The result is the only ACTBUF write for the head. Requant slot 35 remains reserved. `sm_shift=2` is calibrated for the shipped mixed-W4/W8 image (see `fixed_point_model.py`).

### SWIGLU

Per element over 176 values (22 words):

```text
sg  = SIG_LUT[|x1|]                           # 129 entries, |x1| in 1/16 units, Q0.15
sg  = (x1 < 0) ? (32767 - sg) : sg            # symmetry sig(-a) = 32767 - sig(a)
t   = (x1 * sg + 16384) >>> 15                # silu(x1), round-half-up
hb3 = sat8( (t * x2 + 64) >>> 7 )
```

### RESADD

`x = sat8(x + y)` elementwise over 64 values (8 words), result written back to X. The residual stays INT8 on the ×8 grid.

### KVAPPEND (INT8 -> INT4 with power-of-two scale)

Per (layer, kv-head, pos), 8 elements `u[0..7]` (post-RoPE `k` from KT, or `v` from V); 4 KV heads per layer:

```text
amax  = max_j |u[j]|                          # 8-bit magnitude; |-128| counts as 128
s     = max(0, msb7(amax) - 2)                # msb7 = index of highest set bit, 0..7; s in 0..5 used
scale = 1 << (s + 9)                          # INT16 Q4.12, power of two (LUT: 0x0200,0x0400,...,0x4000)
u4[j] = sat4( (u[j] + (s ? 2^(s-1) : 0)) >>> s )  # signed round-half-up
```

The 8 nibbles (4 B) and the 2 B scale are appended at `(layer, kv-head, pos)` per the KVBUF layout. Dequantization never touches the shared MVM array: `sk` folds into the fused-attention score (`>>>11`), `sv` folds into `p'` (`>>>15`).

## MVM Engine Semantics

### Array and tile geometry

- 8 output rows per block × 8 K-lanes = 64 signed MACs per cycle; one 256-bit weight word feeds exactly one cycle. An explicit clear beat (`MV_CLR`) resets the accumulators before each row block's K sweep.
- W4 weights are stored **8×8-tile interleaved**: tile word `(m0, k0)` at `wbase + m0×kwords + k0` covers rows `8·m0 .. 8·m0+7` and K elements `8·k0 .. 8·k0+7`. Within a word, row `r` occupies 32-bit lane `r`; within a lane, element `k0·8+l` occupies nibble `l`. INT4 nibbles are sign-extended to 8 bits at the array input.
- Layer-1 WQ uses the same tile address/order but INT8 values: rows 0..3 occupy four 64-bit lanes in the normal word, and rows 4..7 occupy the corresponding word at `4630 + m0×8 + k0`. Two simultaneous 256-bit reads reconstruct the 8×8 INT8 tile without adding a MAC cycle.
- Scale storage: 16 B unit per `(m0, group)` = 8 rows × INT16 Q4.12, at unit index `sbase + m0×gpr + g` (`gpr` = groups per row: 1 for K ≤ 64; 3 for K = 176, covering 64+64+48). One 32 B scale word holds two units (low/high 128-bit half selected by unit index bit 0).
- Output tensors process in row blocks of 8 (`mblocks = ceil(M/8)`). Partial blocks (M = 172 → 22 blocks with 4 valid rows in the last; M = 32 → 4 exact blocks) use rows-valid byte write strobes; padded weight rows/nibbles are zero.

### Weight source select (`wsel`)

| `wsel` | Source | Use |
|---:|---|---|
| 0 | WBUF tile word | All weight-tensor matmuls (QKV, WO, W1, W2, W3, logits). |
| 1 | KVBUF direct read | Reserved legacy MVM source; fused attention reads KV directly. |
| 2 | KVBUF nibble-transposed read | Reserved legacy MVM source; fused attention reads KV directly. |

### Fused dequantization (exact semantics)

Per row, per cycle: `dotsum = Σ_{l=0..7} signed8(w_l) × signed8(x_l)` (≤ 21 bits signed) accumulates into a signed 25-bit group partial `part`. On the last cycle of each 64-element group (every 8th MAC cycle, or the final K cycle):

```text
main += ((part + dotsum) * scale + 2048) >>> 12   # round-half-up; result taken as 32 bits
part  = 0
```

`scale_en = 0` forces `scale = 0x1000` (1.0 in Q4.12) — the bypass used by the KV passes so raw dot sums land in the accumulator unchanged. There is no standalone dequantized weight tensor anywhere; scales multiply group partials at group boundaries inside the accumulator path.

### Writeback modes (`ymode`)

| `ymode` | Behavior | Use |
|---:|---|---|
| 0 | INT8 requant: `y_r = sat8((acc_r × mult + rnd) >>> shift)` with `rnd = (shift==0) ? 0 : 1<<(shift-1)`; `mult`/`shift` from VECBUF rq slot; 8 lanes/word, rows-valid strobes. | QKV, WO, W1, W3, W2. |
| 1 | Raw INT32: accumulators written 2 rows per ACTBUF word over 4 sub-word beats, rows-valid strobes. | Reserved legacy mode. |
| 2 | Streaming argmax over signed INT32 accumulators; no buffer writeback. | Logits. |

Argmax tie rules (exact): comparisons are strict `>` both within and across 8-row blocks, so the **lowest token index wins globally**, matching Python/NumPy's first-maximum rule. Comparison uses raw signed INT32 accumulators — requant plays no role, and no logits vector is stored.

### Structural requant table (no data calibration)

The requant slots are fixed constants derived from the fixed-point grid analysis (see `fixed_point_model.py`), not from activation statistics:

| Slot(s) | mult | shift | Meaning |
|---|---:|---:|---|
| `7l+0` (q) | 5793 | 14 | ×8 grid × `1/√8` fold: `5793 = round(2^14/√8)`. |
| `7l+1` (k), `7l+2` (v), `7l+3` (wo) | 1 | 0 | ×8 grid passthrough. |
| `7l+4` (w1), `7l+6` (w3) | 2 | 0 | Land on the SwiGLU ×16 input grid. |
| `7l+5` (w2) | 4 | 0 | ×2 accumulator → ×8 output grid. |
| 35 | 1 | 16 | Reserved legacy attention slot; fused attention owns its local reciprocal. |
| 36 | 1 | 8 | Reserved (placeholder value). |

### Special passes

- **Fused attention**: one invocation per query head per layer, `T=ceil((pos+1)/8)` tiles. Schedule is one Q-load beat, `T` max beats, `2T` exp/V beats, 16 divider beats, one write, and one done beat. K/V scale and data accesses are independent; only `ATT[h]` is written.
- **Logits + argmax**: `M = 512`, `K = 64`, `wsel=0` over the embedding tiles with embedding scales enabled, `ymode=2`.

## Buffer Layouts

Offsets are window-relative bytes. Word-index formulas are authoritative in RTL; byte offsets are given for host software.

### WBUF (148 KiB window = 4,736 × 32 B words; usage 150,208 B = 4,694 words)

Weight tile region (strict llama2.c checkpoint tensor order):

| Offset | Words | Tensor (tile words: `mblocks × kwords`) |
|---:|---:|---|
| `0x00000` | 512 | `token_embedding` 512×64 (64×8) |
| `0x04000 + l×0x5A00` | +0 | layer `l` `wq` 64×64 (8×8) |
| `+0x0800` | +64 | `wk` 32×64 (4×8) |
| `+0x0C00` | +96 | `wv` 32×64 (4×8) |
| `+0x1000` | +128 | `wo` 64×64 (8×8) |
| `+0x1800` | +192 | `w1` 172×64 → 176 padded rows (22×8) |
| `+0x2E00` | +368 | `w2` 64×176 padded K (8×22) |
| `+0x4400` | +544 | `w3` 172×64 → 176 padded rows (22×8) |

Layer tile stride = 720 words = 23,040 B (`0x5A00`); the baseline tile region ends at word 4,112 = `0x20200` (131,584 B). Layer-1 WQ's 64 normal words hold its INT8 rows 0..3 rather than INT4; INT8 rows 4..7 use 64 extension words at 4630..4693. Total weight storage is therefore 133,632 B.

Scale region (16 B units; one 32 B scale word = 2 units):

| Offset | Units | Scales |
|---:|---:|---|
| `0x20200` (word 4112) | 64 | embedding: 64 m-blocks × 1 group = 1,024 B (words 4112..4143) |
| `0x20600 + l×0x5C0` (word 4144 + l×46) | +0 | `wq` 8 units (128 B) |
| `+0x080` | +8 | `wk` 4 units (64 B) |
| `+0x0C0` | +12 | `wv` 4 units (64 B) |
| `+0x100` | +16 | `wo` 8 units (128 B) |
| `+0x180` | +24 | `w1` 22 units (352 B) |
| `+0x2E0` | +46 | `w2` 24 units (8 m-blocks × 3 groups; 384 B) |
| `+0x460` | +70 | `w3` 22 units (352 B) |

Layer scale stride = 92 units = 1,472 B (`0x5C0`); scale region totals 8,384 B and ends at `0x222C0` (139,968 B = 136.7 KiB).

The RoPE table immediately follows at word 4,374 (`0x222C0`). Each position occupies 16 B `{cos[63:0], sin[63:0]}`; positions `2n` and `2n+1` occupy the low and high 128-bit halves of WBUF word `4374+n`. The 512 positions consume 256 words (8,192 B), ending at word 4629. The layer-1 WQ INT8 upper halves occupy words 4630..4693. WBUF spare is 1,344 B (42 words, 4694..4735). RMSNorm gains and requant entries remain in VECBUF.

### KVBUF (124 KiB window = 3,968 × 32 B words; usage 122,880 B = 3,840 words)

Layer `l` base word = `l × 768` (24,576 B stride); 4 KV heads per layer, 512 positions:

| Word offset | Size | Contents |
|---:|---:|---|
| `+0` | 256 words (8,192 B) | K data: word `h×64 + t/8`; the 4 B lane `(t%8)×4` holds position `t`'s 8 nibbles (element `hd` at nibble `hd`), h = KV head 0..3 |
| `+256` | 128 words (4,096 B) | K scales: word `h×32 + t/16`; the 2 B lane `(t%16)×2` holds position `t`'s Q4.12 pow2 scale |
| `+384` | 256 words (8,192 B) | V data, same layout as K data (consumed directly by fused attention; the legacy transpose view remains internal) |
| `+640` | 128 words (4,096 B) | V scales, same layout as K scales |

Five layers use 3,840 words = 122,880 B (120 KiB); spare 128 words (4,096 B).

### ACTBUF (4 KiB window = 512 × 8 B words; usage 442 words = 3,536 B)

| Word | Words | Name | Format |
|---:|---:|---|---|
| 0 | 8 | `X` | residual stream (×8 grid), INT8×64 |
| 8 | 8 | `XB` | RMSNorm output / MVM operand, INT8×64 |
| 16 | 8 | `Q` | post-RoPE queries, INT8×64 (query head `h` = word 16+`h`) |
| 24 | 8 | `KT` | post-RoPE keys before append, INT8×32 used (kv head `h` = word 24+`h`) |
| 32 | 8 | `V` | values before append, INT8×32 used |
| 40 | 256 | `SCORE_RSVD` | Reserved legacy score area; fused attention does not access it. |
| 296 | 64 | `PR_RSVD` | Reserved legacy probability area; fused attention does not access it. |
| 360 | 8 | `ATT` | per-query-head attention outputs (head `h` = word 360+`h`), INT8×64 |
| 368 | 22 | `HB` | `w1` output (×16 grid), INT8 × 176 |
| 390 | 22 | `HB2` | `w3` output (×16 grid), INT8 × 176 |
| 412 | 22 | `HB3` | SwiGLU output, INT8 × 176 |
| 434 | 8 | `Y` | `wo`/`w2` output + residual addend, INT8×64 |

### VECBUF (8 KiB window = 1,024 × 8 B words; usage 213 words = 1,704 B)

| Words | Contents |
|---|---|
| 0..175 | RMSNorm gains: 11 entries × 16 words (64 × INT16 Q2.14, 4 per word); layer `l` att at word `l×32`, ffn at `l×32+16`, final at word 160 |
| 176..212 | Requant table, 37 slots × 8 B `{mult s32 @ [31:0], shift u8 @ [39:32]}` |

Requant slot order: layer `l` slots `7l+0=q`, `7l+1=k`, `7l+2=v`, `7l+3=wo`, `7l+4=w1`, `7l+5=w2`, `7l+6=w3` (slots 0..34); slots 35 and 36 are reserved. There is no logits storage anywhere (argmax is fused into the logits MVM writeback stream).

RoPE no longer consumes VECBUF space: the 512-position cos/sin table is packed into the WBUF spare region described above. This makes the gains, RoPE, and requant regions pairwise disjoint and preserves the original SRAM capacities and MMIO windows.

## Sequencer States

RTL state names (`stories260k_core`), in execution order:

| State | Engine | Description |
|---|---|---|
| `C_IDLE` | — | No run active; all host accesses accepted. Accepted legal start latches config, clears `SEQ_POS`/token counter, → `C_EMB`. |
| `C_EMB` | SFU EMBED | Dequantize embedding row of the current token into `X`. |
| `C_RMS1` | SFU RMSNORM | `XB = rmsnorm(X, att gain[l])`. |
| `C_QKV` | MVM ×3 | `wq` (M=64) / `wk` (M=32) / `wv` (M=32) passes (qkv_i = 0,1,2) → `Q`, `KT`, `V`. |
| `C_ROPE` | SFU ROPE | RoPE on `Q` (8 words) and `KT` (4 words) at `pos`. |
| `C_KVA` | SFU KVAPPEND | Quantize + append K/V at (layer, 4 KV heads, pos) with scales. |
| `C_SCORE` | Fused attention | Complete QK/max/exp/V/reciprocal pass for query head `h` vs KV head `h>>1` → `ATT[h]`; loops for heads 0..7. |
| `C_SM`, `C_AV` | — | Reserved legacy encodings; unreachable in v1.2. |
| `C_WO` | MVM | `wo(ATT)` → `Y`. |
| `C_RES1` | SFU RESADD | `X = sat8(X + Y)`. |
| `C_RMS2` | SFU RMSNORM | `XB = rmsnorm(X, ffn gain[l])`. |
| `C_W1` | MVM | `w1(XB)` → `HB` (M = 172). |
| `C_W3` | MVM | `w3(XB)` → `HB2` (M = 172). |
| `C_GLU` | SFU SWIGLU | `HB3 = swiglu(HB, HB2)` (176 elements). |
| `C_W2` | MVM | `w2(HB3)` → `Y` (K = 176). |
| `C_RES2` | SFU RESADD | `X = sat8(X + Y)`; layers 0..3 loop to `C_RMS1`, layer 4 → `C_RMSF`. |
| `C_RMSF` | SFU RMSNORM | `XB = rmsnorm(X, final gain)`. |
| `C_LOG` | MVM | Tied-embedding logits, M = 512, streaming argmax. |
| `C_TOK` | — | `TOKEN_OUT = argmax`; `token_valid`, `TOKEN_CNT`, `SEQ_POS` increment. Chain & tokens remain → context check (`pos == 511` → `C_ERR` with `CTX_OVERFLOW`) else `C_EMB`; otherwise → `C_FIN`. |
| `C_FIN` | — | Sets sticky `done`, returns to `C_IDLE`. |
| `C_ERR` | — | Sets sticky `error` + `ecode`, returns to `C_IDLE`. |

`STATUS.busy` is high in every state except `C_IDLE`. SFU ops and MVM passes each run to completion (`sfu_done`/`mv_done`) before the sequencer advances. `soft_reset` returns the sequencer, SFU, and MVM engine to idle immediately.

## Performance Counters

| Counter | Width | Semantics |
|---|---:|---|
| `CYCLE` (`CYCLE_LO/HI`) | 64 | Increments every `clk` cycle while `busy=1`. Wraps at 2^64. |
| `MAC` (`MAC_LO/HI`) | 64 | Increments by 64 per MVM run cycle and per fused-attention max/exp/V beat (logical 64-lane work, including padded lanes). Wraps at 2^64. |
| `TOKEN_CNT` | 32 | Increments per completed token. Wraps at 2^32. |

Counters are cleared by any aligned write to `PERF_CLR` and by `rst_n`/`CTRL.soft_reset`; an accepted start does not clear them, so hosts may accumulate across runs. Host throughput = `TOKEN_CNT × f_clk / CYCLE`.

Budget and measurement:

- **64 tokens:** 499,585 cycles = **12,810.6 token/s**, logical MAC utilization 59.6%; two-run deterministic and all 64 tokens exactly match the fixed-point golden prefix (`soc_sim-f580b5dc47aa4982a5409383c4b2f096`).
- **256 tokens:** 2,366,977 cycles = **10,815.5 token/s**, logical MAC utilization 65.9% (`soc_sim-92075320ba6e43f0acaf9c0f4497c3c2`).
- **512 tokens:** 5,716,993 cycles = **8,955.8 token/s**, logical MAC utilization 71.8% (`soc_sim-02b6825334eb41f69ce7ea93e99f5399`). Target ≥ 8,700 token/s: **met at the maximum context**.

## Error Behavior

Two disjoint error channels (exact RTL behavior):

**Host access errors** — reported only on the transfer (`mm_error=1`), never set sticky `STATUS.error`/`ecode`; the offending address and code are latched into `ERR_ADDR` (latest error wins):

| Code | Name | Condition |
|---:|---|---|
| 1 | `ALIGN` | CSR access with `mm_addr[1:0] != 0`. Buffer addresses do not check alignment (`mm_addr[1:0]` is ignored and aliases to the aligned word). |
| 2 | `RO_WRITE` | Write to a read-only CSR. |
| 3 | `BUSY_START` | `CTRL.start` written while `busy=1`; the active run is **not** aborted and no start occurs. |
| 5 | `INVALID_ADDR` | Address outside implemented CSR offsets and buffer windows. |

**Core run errors** — set sticky `STATUS.error` + `STATUS.ecode`, assert `irq` if enabled:

| `ecode` | Name | Condition |
|---:|---|---|
| 6 | `CTX_OVERFLOW` | Defensive core code for a request beyond the 512-entry context. The current 9-bit `gen_len_m1` cannot request more than 512 tokens, so a legal run does not produce this code. |

`STATUS.ecode` is a 4-bit readback of the last core error; it clears on an accepted start and on reset, not on STATUS W1C. Invalid host accesses never modify the targeted register or buffer location.

## Reset and Clear Behavior

`rst_n` (active-low asynchronous assert) and `CTRL.soft_reset` (synchronous pulse; preempts a same-write start) produce:

- CSR reset values per `regmap.md`; `busy/done/error/token_valid/ecode/irq` = 0; `SEQ_POS`, `TOKEN_CNT`, `CYCLE`, `MAC`, `ERR_ADDR` = 0; sequencer → `C_IDLE`; SFU and MVM engines → idle (including aborting any in-flight op).
- **Buffer contents are not reset-cleared.** The behavioral SPM arrays power up at zero (simulation `initial` block) and are host/core-managed afterwards; soft reset intentionally preserves loaded weight/table images. KV and ACT locations are always written by the engine before being read within a run, so stale bytes are never consumed.

Sticky clear rules: `done` W1C at `STATUS[1]`; `error` W1C at `STATUS[2]` (does not clear `ecode`/`ERR_ADDR`); `token_valid` W1C at `STATUS[8]`; `done`/`error`/`ecode` also clear on an accepted start; everything clears on reset/soft reset.

## Synthesis Constraints and Implementation Rules

- One clock `clk`; no generated clocks, clock gates, latches, vendor primitives, PLLs, or synchronizers inside the IP.
- `de/syn/stories260k.sdc` carries the 10 ns clock constraint for the 100 MHz target on the Nangate 45 nm open PDK; the file alone is not closure evidence. STA evidence comes from the registered soc_syn/OpenROAD flow.
- Keep arithmetic explicitly signed in RTL for INT4/INT8 operands, INT32 accumulation, signed requant, and saturation semantics; preserve round-half-up everywhere except the documented `sm_shift` z-domain shift.
- The SPM baseline is behavioral wide-word arrays with combinational reads and power-on zero init; no memory inference is claimed. The synchronous-macro replacement contract in `interface_spec.md` applies: registered read data, preserved port widths, host-managed initialization (no reset clear), and `mm_ready` backpressure rules.
- The 4 mm² / 1.46 M-cell / 0.277 MB-SRAM physical targets belong to the PD stage and must cite OpenROAD reports when claimed.

## Known Limitations and Accepted Error Budget

| Limitation | Rationale / bound |
|---|---|
| Residuals are INT8 on the ×8 grid (`sat8(x + y)`) | Keeps ACTBUF tiny; bounded by end-to-end legality/determinism checks and the fixed-point golden model, not bit-exactness vs float. |
| Text fidelity improves but remains below FP32 | Layer-1 WQ INT8 makes the opening six generated pieces match FP32 (`Once upon a time, there`), and all RTL tokens now match the fixed model. Later malformed subwords remain quantization/model-fidelity loss, not RTL/golden divergence; eliminating them requires a QAT/mixed-precision checkpoint or more precision, not another RTL rounding guess. |
| Truncating softmax z-domain shift | The sole documented exception to the round-half-up rule; controlled by calibrated `sm_shift=2`. |
| Power-of-two KV scales | At most 2× per-position quantization over/under-estimate vs optimal scale; shift-only append hardware. |
| RMSNorm without the 1/64 mean division, `1/√8` folded into the q slot | Constant factors absorbed by the structural requant table; the golden model matches operation-for-operation. |
| Context cap at 512 | Matches the checkpoint maximum. `gen_len_m1` is 9 bits, so one run cannot request a 513th token. |
| Greedy argmax only | No temperature/top-p sampling hardware. |
| One model, fixed geometry | Any checkpoint/config change reopens docs. |
| Behavioral SPM baseline (combinational read, no reset clear) | Macro replacement must preserve every host-visible rule in this spec and the interface spec. |

## Assumptions

- The local memory-mapped interface is little-endian.
- The upstream wrapper holds request signals stable until `mm_ready=1` and samples `mm_rdata`/`mm_error` in the cycle after acceptance.
- `rst_n` is distributed by the SoC with asynchronous assert and safe deassert relative to `clk`.
- The packer (`dv/tests/pack_stories260k.py`) owns conversion of `stories260K.bin` into WBUF/VECBUF images: per-64-group INT4 quantization except layer-1 WQ INT8, embedding scale bumped ×8 for the residual grid, zero K/M padding, split W8 tile packing, WBUF-resident Q2.14 RoPE tables, VECBUF gains, and structural requant constants.
- `dv/tests/fixed_point_model.py` is the bit-exact RTL-semantics golden model used for grid/`sm_shift` calibration and float-vs-fixed token-trace comparison. The real-image TB asserts its first 64 generated tokens.
- Software never relies on a fixed token cycle count; only the visible ordering (busy → token_valid per token → done) is architectural. (The measured cycle count is image-independent in practice, since no control flow is data-dependent.)
