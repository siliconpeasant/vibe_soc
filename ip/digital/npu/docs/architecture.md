# npu Architecture Handoff

## Scope and Status

This document is the architecture handoff for the reusable digital IP `npu` under `ip/digital/npu`. It supersedes the earlier dot-product-demo architecture with an approved minimal INT8 inference-layer evolution. It does not approve RTL, verification, synthesis, CRG, or top-level integration work.

The top module remains `npu`, and the local memory-mapped target interface remains unchanged. Downstream RTL, verification, and synthesis must rerun because the documented register map and compute behavior have changed.

## Knowledge-Base Evidence

- `documents/integrated-circuit/Google/Quantization-and-Training-of-Neural-Networks-for-Efficient-Integer-Arithmetic-Only-Inference.pdf:page 4` describes a typical quantized fused layer using INT8/UINT8 operands, signed INT32 accumulation, INT32 bias, fixed-point multiplier with rounding/right shift, saturating 8-bit output cast, and fused clamp activations such as ReLU/ReLU6.
- The same Google paper page states that INT32 bias uses zero point 0 and accumulator scale because bias quantization error can shift outputs.
- `tutorials/npu/zsc_v2_npu_tutorial/markdown/chapter5.md:314` identifies INT8 quantization, zero-point/scale, per-channel quantization, and fused activation as key inference-accelerator techniques; it also notes ReLU6/clamp is hardware-simple.
- Earlier NPU knowledge-base evidence selected scratchpad-dominant storage for predictable tensor data with software/DMA scheduling, and required a preserved datapath/controller partition.
- `textbooks/integrated-circuit/Digital-System-Test-and-Testable-Design-Using-HDL-models-and-Architectures.pdf:page 67` recommends RTL partitioning into datapath and controller, where the datapath stores/transfers data and performs arithmetic while the controller state machine issues control signals.

## Selected IP Architecture

### IP Selection and Reuse

| Block | Selection | Source/reuse | Rationale | Risk/replacement |
|---|---|---|---|---|
| `npu` top | Evolved in-house RTL IP | `ip/digital/npu` | Required reusable digital IP with a stable wrapper-friendly target interface | Existing dot-product RTL must be updated after doc approval |
| Register/control target | Existing simple memory-mapped command/data interface | In-house | Avoids binding the IP to APB/AHB/AXI; wrapper can be added later | APB/AHB wrapper protocol remains a SoC integration task |
| Scratchpad storage | Small software-managed activation, weight, output, and bias windows | In-house resettable register arrays with implementation-only byte-lane banking | Matches KB guidance for predictable tensor access, reduces behavioral read-mux fan-in, and avoids cache/tag complexity | Replace the internal boundary with compiler SRAM during synthesis/PD if a foundry macro is selected |
| Load/store sequencer | Internal descriptor-driven scratchpad address generator | In-house | Provides DMA-style local scheduling without making this IP an external bus master | If true external DMA is required, bus protocol, burst, ordering, and error semantics must be architected before RTL |
| Compute datapath | 4-lane signed INT8 MAC with signed 32-bit accumulation | In-house | Tiny scope, complete NPU role coverage, deterministic verification | Can scale to more lanes only after doc/RTL reopen |
| Quantization/output | INT32 bias, signed INT32 multiplier, rounding/right shift, output zero point, optional clamp, signed INT8 saturation | In-house | Aligns minimal fused-layer behavior with KB evidence | True per-output multiplier arrays are future scope |
| Controller | FSM controlling descriptor check, load, MAC, bias, requant, store, done, and error | In-house | Clear datapath/controller partition and testable sequencing | Microcode or descriptor queue can replace FSM in a larger NPU |

License/ownership assumption: all planned RTL is project-owned in-house code. No third-party RTL or commercial NPU IP is selected for this tiny implementation.

### Functional Model

The NPU executes one software-scheduled inference command at a time:

1. Software writes an INT8 activation vector into activation scratchpad.
2. Software writes one or more INT8 weight rows into weight scratchpad.
3. Software writes optional signed INT32 bias values into bias scratchpad.
4. Software programs base, count, stride, quantization, activation, and interrupt registers.
5. The internal sequencer reuses the activation vector for each output element, reads a row-strided weight row, and runs K groups of four signed INT8 MACs.
6. The datapath adds signed INT32 bias, applies multiplier/rounding/right shift, adds signed output zero point, applies optional ReLU or ReLU6-style clamp, saturates to signed INT8, and stores one output byte.
7. Status, interrupt, last-output count, accumulator result, and error state report completion or fault conditions.

This is not a convolution engine, systolic array, autonomous external-memory accelerator, or framework-specific quantization unit. It is a deliberately small linear/GEMV NPU slice that preserves a backward-compatible single-output dot-product profile.

## Technology and Process Assumptions

