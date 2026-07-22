# stories260k Verification Plan

## Scope and Status

Verification covers the standalone `stories260k` IP defined by `design_spec.md`, `interface_spec.md`, and `regmap.md`: the fixed stories260K GQA dataflow, mixed-W4/W8 fused-dequant MAC array, fused attention, SFU operators, buffer layouts, CSR/token/perf contract, and error model.

**Status: the PoC suite is implemented and passing.** All runs execute through the registered `soc-build` MCP tools (`soc_comp`, `soc_sim`, `soc_regress`) under `pipeline_state.json` gating — local direct simulator invocation is out of contract. Measured evidence (VCS `soc_sim`):

| Claim | Evidence |
|---|---|
| T1–T4 PASS, 64-token fixed-model exactness, and two-run determinism | `soc_sim-f580b5dc47aa4982a5409383c4b2f096` |
| 64 tokens / 499,585 cycles = **12,810.6 tok/s**, logical MAC util 59.6% | same run |
| 256 tokens / 2,366,977 cycles = **10,815.5 tok/s**, logical MAC util 65.9% | `soc_sim-92075320ba6e43f0acaf9c0f4497c3c2` |
| 512 tokens / 5,716,993 cycles = **8,955.8 tok/s**, logical MAC util 71.8% | `soc_sim-02b6825334eb41f69ce7ea93e99f5399` |
| lint Verilator `-Wall` 0 warnings; Verilator compile PASS | latest lint/comp logs |
| Real-model token stream (tok512 detok) | see "Real-Model Fidelity" below |

Targets still **not** evidenced: 100 MHz timing closure (STA), 4 mm² / 1.46 M cells (synthesis/PD). Those belong to the soc_syn/OpenROAD stages and must not be claimed from simulation logs.

## v1.2 Delta Acceptance

The implemented v1.2 acceptance basis is:

1. First-divergence tracing compared RTL intermediate values with
   `fixed_point_model.py`; fixes included the golden conditional-expression
   bug, signed KV round-half-up, `p'`/attention/SwiGLU rounding, gain clamp,
   and lowest-index argmax tie behavior.
2. Every real-image run asserts the first 64 generated tokens against the
   fixed-model golden trajectory. This catches fused-attention, mixed-W8
   layout, rounding, and argmax drift end to end.
3. Real-image VCS chains at 64, 256, and 512 tokens pass token legality,
   exact token count, boundary-address, and ≥8,700-token/s checks. The default
   64-token case also proves two-run determinism; the long cases run once.
4. Registered synthesis and the complete OpenROAD flow must report setup and
   hold WNS/TNS and the exact constraint/report paths; an SDC file alone is
   not evidence.

## Testbench Model

`dv/tb/tb_stories260k.sv` provides:

- Clock/reset driver: 10 ns `clk` period (throughput numbers are quoted at 100 MHz), active-low `rst_n`.
- A local MMIO BFM (`mm_wr`/`mm_rd` tasks) honoring the registered response timing (data sampled the cycle after acceptance) and busy-stall rule.
- Hierarchical image loading: `$readmemh` directly into `u_dut.u_spm.wbuf_mem` / `vec_mem` when plusargs are present; MMIO-written fallback images otherwise.
- An SV golden model of the MAC (`mac_golden_step`) implementing the exact round-half-up fused-dequant semantics `(part + dotsum) × scale + 2048 >>> 12` with scale-bypass = 4096, compared against the RTL row accumulators after every trial.
- Hierarchical token capture with legality checking, first-64 fixed-model comparison for real images, CSR scoreboards, and a per-state cycle histogram.
- A global watchdog (200 ms sim time) that fails the run if the sequencer ever hangs.

## Weight Image Flow (real checkpoint)

1. Fetch the checkpoint. The direct HF download was blocked during the original run; the working path is the `hf-mirror.com` mirror with the correct subdirectory layout:

   ```bash
   wget https://hf-mirror.com/karpathy/tinystories/resolve/main/stories260K.bin
   ```

