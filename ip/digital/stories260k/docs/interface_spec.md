# stories260k Interface Specification

## Module Declaration

The top module is `stories260k` (implemented in `de/rtl/stories260k.v`). It has no compile-time capacity parameters; model geometry and buffer sizes are fixed by the design specification. `stories260k_spm` exposes internal word-count parameters (`WBUF_WORDS=4736`, `KV_WORDS=3968`, `ACT_WORDS=512`, `VEC_WORDS=1024`) that are not part of the public contract.

```verilog
module stories260k (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        mm_valid,
    input  wire        mm_write,
    input  wire [19:0] mm_addr,
    input  wire [31:0] mm_wdata,
    input  wire [3:0]  mm_wstrb,
    output reg  [31:0] mm_rdata,
    output wire        mm_ready,
    output reg         mm_error,
    output wire        irq
);
```

## Port Table

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | Input | 1 | Single IP clock. All host interface, register, sequencer, SPM, SFU, and datapath state is synchronous to this clock. |
| `rst_n` | Input | 1 | Active-low asynchronous reset. Resets CSR/sequencer/SFU/MVM/attention state; does not clear buffer contents. |
| `mm_valid` | Input | 1 | Host request valid. Inputs must remain stable while `mm_valid=1` and `mm_ready=0`. |
| `mm_write` | Input | 1 | Host request type. `1` selects write; `0` selects read. |
| `mm_addr` | Input | 20 | Local byte address inside the 1 MiB stories260k aperture. |
| `mm_wdata` | Input | 32 | Write data. Byte lane 0 is bits `[7:0]` … lane 3 is `[31:24]`. |
| `mm_wstrb` | Input | 4 | Write byte strobes. Used by buffer writes; **ignored for CSR writes**. Ignored for reads. |
| `mm_rdata` | Output | 32 | Read data, registered. Valid in the cycle after the accepting clock edge. |
| `mm_ready` | Output | 1 | Request acceptance, combinational. A transfer is accepted when `mm_valid && mm_ready` is high on a rising `clk` edge. |
| `mm_error` | Output | 1 | Registered one-transfer error response, valid in the same cycle as the corresponding `mm_rdata`. |
| `irq` | Output | 1 | Level interrupt: `CTRL.irq_en && (done || error || token_valid)`. |

## Clocking

`clk` is the only clock. There are no internal generated clocks and no clock-domain crossings inside `stories260k`. All state changes occur on the rising edge of `clk`, except hardware reset assertion through `rst_n`.

## Reset

`rst_n` is active-low asynchronous assert. When `rst_n=0`, the IP drives:

| Signal/state | Reset value |
|---|---|
| `mm_ready` | `1'b1` (combinational; no stall while idle) |
| `mm_error` | `1'b0` |
| `mm_rdata` | `32'h0000_0000` |
| `irq` | `1'b0` |
| Sequencer / SFU / MVM / attention | idle (soft reset also aborts any in-flight op) |
| Registers and performance counters | values listed in `regmap.md` (`ID`, `VERSION` nonzero) |
| Buffers (WBUF/KVBUF/ACTBUF/VECBUF) | **not cleared** — behavioral arrays power up at zero and preserve contents across resets |

Reset deassertion is assumed to meet SoC reset timing requirements. The IP does not include a reset synchronizer. `CTRL.soft_reset` is a synchronous pulse with the same architected effects (CSR + engines reset, buffers preserved) and preempts a start requested in the same CTRL write.

## Target Protocol

The host interface is a ready/valid local target protocol in the style of `npu`, with a registered response:

- The host presents one request with `mm_valid=1`.
- `mm_ready` is combinational: it is low **only** when the current request targets a buffer window while `STATUS.busy=1`. All other requests — including every CSR access during a run — are accepted immediately at the next rising edge.
- If `mm_ready=0`, the request has not been accepted and all request inputs must remain stable.
- **Response timing**: `mm_rdata` and `mm_error` are registered at the accepting edge and are valid in the cycle immediately after acceptance. They hold their values while a subsequent request is stalled, and return to zero in cycles with no accepted transfer and no stall.
- There are no bursts, protection bits, exclusive accesses, IDs, out-of-order responses, endian conversions, or split responses.

