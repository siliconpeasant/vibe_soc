# OpenTitan Native IP Split Architecture Handoff

## Scope

This handoff defines the architecture plan for splitting the current OpenTitan Earlgrey
vendor-island `chip/top` implementation into vibe_soc-native IP packages. It is a pre-doc
architecture artifact only. It does not approve RTL edits, does not replace module-level
`design_spec.md` / `interface_spec.md` / `regmap.md` / `verification_plan.md`, and must not update
`pipeline_state.json`.

The canonical source of truth remains:

- OpenTitan vendor source: `chip/top/de/rtl/vendor/opentitan`
- Current top filelist entry: `chip/top/de/rtl/filelist.f`
- Current passing baseline: `chip_sw_uart_smoketest` through `soc-build.soc_sim`

The split is filelist-ownership-first. RTL is copied or promoted into native IP workspaces only
after the owning package doc stage is complete and its filelist order has a validation gate.

## Current Architecture Snapshot

`chip/top/de/rtl/filelist.f` is the human-readable entry point. It includes ordered fragments that
preserve the known-good FuseSoC-generated OpenTitan dependency order. The current split already
exposes these native package boundaries:

| Package | Status | Current responsibility |
|---|---:|---|
| `ip/digital/common` | stabilize | Shared OpenTitan primitive filelist fragments, still referencing vendor source |
| `ip/digital/tlul` | stabilize | Copied TL-UL package, integrity, FIFO/assert, adapters, RACL, and debug fragments |
| `ip/digital/uart_ot` | stabilize | Copied OpenTitan UART RTL and UART reg top |
| `chip/top` | vendor island | Remaining Earlgrey packages, autogen top packages, peripherals, security IP, xbars, CPU/debug, boot/ROM, AST, top wrappers |

Generated `de/run/rtl.f` currently expands to mostly `chip/top` vendor-owned entries plus the
native TL-UL and UART slices. The migration goal is to reduce `chip/top` ownership to integration
top, top-specific packages, pad/strap policy, and temporary vendor fallback references.

## Technology and Process Assumptions

No new physical process is selected by this handoff. Until a separate physical-design handoff
selects a node, PDK, SRAM/register-file compiler, IO library, flash/OTP macro, and analog library,
all split packages must preserve the current OpenTitan simulation-oriented generic implementation.

Assumptions:

- Standard-cell primitives continue through OpenTitan `prim` / `prim_generic` or existing
  `soc_ip_common` wrappers until a process library binding is approved.
- SRAM, ROM, flash, OTP, AST, USB PHY, clock, reset, power, life-cycle, and entropy analog sources
  are not process-closed. Their native packages must document macro/analog replacement points.
- DFT, scan, MBIST, LBIST, and low-power behavior are carried as OpenTitan interface assumptions
  only. They are not signed off by this split.
- `crg-gen` is not registered in the current tool contract. Do not schedule generated CRG RTL.
  Clock/reset work must stop at architecture/doc handoff or use existing RTL only.

Design-critical blockers before physical implementation:

- Foundry/process node, PDK, stdcell, SRAM/ROM/register-file compilers, flash/OTP macro strategy,
  IO/PHY libraries, and voltage domains are unresolved.
- Whether AST, flash, OTP, LC/key manager, and alert escalation are product requirements or only
  retained to keep the OpenTitan baseline passing is unresolved.

## Integration Architecture

The target architecture keeps `chip/top` as the integration owner and moves reusable IP into
short-named `ip/digital/*` packages.

Top-level ownership:

| Area | Owner after split | Notes |
|---|---|---|
| Chip wrapper, pad ring, straps, top package glue | `chip/top` | Keep `top_earlgrey`/`chip_earlgrey_asic` integration until replacement top doc stage |
| Shared primitives and common packages | `ip/digital/prim`, `ip/digital/common` | `common` may remain a compatibility aggregator |
| TL-UL fabric utilities | `ip/digital/tlul` | Existing package remains bus utility owner |
| Xbar instances | `ip/digital/xbar` | Own generated `tl_main_pkg.sv`, `xbar_main.sv`, `tl_peri_pkg.sv`, and `xbar_peri.sv` |
| Interrupts | `ip/digital/rv_plic` | Own IRQ gateway/target/reg/top |
| CPU subsystem | `ip/digital/rv_core_ibex` | Own `rv_core_ibex` wrapper and imported Ibex RTL dependency boundary |
| Debug | `ip/digital/rv_dm` | Own JTAG/DMI/TL-UL debug path |
| ROM/boot | `ip/digital/rom_ctrl`, `ip/digital/boot_rom` | Separate ROM controller from ROM image/collateral ownership |
| Security/entropy | `ip/digital/alert_handler`, `ip/digital/entropy_src`, `ip/digital/edn`, `ip/digital/csrng` | Split before broad peripherals because many peripherals emit alerts |
| Peripherals | `ip/digital/<ip>` | One package per IP unless doc stage approves grouping |