2. Pack images (structural requant, no numpy calibration needed):

   ```bash
   python3 dv/tests/pack_stories260k.py stories260K.bin dv/sim/img
   ```

   The packer parses the llama2.c export, quantizes all matrices to per-64-group INT4 except Design-B INT8 (L1 QKV+WO, L2 WQ+WO, L3 WQ), and emits fixed-capacity WBUF/VECBUF images (WBUF 5,024 words). INT8 rows 0..3 occupy normal tiles; rows 4..7 occupy WBUF words 4630..4821 (L1), 4822..4949 (L2 WQ/WO), 4950..5013 (L3 WQ). Structural requant slots are q=(5793,14), k/v/wo=(1,0), w1/w3=(2,0), w2=(4,0); slots 35/36 are reserved.

3. Run the TB through the registered MCP flow with plusargs injected via `USER_SIM_FLAGS`:

   ```text
   soc_sim(module=stories260k,
           USER_SIM_FLAGS="+WIMAGE=<abs>/dv/sim/img/wbuf.hex +VIMAGE=<abs>/dv/sim/img/vecbuf.hex")
   ```

4. **Fallback** (no plusargs): deterministic LFSR pseudo-random WBUF contents (xorshift32, seed `0x260C_0ACE`; scale words fixed to `0x0800`) plus MMIO-written WBUF RoPE tables and VECBUF gains/requant entries. Fallback runs check determinism, protocol, counters, and token legality only — never model accuracy.

## Directed Test Matrix (implemented, all passing)

| Test | Stimulus | Pass criteria |
|---|---|---|
| **T1** ID/VERSION | Read `ID` and `VERSION` after reset. | `ID = 0x5354_4F52`, `VERSION = 0x0001_0000`, no `mm_error`. |
| **T2** MAC unit | Dedicated `stories260k_mac` instance driven with xorshift-patterned operands: 1-step and 8-step trials with `scale_en=1`, 3-step trial with `scale_en=0` (bypass); SV golden model steps in lockstep per cycle. | All 8 row accumulators bit-equal the golden `(part + dotsum) × scale + 2048 >>> 12` semantics after every trial, including group-boundary fold and bypass = 4096. |
| **T3** full decode | Real or fallback buffers; RoPE positions 0/383/511 and bank tails; BOS, `SM_SHIFT=2`, chain lengths 64/256/512. | Exact token count/SEQ_POS, ids <512, no core error, T≥8,700 at each length. Real images assert first 64 fixed-model tokens. Default 64 mode repeats and compares the full stream; long modes reach position 255/511 once. |
| **T4** error injection | Read unmapped address `0x70000`; then re-read `ID`. | First read returns `mm_error=1`; CSR reads still work afterwards (`ID` correct, no error). |

## Real-Model Fidelity

Measured opening from the mixed-W4/W8 real-checkpoint run:

```text
 Once upon a time, there a ...
```

Float reference trajectory for the same BOS prompt:

```text
Once upon a time, there was a little girl named Lily...
```

Assessment (written as measured, no embellishment):

- The first six generated pieces match FP32: `Once upon a time, there`; token 6 then diverges (`a` versus FP32 `was`).
- RTL and the corrected fixed-point model match exactly for the asserted 64-token prefix. Thus remaining malformed subwords are W4A8/checkpoint fidelity, not an RTL-vs-golden arithmetic bug.
- Removing the later quality gap requires a QAT or higher-precision checkpoint/design trade-off. It is not justified to hide it with unverified rounding changes.
- The WBUF image must contain all 512 non-overlapping RoPE cos/sin entries at words 4374..4629; the TB checks positions 0, 383, and 511 before decode.

## Golden Model (`dv/tests/fixed_point_model.py`)

RTL-semantics numpy emulator used for numerics calibration and float-vs-fixed comparison:

```bash
python3 dv/tests/fixed_point_model.py stories260K.bin [steps]
```

Prints float and fixed-point traces for calibration. The shipped Design-B v1.7 configuration uses residual `k_x=3`, INT8 ops `wq1,wk1,wv1,wo1,wq2,wo2,wq3`, `sm_shift=1`, and decode frequency penalty 32. The model mirrors the hardware operation-for-operation, including signed KV round-half-up, fused attention, LUTs, restoring-divider reciprocal, saturation, lowest-index argmax, and token-frequency penalty.

