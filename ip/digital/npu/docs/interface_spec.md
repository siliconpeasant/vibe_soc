# npu Interface Specification

## Module Declaration

The top module is `npu`. NPU v2 phase 1 adds four compile-time capacity parameters. The public port list, register offsets, and fixed scratchpad apertures are unchanged.

```verilog
module npu #(
    parameter integer ACT_SPM_BYTES  = 64,
    parameter integer WGT_SPM_BYTES  = 64,
    parameter integer OUT_SPM_BYTES  = 64,
    parameter integer BIAS_SPM_WORDS = 16
) (
    input         clk,
    input         rst_n,
    input         mm_valid,
    input         mm_write,
    input  [15:0] mm_addr,
    input  [31:0] mm_wdata,
    input  [3:0]  mm_wstrb,
    output [31:0] mm_rdata,
    output        mm_ready,
    output        mm_error,
    output        irq
);
```

## Parameter Table

| Parameter | Type | Default | Legal values | Description |
|---|---|---:|---:|---|
| `ACT_SPM_BYTES` | Integer | 64 | 4..64, multiple of 4 | Implemented activation-byte prefix in the fixed `0x0100-0x013f` aperture. |
| `WGT_SPM_BYTES` | Integer | 64 | 4..64, multiple of 4 | Implemented weight-byte prefix in the fixed `0x0200-0x023f` aperture. |
| `OUT_SPM_BYTES` | Integer | 64 | 4..64, multiple of 4 | Implemented output-byte prefix in the fixed `0x0300-0x033f` aperture. |
| `BIAS_SPM_WORDS` | Integer | 16 | 1..16 | Implemented signed INT32-word prefix in the fixed `0x0400-0x043f` aperture. |

Illegal parameter values are integration/elaboration errors and need not produce a runtime `ERR_CODE`. All implemented byte capacities are word aligned. Because aperture bases and maximum extents are fixed, legal parameters cannot overlap address regions. The defaults exactly preserve 64-byte activation, weight, and output storage plus 16 bias words.

## Port Table

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | Input | 1 | Single NPU clock. All host interface, register, controller, scratchpad, quantization, and datapath state is synchronous to this clock. |
| `rst_n` | Input | 1 | Active-low asynchronous reset. Assertion immediately resets externally visible state; deassertion must be safe relative to `clk` at SoC integration. |
| `mm_valid` | Input | 1 | Host request valid. Inputs must remain stable while `mm_valid=1` and `mm_ready=0`. |
| `mm_write` | Input | 1 | Host request type. `1` selects write; `0` selects read. |
| `mm_addr` | Input | 16 | Local byte address inside the NPU aperture. |
| `mm_wdata` | Input | 32 | Write data. Byte lane 0 is bits `[7:0]`, lane 1 is `[15:8]`, lane 2 is `[23:16]`, lane 3 is `[31:24]`. |
| `mm_wstrb` | Input | 4 | Write byte strobes. Registers and bias words require `4'b1111`; byte scratchpads use individual byte strobes. Ignored for reads. |
| `mm_rdata` | Output | 32 | Read data for an accepted read. Invalid reads return zero with `mm_error=1`. |
| `mm_ready` | Output | 1 | Request completion. A transfer completes when `mm_valid && mm_ready` is high on a rising `clk` edge. |
| `mm_error` | Output | 1 | One-transfer access error response. It is valid with `mm_ready=1` and does not remain asserted after the transfer unless the next transfer also errors. |
| `irq` | Output | 1 | Level interrupt. Asserted when interrupt enable is set and either sticky `done` or sticky `error` is set. |

## Clocking

`clk` is the only clock. There are no internal generated clocks and no clock-domain crossings inside `npu`.

All state changes occur on the rising edge of `clk`, except hardware reset assertion through `rst_n`. Host read data and response are valid for the transfer cycle in which `mm_valid && mm_ready` is true.

## Reset

`rst_n` is active-low asynchronous assert. When `rst_n=0`, the IP drives:

| Signal/state | Reset value |
|---|---|
| `mm_ready` | `1'b1` |
| `mm_error` | `1'b0` |
| `mm_rdata` | `32'h0000_0000` |
| `irq` | `1'b0` |
| FSM | `IDLE` |
| Scratchpads | All implemented bytes/words zero in the phase-1 register-array baseline |
| Registers | Values listed in `regmap.md` |

Reset deassertion is assumed to meet SoC reset timing requirements. The IP does not include a reset synchronizer.

## Target Protocol

The host interface is a simple ready/valid local target protocol:

- The host presents one request with `mm_valid=1`.
- If `mm_ready=1`, the request completes on that rising clock edge.
- If `mm_ready=0`, the request has not completed and all request inputs must remain stable.
- There are no bursts, protection bits, exclusive accesses, IDs, out-of-order responses, byte-lane endian conversions, or split responses.
- Register requests complete without wait states in phase 1. A future non-resettable SRAM initialization sequence may temporarily backpressure all requests as specified below.
- Scratchpad requests complete without wait states when `STATUS.busy=0`.
- Scratchpad requests stall with `mm_ready=0` while `STATUS.busy=1`, then complete after the command reaches a terminal state.

When `mm_valid=0`, `mm_ready` may remain high and `mm_error` is zero.

## Address and Alignment Rules