| Topic | Architecture assumption |
|---|---|
| Process/node | No foundry or node is selected at architecture stage. RTL must be portable Verilog-2005. |
| Standard cells | Generic synchronous logic using single `clk`; no hard macros, gated clocks, latches, or process-specific cells in initial RTL. |
| Memories | Scratchpads initially use resettable register arrays striped over four byte-lane banks without changing the software-visible windows. Replacement with SRAM compiler macro is deferred until process selection. |
| Voltage domains | One digital voltage domain. No level shifters or isolation cells inside `npu`. |
| Clocks | One input clock `clk`; no internally generated clocks. |
| Reset | One active-low asynchronous reset `rst_n`, synchronized/deassertion assumptions documented for SoC integration. |
| Timing target | Tiny IP should target easy closure at chip peripheral clock rates; no numeric frequency is approved until SoC process/library constraints are known. |
| Power | Clock-enable style activity reduction is allowed. No clock-gating cells or power-gating logic in initial RTL. |
| Physical design | Small rectangular IP with scratchpad placed near datapath is expected; no placement, floorplan, SDC, or OpenROAD handoff in this architecture step. |

## Top-Level Partition

The doc and RTL stages should partition `npu` into these internal roles, even if implemented in one Verilog file for small scope:

| Role | Responsibility |
|---|---|
| Memory-mapped frontend | Decodes register and scratchpad aperture accesses, returns read data, ready, and error response. |
| Register file | Holds control, descriptor, quantization, status, interrupt, and error state. |
| Scratchpad | Software-managed activation, weight, output, and bias storage. Target sizes: 64 bytes activation, 64 bytes weight, 64 bytes output, and 16 signed INT32 bias words. Byte-addressed arrays may use four internal lane banks to reduce read-mux fan-in. |
| Load/store sequencer | Generates internal scratchpad reads/writes, supports activation stride, weight row stride, output stride, and bias indexing, and detects out-of-range descriptors. |
| MAC datapath | Four signed INT8 lanes, signed 16-bit products, signed INT32 accumulator, optional accumulator seed. |
| Bias/requantize/activate | Adds INT32 bias, applies fixed-point multiplier and shift, adds zero point, clamps activation, and saturates to signed INT8. |
| Controller FSM | Owns command acceptance, busy/done/error sequencing, interrupt request, and datapath enables. |

Controller/datapath separation is required in the doc-stage microarchitecture to preserve reviewability and testability.

## Interface Concept

The IP exposes the existing simple single-cycle target-style memory-mapped interface that can later be wrapped for APB or AHB:

| Signal | Dir | Width | Description |
|---|---:|---:|---|
| `clk` | in | 1 | Single IP clock. |
| `rst_n` | in | 1 | Active-low asynchronous reset. |
| `mm_valid` | in | 1 | Register/data access request valid. |
| `mm_write` | in | 1 | 1 = write, 0 = read. |
| `mm_addr` | in | 16 | Byte address within NPU local aperture. |
| `mm_wdata` | in | 32 | Write data. |
| `mm_wstrb` | in | 4 | Byte write strobes. |
| `mm_rdata` | out | 32 | Read data. |
| `mm_ready` | out | 1 | Request accepted/read data valid. |
| `mm_error` | out | 1 | Access error response for invalid address/alignment/write strobe. |
| `irq` | out | 1 | Level interrupt for done or error when enabled. |

Protocol assumptions:

- At most one request is accepted per cycle.
- Register accesses complete with `mm_ready` in one cycle.
- Scratchpad aperture accesses may stall while the internal sequencer owns scratchpad storage.
- No burst, out-of-order, byte-lane endian conversion, protection, or bus locking semantics are defined inside this IP.
- Endianness is little-endian for byte placement within `mm_wdata`.

## Register and Addressing Concept

The approved local address map is:

| Offset/range | Name | Access | Purpose |
|---|---|---|---|
| `0x0000` | `CTRL` | RW/WO bits | `start`, `soft_reset`, `irq_en`, `clear_done`, `clear_error`. |
| `0x0004` | `STATUS` | RO/W1C bits | `busy`, `done`, `error`, `sat_overflow`, `cmd_active`. |
| `0x0008` | `CFG` | RW/RO mixed | K-step count and activation stride. |
| `0x000c` | `ACT_BASE` | RW | Activation scratchpad byte base. |
| `0x0010` | `WGT_BASE` | RW | Weight scratchpad byte base. |
| `0x0014` | `OUT_BASE` | RW | Output scratchpad byte base. |
| `0x0018` | `ACC_INIT` | RW | Signed INT32 accumulator seed. |
| `0x001c` | `ACC_RESULT` | RO | Last output element's post-bias accumulator. |
| `0x0020` | `ERR_CODE` | RO/W1C | Encoded last error. |
| `0x0024` | `OUT_CFG` | RW | Output count, output stride, weight row stride. |
| `0x0028` | `BIAS_BASE` | RW | Bias scratchpad word base. |
| `0x002c` | `QUANT_MULT` | RW | Signed INT32 quant multiplier. |
| `0x0030` | `QUANT_CFG` | RW | Quant shift, output zero point, activation mode, ReLU6 max. |
| `0x0034` | `LAST_OUT_COUNT` | RO | Number of output bytes stored by the most recent command. |
| `0x0100-0x013f` | `ACT_SPM` | RW | 64-byte activation scratchpad window. |
| `0x0200-0x023f` | `WGT_SPM` | RW | 64-byte weight scratchpad window. |
| `0x0300-0x033f` | `OUT_SPM` | RW | 64-byte output scratchpad window. |
| `0x0400-0x043f` | `BIAS_SPM` | RW | 16 signed INT32 bias entries. |