## Address Windows and Alignment Rules

| Region | Address range | Size | Access behavior |
|---|---:|---:|---|
| CSR | `0x00000-0x00FFF` (implemented offsets per `regmap.md`) | 4 KiB window | Word-aligned accesses only (`mm_addr[1:0] != 0` → `ALIGN` error). Read-only register writes → `RO_WRITE`. Write strobes ignored. |
| WBUF | `0x10000-0x34FFF` | 148 KiB (4,736 × 32 B words) | Byte scratchpad over 32-bit host transfers; `mm_addr[1:0]` ignored (aliases to the aligned word); lane `n` updates byte `{addr[4:0] div 4}×4+n` when `mm_wstrb[n]=1`. |
| KVBUF | `0x40000-0x5EFFF` | 124 KiB (3,968 × 32 B words) | Same. |
| ACTBUF | `0x60000-0x60FFF` | 4 KiB (512 × 8 B words) | Same. |
| VECBUF | `0x64000-0x65FFF` | 8 KiB (1,024 × 8 B words) | Same. |
| All other addresses | remainder of 1 MiB | — | `INVALID_ADDR`: `mm_error=1`, read data zero, no state change. |

Buffer windows are fully implemented up to their stated sizes (usage is smaller than the window; spare tails are ordinary scratchpad bytes). Host buffer reads return the aligned 32-bit word containing the addressed byte: `mm_rdata[8n +: 8] = buf[base + n]`.

## CSR Access Timing

CSR requests are never stalled. A CSR read accepted at edge N returns the registered value in cycle N+1; invalid offsets return `mm_error=1` and zero data in that cycle. CSR writes apply at the accepting edge: W1S pulses (`start`, `soft_reset`), W1C sticky clears (STATUS bits 1/2/8), and plain RW fields (`irq_en`, `chain_en`, `TOKEN_IN`, `GEN_CFG`).

Every CTRL write rewrites `irq_en` and `chain_en` from data bits `[2]`/`[3]` — a bare start pulse must be written with the desired enable bits set. Configuration writes while `busy=1` are accepted but affect only the next start; the run in progress uses the values latched at its start.

## Buffer Access Timing

When idle, buffer reads and writes are accepted in one cycle (registered read data the following cycle). When `STATUS.busy=1`, buffer requests see `mm_ready=0` and must be held; they complete under the idle rules once the run terminates. The internal sequencer owns the buffers during a run; this stall rule avoids undefined simultaneous host/compute access. A write with `mm_wstrb=4'b0000` is an accepted no-op.

## Host Loading Contract

The host must follow this order before the first start (buffer contents survive soft reset, so reload is needed only after power-up or image change):

1. **WBUF weights and tables** (`0x10000` upward): all tensors in strict checkpoint order, 8×8-tile interleaved per `design_spec.md`. All are W4 except layer-1 WQ: its rows 0..3 occupy the normal 64 tile words and rows 4..7 occupy WBUF words 4630..4693. Scales start at offset `0x20200`; the 512-position RoPE table starts at `0x222C0` and occupies words 4374..4629. Tile/scale padding is zero.
2. **VECBUF**: RMSNorm gains (words 0..175), then structural requant slots 0..34 (words 176..210; q = 5793/14, k/v/wo = 1/0, w1/w3 = 2/0, w2 = 4/0). Slots 35 and 36 are reserved.
3. **Run registers**: `TOKEN_IN` = BOS (1) or any prompt token id; `GEN_CFG.gen_len_m1` and `GEN_CFG.sm_shift` (2 for the calibrated mixed-W4/W8 image default).
4. **Start**: write `CTRL` with `start=1` plus the desired `irq_en`/`chain_en`. A start while `busy=1` fails with `BUSY_START` and does not disturb the run.

KVBUF and ACTBUF need no host initialization: the engine writes every byte it reads within a run. In simulation, images may also be loaded directly into the behavioral arrays via `$readmemh` (as the TB does with `+WIMAGE`/`+VIMAGE`); this is a testbench convenience, not a host contract.