| Region | Address range | Alignment | Write strobe | Access behavior |
|---|---:|---|---|---|
| Registers | `0x0000-0x0034` at implemented offsets | Word aligned | `4'b1111` for writable registers | Reads and writes require `mm_addr[1:0]=0`. Read-only register writes return `RO_WRITE`. |
| Activation scratchpad | Reserved `0x0100-0x013f`; implemented `0x0100` through `0x0100+ACT_SPM_BYTES-1` | Word aligned transfer start | Any `mm_wstrb` | Reads return four bytes; writes update asserted byte lanes. |
| Weight scratchpad | Reserved `0x0200-0x023f`; implemented `0x0200` through `0x0200+WGT_SPM_BYTES-1` | Word aligned transfer start | Any `mm_wstrb` | Reads return four bytes; writes update asserted byte lanes. |
| Output scratchpad | Reserved `0x0300-0x033f`; implemented `0x0300` through `0x0300+OUT_SPM_BYTES-1` | Word aligned transfer start | Any `mm_wstrb` | Reads return four bytes; writes update asserted byte lanes when idle. |
| Bias scratchpad | Reserved `0x0400-0x043f`; implemented `0x0400` through `0x0400+4*BIAS_SPM_WORDS-1` | Word aligned | `4'b1111` for writes | Reads and writes one signed INT32 bias word. |

Valid byte scratchpad starting offsets are `0, 4, 8, ..., CAPACITY-4` for the selected scratchpad. A byte scratchpad access is valid only when all four lanes are inside the implemented prefix. A word-aligned access in the unused reserved tail returns `INVALID_ADDR`; an unaligned access returns `SPM_UNALIGNED` according to the existing decode priority.

Valid bias scratchpad offsets are `0, 4, ..., 4*(BIAS_SPM_WORDS-1)`. The remaining reserved bias aperture is unimplemented and returns `INVALID_ADDR`. At default parameter values, valid offsets remain `0, 4, ..., 60`.

## Register Access Timing

Register reads:

- Complete in one cycle when `mm_valid=1`.
- Return the current register value on `mm_rdata`.
- Return `mm_error=1` and zero read data for invalid or unaligned register addresses.

Register writes:

- Complete in one cycle when `mm_valid=1`.
- Require `mm_wstrb=4'b1111`.
- Apply write-one-to-clear and pulse semantics on the completing clock edge.
- Return `mm_error=1` and do not modify state for invalid address, read-only register write, unaligned address, or bad write strobe.

Descriptor register writes while `STATUS.busy=1` are accepted. They affect the next command only because all command descriptors are latched on accepted `CTRL.start`.

## Scratchpad Access Timing

Activation, weight, and output scratchpad reads when idle:

- Complete in one cycle.
- Return four bytes in little-endian order: `mm_rdata[8*n +: 8] = scratchpad[offset+n]`.

Activation, weight, and output scratchpad writes when idle:

- Complete in one cycle.
- For each lane `n`, update `scratchpad[offset+n]` only if `mm_wstrb[n]=1`.
- A write with `mm_wstrb=4'b0000` is accepted as a no-op.

Bias scratchpad accesses when idle:

- Reads complete in one cycle and return the selected signed INT32 bias word.
- Writes complete in one cycle only with `mm_wstrb=4'b1111`; other write strobes return `mm_error=1`, set `ERR_CODE=BIAS_BAD_WSTRB`, and do not modify the bias word.

Scratchpad accesses while busy:

- Hold `mm_ready=0`.
- Do not update `mm_rdata`, `mm_error`, sticky status, or scratchpad contents until the access later completes.
- Complete using the same idle rules after the command reaches `DONE` or `ERROR`.

The internal compute sequencer has priority over scratchpad arrays during a command. The host-visible stall rule avoids undefined simultaneous host/compute access behavior.

Phase 1 uses behavioral register arrays and retains the current zero-wait idle scratchpad accesses. It does not claim that synthesis infers an SRAM.

## Internal SRAM Replacement Boundary

No SRAM signal is a public `npu` port in phase 1. A future internal replacement may give each scratchpad an independent 1R1W interface with a synchronous read request, flopped read data valid one cycle later, a synchronous write request, 32-bit write data, and four byte write enables. Bias writes normally use `4'b1111`; byte scratchpads use lane enables.

The controller must adapt to that latency: compute read addresses are issued before operands are consumed, host scratchpad reads hold `mm_ready=0` until returned data is valid, and completion/status updates occur only after their dependent memory operations complete. The protocol already permits wait states, and no fixed command cycle count is part of the public contract.

For a macro without storage reset, hardware-reset release and `CTRL.soft_reset` require an internal zero-fill sequence over every implemented location. Until zero fill finishes, no command or scratchpad request may complete and `mm_ready` may remain low; `busy`, sticky status, and `irq` remain at reset values. The phase-1 register-array implementation performs its clear directly and adds no such initialization wait.

## Interrupt Timing

`irq` is a registered or combinational level function of architectural state:

```text
irq = irq_en && (done || error)
```

It must assert no later than the cycle after `done` or `error` becomes sticky. It must deassert no later than the cycle after `irq_en`, `done`, and `error` no longer require assertion.

## Timing of Command Completion

The docs do not require a fixed cycle count. A compliant implementation must preserve the visible ordering:

- `busy` asserts after an accepted legal `start`.
- Descriptor errors set sticky `error` before any output write.
- Each successful output byte is stored before `LAST_OUT_COUNT` is incremented for that byte.
- Final `done` is set after the final output byte is visible in `OUT_SPM`.
- `ACC_RESULT` is the last output element's signed INT32 post-bias accumulator on successful completion.

## Integration Notes

- A future APB/AHB wrapper must translate its protocol to this local target interface and preserve wait-state behavior for scratchpad stalls.
- A wrapper crossing clock domains must include CDC logic outside `npu`.
- SoC-level address decode and interrupt routing are external to this IP.
- The interface does not expose quantization scale metadata; software programs already-quantized multiplier, shift, zero point, and clamp fields.