## Assertions and Checks

Implemented as TB checks/scoreboards; recommended for conversion to SVA in the regression stage:

- `irq == irq_en && (done || error || token_valid)` after reset deassertion.
- `mm_error` is meaningful only in the cycle after an accepted transfer.
- `token_valid` sets only when `TOKEN_OUT` updates; exactly one `token_valid` per token; every token id < 512.
- `TOKEN_CNT` increments exactly with `token_valid`; `CYCLE` counts only busy cycles; `MAC` advances by ≤ 64 per cycle.
- A start while busy returns `mm_error=1` and does not perturb the run (no extra tokens, no state corruption).
- Determinism: identical images + identical start configuration produce identical token streams and identical `CYCLE` counts across runs (T3 compares streams; cycle equality holds in the measured logs).
- No X on `mm_rdata`, `mm_ready`, `mm_error`, `irq` after reset deassertion.

## Functional Coverage Goals

Regression-stage coverage targets (not all instrumented in the PoC TB):

- Sequencer: all executed `C_*` states, QKV three-pass loop, per-head fused `C_SCORE` loop, both `C_TOK` exits; legacy `C_SM/C_AV` are unreachable.
- MVM: W4 and WQ1 W8 paths, partial M=172 block, M=32 GQA passes, w2 three-group tail, INT8 requant, and lowest-index argmax.
- Fused attention/SFU: positions 0/7/8/255/511, masked tails, nonzero `sm_shift`, KV rounding rails, RMSNorm clamps, and sigmoid symmetry.
- CSR: every host error code (1 `ALIGN`, 2 `RO_WRITE`, 3 `BUSY_START`, 5 `INVALID_ADDR`); W1C on each sticky bit; `ERR_ADDR` latest-wins with `err_code`; `GEN_CFG.sm_shift` write/readback; `DEC_CFG` write/readback (`rep_pen`/`adapt_en`/`norep_win`); 10-bit `SEQ_POS` reaching 512.
- Chain modes: `chain_en` on/off × gen_len 1/many/512; boundary-address checks for position 511 and a full-length chain test in long regression.
- Argmax: max at first/middle/last block; lowest index wins ties within and across blocks.

## Pass and Fail Criteria

Pass criteria (met for T1–T4 as cited above; regressions must re-meet them):

- T1–T4 pass with zero `errors` and the `TB_STORIES260K PASSED` banner, run through the registered `soc-build` MCP flow.
- The T3 throughput print shows ≥ 8,700 tok/s; MAC-path checks (T2) are bit-exact.
- Real-image runs complete T3 with legality/throughput criteria and reproduce the fixed-model 64-token prefix; default mode also proves determinism.
- Assertions report zero failures; coverage goals hit or carry reviewed waivers.

Fail criteria:

- Any bit mismatch in MAC accumulators, token streams, counters, or CSR values; any SFU deviation beyond the documented LUT tolerance against the golden model.
- Any illegal token id, missing/duplicated `token_valid`, `TOKEN_CNT` drift, or determinism break.
- Any error injection that corrupts subsequent accesses; any hang (watchdog).
- Throughput below 8,700 tok/s without a documented design change and updated spec targets.
- Any run bypassing the registered MCP verification flow; any claim of frequency/area/PD closure or of prose-level text fidelity from current evidence.

## Verification Assumptions

- The BFM holds request signals stable while `mm_ready=0` and samples `mm_rdata`/`mm_error` in the cycle after acceptance, per the interface spec.
- The packer's layout constants are kept in sync with `de/rtl/stories260k_core.v` and `design_spec.md` by construction; a layout mismatch shows up as T3 determinism/legality failures on real images.
- LFSR fallback weights are statistically legal (positive scales, nonzero requant mults) but carry no model meaning; accuracy statements come only from `+WIMAGE`/`+VIMAGE` runs plus golden-model comparison.
- Throughput is measured at the TB clock of 10 ns; the 100 MHz frequency target itself is a synthesis/STA claim owned by the soc_syn/OpenROAD stages, not by simulation.
- Any RTL-driven interface change requires reopening this plan together with the doc set.
