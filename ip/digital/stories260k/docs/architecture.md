# stories260k Architecture Handoff

## Scope and Status

This document is the architecture handoff for the reusable digital IP `stories260k` under `ip/digital/stories260k`: a single-token-per-pass mixed-W4/W8 inference engine that executes the complete llama2.c TinyStories `stories260K` checkpoint (260,032 parameters, GQA 8 query heads / 4 KV heads) entirely from on-chip SRAM.

The implemented v1.2 delta is recorded in `design_spec.md`: fused tiled
attention, a parallel internal KV scale-bank read, round-half-up KV append,
global lowest-index argmax ties, layer-1 WQ INT8, and calibrated `sm_shift=2`.
It keeps the external interface, 512-token limit, 284 KiB aggregate SRAM
capacity, and host-visible windows unchanged. RTL/golden and 64/256/512 VCS
evidence is complete; synthesis/OpenROAD timing evidence is tracked separately.

The RTL baseline implementing this architecture exists under `de/rtl/` (`stories260k`, `stories260k_regs`, `stories260k_spm`, `stories260k_mac`, `stories260k_sfu`, `stories260k_attn`, `stories260k_core`, Verilog-2005) and is the authoritative source for all layout constants and operator semantics in this doc set. The PoC testbench (`dv/tb/tb_stories260k.sv`), checkpoint packer (`dv/tests/pack_stories260k.py`), and RTL-semantics fixed-point golden model (`dv/tests/fixed_point_model.py`) also exist. **Measured VCS `soc_sim` evidence exists for simulation-level claims**: T1–T4 pass, the first 64 real-image tokens are bit-exact to the fixed model, and maximum-context throughput is 8,955.8 tokens/s at 100 MHz (see Metrics).

The top module is `stories260k`. The local memory-mapped target interface uses the same ready/valid style protocol as the existing `npu` IP, widened to a 20-bit byte address (`mm_addr[19:0]`, 1 MiB aperture), with registered read-data/error responses. One clock `clk`, one active-low asynchronous reset `rst_n`.

## Provenance and Design Story

`stories260k` exists because of an experiment in self-reference. As an early concept proof, the Kimi K3 design agent set out to build a chip whose only workload is a nano language model built on K3's own architecture lineage: the open `stories260K` checkpoint from the llama2.c TinyStories ecosystem, a 5-layer, 64-wide GQA decoder-only transformer that generates coherent tiny stories one token at a time.

In a continuous 48-hour autonomous session, K3 performed the full construction loop itself — quantization scheme selection, microarchitecture design, RTL, verification, and physical build — using only open-source EDA tooling (the OpenROAD flow) and the open Nangate 45 nm PDK. No human edited the design during the run.

The run was not a straight line. The real checkpoint download initially failed until K3 re-derived the correct `hf-mirror.com` subdirectory path for `stories260K.bin`. The first silicon-realistic decodes produced degenerate token salad; K3 debugged its own numerics autonomously, and the fix list reads like a greatest-hits of fixed-point engineering: a restoring divider that needed all 32 iterations for the exact RMSNorm quotient (26 iterations silently returned `quotient >> 6`), a systematic negative-floor bias in the MAC group fold (fixed by round-half-up, `(part×scale + 2^11) >>> 12` — one of the two main causes of the full-chain collapse), stale scale-region base constants after a layout change, an unsigned `sq8` sum-of-squares helper, embedding-scale region constants, and the 8×8 WBUF tile interleave itself. Each fix moved the output closer to language, until the chip printed its first words: **"Once upon a"** — the same opening the floating-point model produces.

The design targets carried by that run, and their current evidence status:

| Metric | Value | Status |
|---|---|---|
| Simulated decode throughput | 12,810.6 / 10,815.5 / 8,955.8 tokens/s @ 100 MHz for 64 / 256 / 512 tokens | **Measured** (VCS `soc_sim`, T1–T4 PASS) — maximum context exceeds the ≥8,700 target |
| Real-model output | Opening six generated pieces match FP32: `Once upon a time, there`; deterministic fixed-model-exact 64-token stream | **Measured**; later malformed subwords remain quantization loss |
| Die area | 4 mm² | Target — OpenROAD evidence pending |
| Standard-cell count | 1.46 M | Target — synthesis evidence pending |
| On-chip SRAM | 0.277 MB (284 KiB, exact by construction) | Fixed by construction |
| Datapath | 8×8 INT4/INT8 MAC array with fused dequantization plus tiled fused attention | Implemented in RTL, T2/T3-verified |
| Frequency | 100 MHz timing closure (10 ns clock) | Target — SDC shipped, STA evidence pending |

The result is a chip designed by a model, for a model: the weight layout in WBUF is the llama2.c checkpoint tensor order rendered as 8×8 MAC tiles, the tokenizer vocabulary is hard-bound to the silicon, and the entire 512-position checkpoint context fits on die. The Metrics section marks, per number, what is fixed by construction, what is measured, and what remains a target.

## Knowledge-Base Evidence

- `github.com/karpathy/llama2.c` (model.c, `run.c`): defines the `stories260K` checkpoint — measured header `{dim, hidden_dim, n_layers, n_heads, n_kv_heads, vocab_size, seq_len} = {64, 172, 5, 8, 4, 512, 512}` — tensor order, shared classifier/embedding weights, RMSNorm pre-norm with gain, RoPE on q/k only, SwiGLU FFN, and greedy/argmax decoding. The chip context cap matches the checkpoint at 512 positions.
- Ainslie et al., "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints" (2023): grouped-query attention — the checkpoint uses 4 KV heads for 8 query heads (`kv_mul = 2`, `kv_dim = 32`); query head `h` attends KV head `h>>1`.
- `documents/integrated-circuit/Google/Quantization-and-Training-of-Neural-Networks-for-Efficient-Integer-Arithmetic-Only-Inference.pdf:page 4`: integer operands, signed INT32 accumulation, fixed-point multiplier with shift, saturating cast — the form of the stories260k requant path.
- AWQ (Lin et al., 2023): group-wise INT4 weight quantization with per-group scales preserves quality at 4 bits; motivates the 64-element group scale format.
- Su et al., "RoFormer" (2021): rotary embedding over adjacent pairs with base-10000 frequencies, q/k only.
- Zhang & Sennrich, "Root Mean Square Layer Normalization" (2019); Shazeer, "GLU Variants Improve Transformer" (2020): RMSNorm-with-gain and SwiGLU (`w1`/`w2`/`w3`), matching the checkpoint.
- Dao et al., "FlashAttention" (2022): running-max softmax with deferred denominator scaling; the attention SFU applies one reciprocal after the AV product.
- FreePDK45 / Nangate 45 nm open PDK and the OpenROAD project: process and toolchain assumptions behind the 100 MHz / 4 mm² / 1.46 M-cell physical targets.

## Selected IP Architecture

### Module Selection and Reuse