## Token Handshake Semantics

- `STATUS.token_valid` sets when `TOKEN_OUT` updates at the end of each decode pass; it is W1C at `STATUS[8]`.
- `TOKEN_OUT[8:0]` holds the emitted token id (0..511) and remains stable until the next token completes.
- With `CTRL.chain_en=1` (latched at start), the emitted token feeds back internally as the next input until `gen_len_m1 + 1` tokens complete, regardless of how fast the host clears `token_valid`; host reads are observational only. The maximum request is 512 tokens and fills positions 0..511.
- With `chain_en=0`, exactly one token is produced per start.
- `TOKEN_CNT` counts completed tokens since the last clear; `SEQ_POS[9:0]` counts context entries within the current run (0..512, reset to 0 at each start).

## Interrupt Timing

`irq` is a level function of architectural state:

```text
irq = CTRL.irq_en && (STATUS.done || STATUS.error || STATUS.token_valid)
```

It asserts in the cycle after any source bit sets and deasserts once `irq_en` is cleared or all sticky sources are W1C-cleared. `token_valid` is an interrupt source (per-token notification in chained runs).

## Timing of Run Completion

The docs do not require a fixed token latency. A compliant implementation preserves the visible ordering:

- `busy` asserts after an accepted start; a start while busy is rejected (`BUSY_START`) without side effects.
- `TOKEN_OUT` and `token_valid` update only after the final logits block of that token has been reduced by argmax.
- `SEQ_POS` and `TOKEN_CNT` increment exactly once per emitted token.
- Final `done` sets after the last token of the run is visible in `TOKEN_OUT`; a `CTX_OVERFLOW` termination sets `error` instead of `done`.
- Performance counters reflect all cycles/MACs/tokens up to the completion point.

## Internal SPM Ports and Future SRAM Replacement Boundary

The behavioral baseline (`stories260k_spm`) implements four wide-word arrays with **combinational reads** and power-on zero initialization:

| Buffer | Array | Core ports |
|---|---|---|
| WBUF | `wbuf_mem[0:4735]`, 256 b | normal tile/RoPE read + scale read + WQ1 W8-upper-half read (three combinational logical reads) |
| KVBUF | `kv_mem[0:3967]`, 256 b | data read + independent scale read + nibble-transposed V view + 32-byte-strobe write port |
| ACTBUF | `act_mem[0:511]`, 64 b | combinational read + 8-byte-strobe write port |
| VECBUF | `vec_mem[0:1023]`, 64 b | combinational read + write port |

Host access is a 32-bit port with per-byte strobes, arbitrated above the core ports (the top level guarantees the host is stalled while the core is busy, so no contention exists).

A future synchronous-macro replacement must preserve the public interface and every host-visible rule, and in addition:

- Register read data (valid one cycle after the read request) while keeping the same port widths; the MVM/SFU/sequencer must pipeline addresses one cycle ahead of operand consumption and delay dependent writebacks/status accordingly.
- Provide host-managed initialization: macros have no reset clear, so the host must zero or reload contents after power-up. The documented contract "buffers are not reset-cleared" makes the behavioral baseline and a macro build indistinguishable from software.
- Reject out-of-range internal addresses before issuing a memory request, and preserve the busy-stall rule so host and core never contend.
- Preserve simultaneous WBUF normal/W8-upper/scale reads and KVBUF data/scale reads, plus the V nibble-transpose view. Banking or replication is an implementation choice, but it must not reduce the documented attention/MVM issue rate.

Any implementation that cannot preserve these rules must reopen the doc stage.

## Integration Notes

- A future APB/AHB wrapper must translate its protocol to this local target interface, preserve the registered-response timing, and honor the busy-stall wait states.
- A wrapper crossing clock domains must include CDC logic outside `stories260k`.
- SoC-level address decode and interrupt routing are external to this IP; the 20-bit local address is decoded internally against the window table above.
- Image generation is tooling scope (`dv/tests/pack_stories260k.py`); the IP consumes only already-packed WBUF/VECBUF contents.
