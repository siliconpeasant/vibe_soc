# OpenTitan Verilator UART smoke

Select this flow explicitly with `SIMULATOR=verilator`; the default chip/top
recipe remains VCS/UVM. Use registered `soc_comp` and `soc_sim` with module
`chip/top`, simulator `verilator`, and test `chip_sw_uart_smoketest`.

`build_sw.sh` builds the test ROM and OTTF UART smoketest without Bazel.
`OT_UPSTREAM_ROOT` defaults to `/workspace/oss/opentitan`, at the matching
OpenTitan commit `d63fbbcd5c2847e2483efc106a9f3a426251c7f1`.
`OT_SW_PYTHON` defaults to `/workspace/oss/venv/bin/python`; its requirements
include OpenTitan dependencies and pyelftools. The build uses the
`riscv64-unknown-elf` GCC/binutils on PATH. Upstream and vendored files are
read-only inputs; generated DT, DIF/register headers, objects, and images
go under ignored `chip/top/dv/sim/sw_sim_verilator/`.

Software generation uses the upstream clkmgr/pwrmgr/rstmgr DT bindings.
Compilation mirrors the upstream device defines and linker scripts.
The flash link explicitly includes `manifest_def.c`; the build checks that
the exported binary starts with its 1024-byte manifest and that its entry
matches the ELF entry within the executable region before producing VMEM.
The ROM image uses upstream rom_ctrl scrambling, ECC, and digest generation.
Upstream `rules/opentitan/sim_verilator.bzl` produces plain 64-bit flash
VMEM for its raw `MemArea` loader; applying the sim_dv flash scrambling
transform would be incompatible. The requested `.64.scr.vmem` basename
is retained, but its contents follow the Verilator format. OTP follows
the upstream Verilator RMA configuration.

The harness status address is `0x411f0080`, matching the generated Ibex
DV_SIM_WINDOW address in `device_sim_verilator.c`. UART DPI runs at 7200
baud and 500000 Hz, matching that device. Simulation accepts only this smoke
test and requires the harness `TEST PASSED CHECKS` marker and exit zero.
The software prerequisite runs before simulation; compilation uses at most
four jobs, C++17, no tracing, and an 1800-second timeout. Software has a
900-second timeout; each simulation is bounded to at most 2400 seconds
and defaults to 10000000000 cycles. Registered MCP calls also impose their
own deadlines.

Evidence is retained in the case directory as `compile.log`, `sim.log`,
and `uart0.log`; software diagnostics and generated VMEM files remain
in `sw_sim_verilator/`. Regenerable object/build trees may be removed after
validation. This smoke test is functional bring-up evidence; synthesis,
formal, and hardware signoff remain outside this task. Implementation decisions use the matching upstream BUILD files, transforms,
device source, and harness as local evidence.