| Block | Selection | Source/reuse | Rationale | Risk/replacement |
|---|---|---|---|---|
| `stories260k` top | New in-house RTL IP (implemented) | `ip/digital/stories260k` | Single-purpose inference engine; one model, one fixed dataflow | Any model/config change requires reopening docs |
| Register/control target | Same ready/valid memory-mapped style as `npu` | In-house, protocol reused | Avoids binding the IP to APB/AHB/AXI; wrapper added later at SoC level | 20-bit address, registered response; wrappers must follow |
| SPM storage | Four software-loaded scratchpads (WBUF/KVBUF/ACTBUF/VECBUF), wide-word behavioral arrays with combinational reads | In-house, implemented | Whole model + full 512-position context on die; no external memory traffic at run time | Replace with synchronous SRAM macros per the interface-spec contract; macros must be host-initialized |
| Compute datapath | 8×8 signed MAC array, 64 MAC/cycle, fused group dequantization; W4 tiles plus split-row layer-1 WQ W8 tiles | In-house, implemented; T2-verified | One 256-bit read feeds W4; two logical WBUF reads feed W8 without extra cycles | A physical SRAM macro must provide the documented read banks |
| Fused attention | Eight-position K/V tiles, parallel scale/data reads, two-pass max/exp, local reciprocal, no SCORE/PR spill | In-house, implemented; T3-verified | Reduces full-context attention to 4,740 cycles/token | Exp LUT and fixed-point path are bit-exact to the golden model |
| Special-function unit | Core invokes EMBED, RMSNORM, ROPE, SWIGLU, RESADD, KVAPPEND; shared isqrt/divider and sigmoid LUT | In-house, implemented; T3-verified end-to-end | LUT-based fixed point keeps nonlinear ops on die | Legacy SOFTMAX opcode is no longer sequenced |
| Controller | Token sequencer FSM with fused per-head attention and GQA KV-head mux (`kvh = head>>1`) | In-house, implemented | Fixed model graph means no descriptor engine is needed | Microcode only if future model flexibility is approved |
| Host software | `dv/tests/pack_stories260k.py` (implemented): quantizes `stories260K.bin`, emits tile-interleaved WBUF/VECBUF hex images with **structural** requant values (no data calibration needed) | In-house tool | Guarantees WBUF layout equals the checkpoint tensor order in MAC tile form | Packer layout constants must stay in sync with RTL |
| Golden model | `dv/tests/fixed_point_model.py` (implemented): RTL-semantics numpy emulator used to calibrate the residual ×8 grid, structural requant, and `sm_shift`, and to print float-vs-fixed token traces | In-house tool | Operation-level mirror of every hardware formula in `design_spec.md` | Docs follow RTL for any ±1-LSB-level divergence |
| Verification | `dv/tb/tb_stories260k.sv`: T1 ID/VERSION, T2 MAC vs SV golden, T3 64/256/512 chained decode with ≥8,700-token/s assertion and 64-token fixed-model assertion, T4 error injection | In-house TB; **T1–T4 PASS measured** | Covers arithmetic/layout drift, determinism, maximum-context performance, and error model | Coverage widening is later-stage scope |

License/ownership assumption: all RTL and tooling is project-owned in-house code. The model checkpoint is the public llama2.c TinyStories `stories260K` artifact (fetched via the `hf-mirror.com` mirror path after the direct download was blocked); no third-party RTL or commercial NPU IP is selected.

### Functional Model

One host start command runs greedy autoregressive decode:

1. Host loads WBUF (W4 tiles, split WQ1 W8 tiles, group scales, and 512-position RoPE table) and VECBUF (RMSNorm gains + structural requant table), then writes the BOS token, generation length, `sm_shift`, and chain enable.
2. The sequencer embeds the token onto the ×8 residual grid, then runs 5 layers of {RMSNorm → QKV MVM → RoPE → KV append → per-query-head fused tiled attention against KV head `h>>1` → output-projection MVM → residual → RMSNorm → w1/w3 MVM → SwiGLU → w2 MVM → residual}.
3. A final RMSNorm feeds the logits MVM (tied embedding weights); argmax is fused into the logits MVM writeback stream, so no logits buffer exists anywhere.
4. The winning token id is written to `TOKEN_OUT` with `token_valid`; with chaining enabled it feeds back as the next input until `gen_len` tokens complete, up to the checkpoint maximum of 512.
5. Performance counters expose cycle/MAC/token counts; measured sustained throughput at 512 tokens is 8,955.8 tokens/s at 100 MHz.

This is not a programmable NPU, a training engine, an external-memory accelerator, or a multi-model runtime. It is a single-checkpoint engine whose entire state fits in 284 KiB of SRAM.

## Quantization Rationale

The architecture question was: can the complete model *and* the complete story context live on die in a ~0.28 MB SRAM budget? The arithmetic says INT4 weights plus INT4 KV cache is the sweet spot, and GQA halves the KV bill again.