Required error conditions include start while busy, descriptor range failures for all scratchpad windows, invalid quantization and activation fields, invalid or unaligned host accesses, unsupported register/bias write strobes, and read-only register writes.

## Clock, Reset, CDC, and RDC

- `npu` has one clock domain: `clk`.
- `rst_n` is asynchronous assert, active low. RTL must make reset behavior deterministic for all externally visible registers and FSM state.
- No CDC exists inside the IP. Any APB/AHB wrapper crossing to another domain is a SoC integration responsibility.
- Reset domain crossing concerns are limited to `rst_n` distribution and deassertion timing. The SoC CRG owner must provide a reset compatible with asynchronous-assert/safe-deassert usage.

## DFT, Verification, and Synthesis Assumptions

DFT:

- Use scan-friendly synchronous state elements; avoid latches, internally generated clocks, and combinational feedback.
- Scratchpad memories must be replaceable by scan-excluded SRAM macros with MBIST hooks if the SoC later selects SRAM compilers.
- No LBIST, MBIST controller, scan stitching, or test wrapper is designed in this architecture artifact.

Verification:

- Required directed tests include reset defaults, register read/write, illegal access, start while busy, backward-compatible dot product, multi-output inference, bias, multiplier/shift requantization, output zero point, activation none/ReLU/ReLU6, output stride, bias range, descriptor out-of-range, and done/error interrupt behavior.
- Required reference model covers signed INT8 multiply, signed INT32 accumulation and bias, signed 64-bit requantization, activation clamp, and signed INT8 saturation.
- Required integration checks cover memory aperture byte-lane behavior and scratchpad busy stall behavior.

Synthesis:

- Initial RTL must synthesize as generic Verilog-2005 without vendor-specific primitives.
- Synthesis constraints are owned by the later synthesis/doc stages, not this architecture handoff.
- If inferred scratchpad area is too large for the selected process, rerun doc and RTL with explicit SRAM macro assumptions.

## SoC Integration Plan

1. Complete this reopened `npu` doc stage: `design_spec.md`, `interface_spec.md`, `regmap.md`, and `verification_plan.md` under `ip/digital/npu/docs/`.
2. Update RTL only after doc approval.
3. Implement the stable target port and the scratchpad, sequencer, MAC, bias/requant, activation, controller, and status partitions.
4. Verify standalone IP through the registered `soc-build` flow.
5. Synthesize standalone IP through the registered `soc-build` flow.
6. Later SoC integration may wrap the target interface with APB or AHB. That wrapper must own protocol conversion, address decode, clock/reset crossing if any, and SoC interrupt routing.

The NPU does not create CRG, top integration logic, bus fabric, external memory DMA, or chip-level address map entries in this architecture step.

## Assumptions, Risks, and Blockers

Approved assumptions carried forward:

- Reusable digital IP at `ip/digital/npu`, top module `npu`.
- Verilog-2005 target.
- Single clock `clk`, active-low asynchronous reset `rst_n`.
- Same local memory-mapped target interface ports.
- Scratchpad-dominant storage with software or external DMA scheduling.
- Datapath/controller partitioning.
- Scope is intentionally small: 4-lane signed INT8 MAC datapath, signed INT32 accumulator/bias, fixed-point requantization, activation clamp, and signed INT8 output.

Architecture assumptions:

- Internal DMA/load-store control means scratchpad descriptor sequencing and prefetch-style staging, not autonomous external memory access.
- Software or a future bus wrapper is responsible for moving tensor data between system memory and NPU scratchpad.
- Per-channel quantization is approximated in this minimal scope by programming one multiplier/shift per command; true per-output multiplier arrays are future scope.
- Software supplies quantized ReLU6 upper clamp because the hardware does not store real-valued scale.

Blockers for downstream stages:

- No design-critical ambiguity remains in the documented minimal scope.
- RTL, verification, and synthesis results from the earlier dot-product design are stale and must rerun against these docs.
- A true external-memory DMA master is not approved. If required, the architecture must be reopened to select bus protocol, ordering, burst, protection, and error semantics.
- Foundry process, SRAM compiler, target frequency, and DFT insertion strategy are not selected. SRAM macro binding and timing closure claims are blocked until those decisions exist.

Unresolved non-blocking risks:

- Scratchpad size may need adjustment after synthesis area estimates.
- Single-port inferred memories may cause stalls during simultaneous host and compute access; the docs define host scratchpad stall while busy to avoid undefined behavior.
- Full per-channel or per-output quantization parameters may be required by future models and would need a register-map extension.