Primary protocol choices remain TL-UL for register and memory-mapped IP integration. Alert,
escalation, entropy, LC, RACL, interrupts, and DMI interfaces must be preserved verbatim until the
owning module doc stage approves a replacement contract.

## Address, Interrupt, Clock, Reset, and CDC Handoff

Address map is not reassigned by this handoff. Each split IP initially keeps its OpenTitan Earlgrey
base address and register layout as encoded by the existing `top_earlgrey` packages and generated
reg tops. Any native address-map consolidation requires a separate `chip/top/docs/architecture_address_map.md`
or module doc-stage update.

Interrupt routing is initially preserved through `rv_plic` and the existing top package constants.
Each peripheral package must document its outgoing IRQs and alert lines before moving out of
`chip/top` filelist ownership.

Clock/reset ownership is initially preserved through existing OpenTitan `clkmgr`, `rstmgr`, AST, and
top-level reset connections. CDC/RDC boundaries are frozen at the current OpenTitan interfaces until
the relevant package doc stage owns them. Because `crg-gen` is not registered, do not schedule
generated CRG RTL or generated clock/reset tree replacement.

## Seven-Step Split Plan

### 1. Filelist Entry Cleanup

Target work:

- Keep `chip/top/de/rtl/filelist.f` as the only top-level entry.
- Convert large residual `chip/top/de/rtl/fragments/*.f` blocks into owner-oriented fragments while
  preserving the exact expanded source order.
- Add a comment header to each fragment stating owner, source root, validation gate, and whether it
  is vendor-reference or copied-native RTL.
- Remove duplicate or dead entries only when the generated canonical filelist proves no compile
  order change.

Target package ownership:

- `chip/top/de/rtl/fragments/*`: temporary integration fragments only.
- `ip/digital/<module>/de/rtl/filelist.f`: full package manifest.
- `ip/digital/<module>/de/rtl/fragments/*.f`: order-preserving insertion points when a
  monolithic include would change OpenTitan compile order.

Validation gate:

- Run `soc-build.soc_comp` for `chip/top/de`, top `chip_earlgrey_asic`.
- Run `soc-build.soc_sim` for `chip/top/dv`, test `chip_sw_uart_smoketest`, seed `1`.
- Diff generated `de/run/rtl.f` against the previous expansion for source-order movement.

Risks:

- Hidden package ordering dependencies in OpenTitan generated packages.
- C/C++ DPI and AES model entries in RTL filelists still need top-level build flags.

### 2. Stabilize Existing `opentitan_common`, `opentitan_tlul`, and `opentitan_uart`

Target work:

- Keep `ip/digital/tlul` as copied-native TL-UL ownership.
- Keep `ip/digital/uart_ot` as copied-native UART ownership.
- Freeze `ip/digital/common` as a compatibility layer before further primitive splitting.
- Add or refresh doc-stage handoff for each package before any RTL changes.

Expected ownership:

| Package | Filelist ownership | Validation focus |
|---|---|---|
| `common` | Common primitive fragments and compatibility include points | Package ordering, primitive dependency closure |
| `tlul` | `tlul_pkg`, integrity helpers, FIFOs, adapters, sockets, assertions | TL-UL type compatibility and adapter elaboration |
| `uart_ot` | UART reg package/top, UART core, RX/TX | TL-UL register interface and chip smoke UART output |

Validation gate:

- Standalone `soc-build.soc_comp` where package Makefiles support it.
- Chip-level `chip_sw_uart_smoketest` must still pass after each package filelist cleanup.

Risks:

- `opentitan_common` still references vendor primitive files and is not a true source-owned package.
- UART standalone DV is absent; chip-level smoke remains the functional proof point.

### 3. Split `prim` / Common Layer