Weights (every weight is touched exactly once per token):

| Representation | Weight bytes | Verdict |
|---|---:|---|
| FP32 | 260,032 × 4 = 1,040,128 B (0.99 MiB) | Impossible on die. |
| INT8 | 260,032 B (254 KiB) | Alone consumes 89% of total SRAM budget; no room for KV. |
| Mixed W4/W8 + per-64-group INT16 scales | 133,632 B weight data + 8,384 B scales = 142,016 B | All but layer-1 WQ use W4; WQ1 W8 adds 2,048 B. With the 8,192 B RoPE table, WBUF has 1,344 B spare. |

KV cache (full 512-position context, 5 layers, K and V, **GQA 4 KV heads**):

| Representation | KV bytes | Verdict |
|---|---:|---|
| FP32 | 5 × 2 × 4 × 512 × 8 × 4 = 655,360 B (640 KiB) | Larger than the whole SRAM budget. |
| INT8 | 163,840 B (160 KiB) | Does not fit KVBUF before adding scales. |
| INT4 + per-(layer,kv-head,pos) power-of-two INT16 scales | 122,880 B (120 KiB) | Fits KVBUF (124 KiB) with 4,096 B spare; K scale folds into the softmax input and V scale into the softmax output, so scales never enter the MAC array. Power-of-two scales make the append quantizer shift-only. |

Total: 146.7 KiB WBUF contents + 120 KiB KV + 3.5 KiB activations + 1.7 KiB vectors = 271.8 KiB used of 284 KiB provisioned. The residual stream and all activations stay INT8 and accumulators stay INT32, so no FP unit exists anywhere in the datapath. The known precision costs are enumerated in `design_spec.md`.

## Top-Level Partition

| Role | Responsibility |
|---|---|
| Memory-mapped frontend / regs (`stories260k_regs` + top decode) | CSR decode (incl. `GEN_CFG.sm_shift`), buffer windows, CTRL/STATUS/token/perf registers, `irq`, `mm_error` responses, start/soft-reset pulses. |
| Core sequencer (`stories260k_core`) | Token-level FSM: EMB → RMS1 → QKV → ROPE → KVA → per-head fused ATTN → WO → RES1 → RMS2 → W1 → W3 → GLU → W2 → RES2 (×5 layers) → RMSF → LOG → TOK → FIN/ERR. GQA mux: query head `h` addresses KV head `h>>1`. |
| MAC array (`stories260k_mac`) | 8 rows × 8 lanes = 64 signed MAC/cycle; per-row 25-bit group partial; at each 64-element group boundary the partial is multiplied by the row's Q4.12 scale and folded **round-half-up** into the INT32 main accumulator; scale bypass forces 1.0. |
| MVM engine (in `stories260k_core`) | Drives the MAC over 8-row blocks × K/8 cycles; W4/W8 select; INT8 requant and streaming lowest-index argmax writeback modes. |
| Fused attention (`stories260k_attn`) | K-score/max pass, K-exp/V-accumulate pass, local restoring-divider reciprocal, final INT8 head write; K/V scales fold locally. |
| SFU (`stories260k_sfu`) | EMBED, RMSNORM, ROPE, SWIGLU, RESADD, round-half-up KVAPPEND; shared isqrt/divider micro-engines. |
| SPM (`stories260k_spm`) | WBUF 4,736×256b with three logical reads, KVBUF 3,968×256b with data/scale/V-transpose views, ACTBUF 512×64b, VECBUF 1,024×64b; host byte-strobe port stalled while busy. |

```text
                     host (SoC bus wrapper)
                             |  mm_valid/write/addr/wdata/wstrb
                             |  mm_rdata/ready/error   (1 MiB aperture)
                             v
   +--------------------------------------------------------------+
   |                      stories260k (top)                       |
   |  +--------------------------------------------------------+  |
   |  | regs: CSR file | address decode | perf counters | irq  |  |
   |  +--------------------------------------------------------+  |
   |          | start/cfg                       ^ status/token  |
   |          v                                 |               |
   |  +--------------------------------------------------------+  |
   |  | core: embed -> 5x{fused-attn(GQA), ffn} -> logits      |  |
   |  | + MVM engine (8-row W4/W8 blocks) + fused attention    |  |
   |  +--------------------------------------------------------+  |
   |     |                 |                    |               |
   |     v                 v                    v               |
   | +-----------+  +--------------+  +-----------------------+  |
   | | mac 8x8   |  | sfu + attn   |  | spm                   |  |
   | | INT4/INT8 |  | rmsnorm/rope |  | WBUF  148KiB 256b words| |
   | | fused deq |  | tiled GQA    |  | KVBUF 124KiB 256b words| |
   | | rnd fold  |  | swiglu/embed |  | ACTBUF  4KiB  64b words| |
   | | int32 acc |  | isqrt/div    |  | VECBUF  8KiB  64b words| |
   | +-----------+  +--------------+  +-----------------------+  |
   +--------------------------------------------------------------+
                             |
                             v irq = irq_en & (done | error | token_valid)
```

Controller/datapath separation is preserved: the sequencer issues phase descriptors to the MVM engine and SFU and never shares arithmetic with them.

## SRAM Budget and Banking

| Buffer | Capacity | Used | Word geometry | Contents |
|---|---:|---:|---|---|
| WBUF | 148 KiB (151,552 B) | 150,208 B (146.7 KiB; 4,694 of 4,736 words) | 32 B words, 8×8-tile interleaved | Mixed-W4/W8 weight data 133,632 B + group scales 8,384 B + RoPE 8,192 B |
| KVBUF | 124 KiB (126,976 B) | 122,880 B (120 KiB; 3,840 of 3,968 words) | 32 B words | Per layer {K data, K scales, V data, V scales} × 4 GQA KV heads, 768-word layer stride |
| ACTBUF | 4 KiB (4,096 B) | 3,536 B address envelope (442 of 512 words) | 8 B words | x/xb/q/kt/v, reserved legacy SCORE/PR regions, att/hb/hb2/hb3/y |
| VECBUF | 8 KiB (8,192 B) | 1,704 B (213 of 1,024 words) | 8 B words | RMSNorm gains (176 words), requant table (37 slots) |
| **Total** | **284 KiB (290,816 B = 0.277 MB)** | 278,328 B (271.8 KiB) | | |

The baseline implements all four as behavioral wide-word arrays with combinational reads and power-on zero initialization (buffer contents are *not* cleared by `rst_n` or soft reset). The synchronous-macro replacement boundary, including host-side initialization duties, is defined in `interface_spec.md`.

## Interface Concept

| Signal | Dir | Width | Description |
|---|---|---:|---|
| `clk` | in | 1 | Single IP clock. |
| `rst_n` | in | 1 | Active-low asynchronous reset. |
| `mm_valid` | in | 1 | Host request valid. |
| `mm_write` | in | 1 | 1 = write, 0 = read. |
| `mm_addr` | in | 20 | Byte address within the 1 MiB local aperture. |
| `mm_wdata` | in | 32 | Write data. |
| `mm_wstrb` | in | 4 | Byte write strobes (buffer writes; ignored for CSR). |
| `mm_rdata` | out | 32 | Read data, registered; valid the cycle after acceptance. |
| `mm_ready` | out | 1 | Request acceptance (combinational; low only for buffer accesses while busy). |
| `mm_error` | out | 1 | Registered one-transfer error response, valid with the read data cycle. |
| `irq` | out | 1 | Level interrupt: `irq_en && (done || error || token_valid)`. |

Address windows: CSR `0x00000-0x00FFF`, WBUF `0x10000-0x34FFF`, KVBUF `0x40000-0x5EFFF`, ACTBUF `0x60000-0x60FFF`, VECBUF `0x64000-0x65FFF`; everything else is `INVALID_ADDR`. Full semantics in `interface_spec.md` and `regmap.md`.