Target packages:

- `ip/digital/prim`
- `ip/digital/prim_generic`
- `ip/digital/prim_alert`
- `ip/digital/prim_lc`
- `ip/digital/prim_reg`
- `ip/digital/common` as a temporary aggregator for top packages and shared generated
  constants that are not primitive RTL.

Expected filelist ownership:

- Move `hw/ip/prim/rtl/*` and `hw/ip/prim_generic/rtl/*` filelist entries out of `chip/top`
  fragments into the relevant `opentitan_prim*` package fragments.
- Keep source references to `chip/top/de/rtl/vendor/opentitan` until the package doc stage approves
  copied-native source ownership.
- Preserve fragment insertion around TL-UL and CPU package points where OpenTitan order currently
  requires it.

Validation gate:

- Package compile for primitive packages where feasible.
- Full `chip_earlgrey_asic` compile.
- `chip_sw_uart_smoketest` simulation.

Risks/dependencies:

- Primitive cells are shared by almost every later package; a bad split blocks all downstream work.
- Technology binding for memories, clock mux/gate, reset sync, pads, and security anchors is still
  unresolved.

### 4. Split Alert, Entropy, EDN, and CSRNG

Target packages:

- `ip/digital/alert_handler`
- `ip/digital/entropy_src`
- `ip/digital/edn`
- `ip/digital/csrng`

Expected filelist ownership:

- `opentitan_alert_handler`: alert handler reg packages/top/wrap, class, ping/esc timers, accumulator,
  LPG control, alert handler top.
- `opentitan_entropy_src`: entropy source packages, health tests, counters, enable delay, core/top.
- `opentitan_edn`: EDN reg package/top, ack/main state machines, core/top.
- `opentitan_csrng`: CSRNG reg package/top, state DB, command stage, block encrypt, CTR_DRBG, core/top.

Validation gate:

- Owner package compile after doc-stage handoff.
- Chip compile and `chip_sw_uart_smoketest`.
- Add an alert/entropy smoke or CSR-driven sanity test only after DV package ownership exists.

Risks/dependencies:

- Alert lines are cross-cutting. Peripherals cannot be fully isolated until alert IDs and top package
  constants are owned and stable.
- Entropy depends on AST/dev entropy assumptions and may remain simulation-only until analog entropy
  source strategy is approved.
- CSRNG uses AES/block encryption dependencies and primitive security utilities.

### 5. Split Xbar

Target package:

- `ip/digital/xbar`

Expected filelist ownership:

- `opentitan_xbar` owns `tl_main_pkg.sv`, `xbar_main.sv`, `tl_peri_pkg.sv`, and `xbar_peri.sv`.
- Shared socket and TL-UL adapter implementation stays in `opentitan_tlul`.
- Address decode constants remain copied from current OpenTitan generated packages until a native
  address-map doc updates them.

Validation gate:

- Xbar package compile against `opentitan_tlul`.
- Chip compile.
- `chip_sw_uart_smoketest`.
- Address-map spot check: UART, ROM, flash, RV_DM, SRAM, and PLIC decode paths still match current
  generated `top_earlgrey` constants.

Risks/dependencies:

- Xbar instances are generated from OpenTitan topgen output. Native regeneration must not be
  scheduled unless the generator inputs and generated outputs are owned and reviewed.
- Address movement changes software images and UVM RAL behavior, so no address reassignment is
  allowed in this split phase.

### 6. Split Peripheral IPs

Target packages:

- Already split/stabilized: `ip/digital/uart_ot`
- Bootstrap priority: `ip/digital/spi_device`, `ip/digital/flash_ctrl`,
  `ip/digital/flash_mem_model`, `ip/digital/gpio`, `ip/digital/pinmux`
- Timer/interrupt support: `ip/digital/rv_timer`, `ip/digital/rv_plic`,
  `ip/digital/aon_timer`
- Additional retained peripherals: `ip/digital/spi_host`, `ip/digital/i2c`,
  `ip/digital/pwm`, `ip/digital/usbdev`, `ip/digital/adc_ctrl`,
  `ip/digital/hmac`, `ip/digital/aes`, `ip/digital/kmac`,
  `ip/digital/otbn`, `ip/digital/pattgen`, `ip/digital/sysrst_ctrl`,
  `ip/digital/sram_ctrl`

Expected filelist ownership:

- Each package owns its reg package/top, protocol-specific packages, core submodules, and IP top.
- Top-specific generated wrappers under `hw/top_earlgrey/ip_autogen/<ip>/rtl` move with the package
  when they are the active Earlgrey implementation.
- Simulation-only memory/model collateral must be named explicitly in package docs and kept out of
  synthesis filelists.

Validation gate:

- Split one peripheral package at a time.
- Package compile if dependency closure is available.
- Chip compile and `chip_sw_uart_smoketest` after each package.
- For bootstrap-critical peripherals, add `chip_sw_uart_tx_rx_bootstrap` only after the required
  `uart_tx_rx_test` software image is available.

Risks/dependencies:

- Peripherals share primitive, alert, interrupt, pinmux, clock/reset, RACL, and TL-UL dependencies.
- Flash/OTP/SRAM require memory macro or simulation model strategy before physical signoff.
- USB, ADC, AST, and sensor paths have analog/PHY assumptions that are not closed here.

### 7. Split CPU, Debug, ROM, and Boot-Related Modules

Target packages:

- `ip/digital/ibex`
- `ip/digital/rv_core_ibex`
- `ip/digital/rv_dm`
- `ip/digital/rom_ctrl`
- `ip/digital/boot_rom`
- `ip/digital/lc_ctrl`
- `ip/digital/keymgr`
- `ip/digital/otp_ctrl`
- `ip/digital/otp_macro`

Expected filelist ownership:

- `opentitan_ibex`: imported lowRISC Ibex RTL and package boundary.
- `opentitan_rv_core_ibex`: OpenTitan wrapper, cfg reg top, address translation, PMP reset package,
  and core integration policy.
- `opentitan_rv_dm`: JTAG package, debug module reg tops, DMI gate, debug module top.
- `opentitan_rom_ctrl`: ROM controller reg packages/top, compare/counter/FSM/mux/scrambled ROM.
- `opentitan_boot_rom`: ROM image collateral, VMEM selection, and software boot collateral interface.
- `opentitan_lc_ctrl`, `opentitan_keymgr`, `opentitan_otp_ctrl`, `opentitan_otp_macro`: boot policy,
  life-cycle, key, and OTP dependencies retained only if product scope requires them.

Validation gate:

- CPU/debug package compile with TL-UL and primitive dependencies.
- Chip compile.
- `chip_sw_uart_smoketest`.
- Debug/ROM boot validation must wait for a doc-stage decision on debug access policy, ROM image
  ownership, and software image build/provenance.

Risks/dependencies:

- Ibex ownership has third-party provenance and licensing considerations; keep OpenTitan/lowRISC
  notices intact.
- ROM, OTP, LC, and key manager affect security boundaries and boot trust. Treat behavior changes as
  design-critical and rerun affected module doc stages.
- Bootstrap case remains blocked until `uart_tx_rx_test_sim_dv.64.scr.vmem` or equivalent approved
  software image is available.

## Module Doc-Stage Handoff Matrix

Each package must enter the gated module flow only after this handoff is consumed by the doc stage.

| Module/workspace | Functional responsibility | Required interfaces | Clock/reset | Register/address ownership | Verification focus | Dependencies |
|---|---|---|---|---|---|---|
| `ip/digital/prim*` | Shared primitive cells | Primitive module APIs | Per primitive | None | Compile closure and representative primitive tests | Process/library decision |
| `ip/digital/tlul` | TL-UL utility fabric | TL-UL H2D/D2H, RACL, DMI adapters | `clk_i`, `rst_ni` plus async FIFO domains | None | Adapter/socket/integrity compile and smoke | `opentitan_prim*` |
| `ip/digital/alert_handler` | Alert collection/escalation | Alert/esc, TL-UL, IRQ | Main/AON as existing OT | Alert handler CSRs | Alert ping/esc sanity | `opentitan_prim_alert`, top alert IDs |
| `ip/digital/entropy_src` | Entropy conditioning | Entropy, TL-UL, alerts, IRQ | Main/entropy domains | Entropy CSRs | Health-test compile/sanity | AST entropy assumption |
| `ip/digital/edn` | Entropy distribution | Entropy req/rsp, TL-UL, alerts, IRQ | Main | EDN CSRs | CSR-driven req/rsp sanity | `entropy_src`, `csrng` |
| `ip/digital/csrng` | CSRNG | CSRNG app, TL-UL, alerts, IRQ | Main | CSRNG CSRs | Instantiate/generate/reseed sanity | AES primitive path |
| `ip/digital/xbar` | Main/peripheral TL-UL interconnects | TL-UL hosts/devices | Main/peripheral | Address decode constants | Decode and routing spot checks | `opentitan_tlul`, address map |
| `ip/digital/uart_ot` | UART peripheral | TL-UL, IRQ, UART pins | Peripheral/core clock | UART CSRs | Chip UART smoke and standalone UART where added | `opentitan_tlul`, `opentitan_prim*` |
| `ip/digital/spi_device` | Bootstrap SPI device | TL-UL, SPI pins, IRQ, alerts | SPI and main domains | SPI device CSRs | Bootstrap ingress sanity | Pinmux, flash, software image |
| `ip/digital/flash_ctrl` | Flash controller | TL-UL, flash macro/model, alerts | Main/flash domains | Flash CSRs and windows | Read/program/erase model sanity | Flash macro/model |
| `ip/digital/rv_plic` | Interrupt controller | IRQ sources/targets, TL-UL | Main | PLIC CSRs | IRQ gateway/target sanity | Peripheral IRQ inventory |
| `ip/digital/rv_core_ibex` | CPU subsystem wrapper | I/D TL-UL, IRQ, debug, alerts | Core/main | Core cfg CSRs | Boot smoke and exception/debug sanity | Ibex, xbar, ROM |
| `ip/digital/rv_dm` | Debug module | JTAG/DMI, TL-UL, CPU debug | JTAG and main domains | Debug CSRs | JTAG/DMI access sanity | CPU, TL-UL |
| `ip/digital/rom_ctrl` | ROM controller | TL-UL, ROM macro/model, alerts | Main | ROM CSRs/windows | ROM fetch and integrity sanity | Boot ROM image |
| `ip/digital/boot_rom` | Boot ROM collateral | ROM image interface | N/A for RTL package unless wrapper needed | ROM image ownership | Image provenance and boot test | SW build/provenance |

## Replacement and Reuse Policy

Default IP selection is OpenTitan-derived native package reuse because the current passing baseline
already proves integration viability. Replacement options must be documented before use:

- Replace `opentitan_tlul` only with an approved bridge/interconnect plan and address-map migration.
- Replace Ibex only with a CPU subsystem architecture update covering interrupt, debug, boot ROM,
  privilege, and software ABI impact.
- Replace flash/OTP/ROM/AST only after process macro and analog dependencies are approved.
- Replace CRG only when a registered CRG flow exists. `crg-gen` is not registered now.

## Blockers and Required Decisions

Design-critical blockers:

- Product scope for retained OpenTitan IP is unresolved: full Earlgrey-compatible chip versus
  reduced UART/bootstrap-focused subset.
- Physical technology/process and macro/analog strategy are unresolved.
- Native address map and interrupt inventory are not approved.
- Clock/reset generation strategy is unresolved, and `crg-gen` is not registered.
- Bootstrap software image for `chip_sw_uart_tx_rx_bootstrap` is not available in the current
  documented baseline.
- Security boundary for debug, ROM, LC, key manager, OTP, alert escalation, entropy, and RACL is not
  approved.

## Recommended Next Dispatches

1. `soc-doc-engineer` for `ip/digital/common`, `ip/digital/tlul`, and
   `ip/digital/uart_ot` stabilization docs.
2. `soc-doc-engineer` for `ip/digital/prim*` package docs before any primitive source
   promotion.
3. `soc-doc-engineer` for `opentitan_alert_handler`, `opentitan_entropy_src`, `opentitan_edn`, and
   `opentitan_csrng`.
4. `soc-doc-engineer` for `opentitan_xbar`, including address-map
   preservation notes.
5. `soc-doc-engineer` one package at a time for bootstrap-critical peripherals:
   `opentitan_spi_device`, `opentitan_flash_ctrl`, `opentitan_flash_mem_model`, `opentitan_gpio`,
   and `opentitan_pinmux`.
6. `soc-doc-engineer` for CPU/debug/ROM/boot packages only after boot/debug/security decisions are
   recorded.

Do not dispatch RTL, verification, synthesis, integration generation, OpenROAD, or generated CRG
work from this architecture handoff alone.