## Clock, Reset, CDC, and RDC

- One clock domain, `clk`; no internally generated clocks, no clock gates, no latches.
- `rst_n` is asynchronous assert, active low; deassertion timing is an SoC integration assumption.
- No CDC exists inside the IP. A future bus wrapper crossing domains owns its CDC logic.
- `rst_n` and `CTRL.soft_reset` reset all CSR and engine state (SFU and MVM included). Buffer contents are not reset-cleared: the behavioral arrays power up at zero and are host/core-managed afterwards (a fresh story simply starts a new run at position 0; KV locations are written before they are read).

## Technology and Process Assumptions

| Topic | Architecture assumption |
|---|---|
| Process/node | Nangate 45 nm open PDK (FreePDK45) is the target technology for the physical build; RTL is portable Verilog-2005. |
| Standard cells | Generic synchronous logic; target 1.46 M cells in 4 mm². No vendor primitives in RTL. |
| Memories | Behavioral wide-word scratchpad arrays (implemented); synchronous macro replacement at synthesis/PD per the documented contract, with host initialization. |
| Clocks | One input clock `clk`, 10 ns constraint in `de/syn/stories260k.sdc`; 100 MHz closure is the target. |
| Reset | One active-low asynchronous reset `rst_n`. |
| Voltage/power | One digital voltage domain; clock-enable activity reduction only; no isolation/retention. |
| Toolchain | Open-source flow only: OpenROAD-flow-scripts for synth/PD handoff under `pd/openroad`, per the design story. Simulation evidence so far is VCS-based via the registered `soc-build` MCP flow; lint/compile also pass under Verilator. |
| Timing target | 100 MHz at the SoC-selected corner set; numeric closure claims remain blocked until soc_syn/OpenROAD evidence exists. |

## Metrics: Measured vs Targets

| Metric | Value | Status |
|---|---:|---|
| Parameter count | 260,032 | Fixed by construction (emb 32,768 + rms_att 320 + wq 20,480 + wk/wv 20,480 + wo 20,480 + rms_ffn 320 + w1/w3 110,080 + w2 55,040 + rms_final 64; classifier tied to embedding). Verified against the measured checkpoint header and the packer. |
| SRAM total | 290,816 B = 284 KiB = 0.277 MB | Fixed by construction (buffer capacities in RTL). |
| WBUF / KVBUF usage | 150,208 B / 122,880 B | Fixed by construction (layout constants in RTL, TB, and packer agree). |
| MAC throughput | 64 MAC/cycle, 6.4 GMAC/s @ 100 MHz | Implemented; T2 bit-exact vs SV golden. |
| Ideal compute | ≈ 9,200 cycles/token at full 512-token context | Analytic bound (259,328 useful matmul MACs + ≤ 5×8×512×8×2 = 327,680 attention MACs over 64 lanes). Not a measurement. |
| Decode throughput | **12,810.6 / 10,815.5 / 8,955.8 tokens/s** for 64 / 256 / 512 tokens | **Measured** — real-checkpoint VCS runs; 512 uses 5,716,993 cycles and meets ≥8,700. |
| Whole-TB result | T1–T4 PASS, run-to-run determinism | **Measured** (same runs). |
| Real-model token stream | Opening `Once upon a time, there` matches FP32; later text contains malformed subwords | **Measured** — RTL first 64 tokens exactly match the fixed-point model; residual gap is fixed-vs-FP32 quantization fidelity. |
| lint / compile | Verilator `-Wall` 0 warnings; Verilator compile PASS | Measured (latest logs). |
| Frequency | 100 MHz | Target — SDC shipped (`de/syn/stories260k.sdc`), STA evidence pending. |
| Die area / cell count | 4 mm² / 1.46 M cells | Target — OpenROAD reports pending. |

**Fidelity statement:** current VCS evidence proves the 512-entry layout, deterministic decode, legal counters/error behavior, maximum-context throughput, and exact agreement with the fixed-point model for the asserted 64-token prefix. Layer-1 WQ INT8 improves the FP32 prefix match to six generated pieces. It does not make the W4A8 model FP32-equivalent; later malformed subwords require a QAT or higher-precision checkpoint/design trade-off.

No synthesis, STA, or PD report is claimed by this doc set. Any downstream claim must cite its own fresh evidence.

## DFT, Verification, and Synthesis Assumptions

DFT:

- Scan-friendly synchronous state elements; no latches, generated clocks, or combinational feedback.
- SPM arrays must be replaceable by scan-excluded SRAM macros with MBIST hooks if the SoC selects compilers.

Verification:

- Implemented and measured TB suite: T1 ID/VERSION, T2 MAC-unit directed tests, T3 full-chain 64/256/512 decode with token legality/counters, 64-token fixed-model exactness, default two-run determinism, and ≥8,700-token/s checks at every tested length, plus T4 MMIO error injection. Full plan in `verification_plan.md`.

Synthesis:

- `de/syn/stories260k.sdc` provides the 10 ns clock constraint (the file itself is not closure evidence). Synthesis and STA evidence are produced later through the registered `soc-build`/soc_syn flow.

## SoC Integration Plan

1. Doc set (this file, `design_spec.md`, `interface_spec.md`, `regmap.md`, `verification_plan.md`) — maintained in sync with the RTL baseline.
2. RTL under `de/rtl/` — implemented; any interface-affecting change reopens docs.
3. Standalone IP verification through the registered `soc-build` MCP flow (`soc_sim`/`soc_regress`) — T1–T4 evidence collected; regression widening (coverage, CTX_OVERFLOW long-chain test) remains.
4. Synthesize through the registered flow with `de/syn/stories260k.sdc`; collect STA evidence against the 100 MHz target.
5. Run the OpenROAD handoff under `pd/openroad` for the 4 mm² / 1.46 M-cell physical targets.
6. Later SoC integration wraps the target interface (APB/AHB), owns address decode, interrupt routing, and any CDC.

The IP does not create CRG, top integration logic, bus fabric, external DMA, or chip-level address map entries in this architecture step.

## Assumptions, Risks, and Blockers

Approved assumptions:

- Reusable digital IP at `ip/digital/stories260k`, top module `stories260k`, Verilog-2005, single `clk`, active-low asynchronous `rst_n`.
- Same local memory-mapped target style as `npu`, widened to `mm_addr[19:0]`, with registered read-data/error responses.
- One fixed model: llama2.c `stories260K` (DIM=64, HID=172, NLAYERS=5, 8 q-heads, 4 KV heads GQA, HEAD_DIM=8, VLEN=512; checkpoint and chip context cap 512). Greedy argmax decode only.
- Whole-model on-chip storage; host loads weights/tables once; no runtime external memory.

Blockers for downstream stages:

- Synthesis and PD evidence do not exist; frequency/area/cell-count remain blocked from completion claims until soc_syn/OpenROAD stages produce fresh evidence.
- The model geometry is hard-bound. Any change to checkpoint, tokenizer, or context length reopens this architecture.
- SRAM macro selection, MBIST, and scan stitching are not selected; binding a macro requires the interface-spec replacement contract and re-verification.

Unresolved non-blocking risks:

- Text fidelity beyond the FP32-matching opening remains fragment-level; the RTL/fixed mismatch is closed, while fixed/FP32 quality is a checkpoint/QAT precision issue.
- RoPE plus WQ1 INT8 leaves 1,344 B in WBUF; KVBUF leaves 4,096 B. Any future context or precision growth must reopen the memory layout.
- LUT-based SFU approximations (exp, sigmoid) carry small quantization error, bounded by the fixed-point golden model comparison.
- Behavioral SPM arrays at 284 KiB are simulation-heavy; long tests load images via `$readmemh` (as T3 does).
