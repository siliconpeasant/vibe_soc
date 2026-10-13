# Open-source Verilator flow for chip/top (OpenTitan Earl Grey).
#
# Selected only by an explicit `SIMULATOR=verilator` on the make command line;
# the default chip/top flow stays VCS + UVM. Reuses OpenTitan's vendored
# Verilator harness (chip_earlgrey_verilator + dv/verilator/chip_sim_tb) and
# DPI models instead of the UVM testbench, so only SW-driven cases
# built for device_sim_verilator are supported (currently uart_smoketest).
#
#   make comp MODULE=chip/top TEST=chip_sw_uart_smoketest SIMULATOR=verilator
#   make sim  MODULE=chip/top TEST=chip_sw_uart_smoketest SIMULATOR=verilator

OT_VL_HW        := $(OT_VENDOR_ROOT)/hw
OT_VL_JOBS      ?= 4
OT_VL_OPT       ?= -O1
OT_VL_TIMEOUT   ?= 2400
# Set to e.g. 100000 for a bounded startup diagnostic (0 disables cycle limit).
OT_VL_MAX_CYCLES ?= $(VERILATOR_MAX_CYCLES)
# Both device_sim_verilator and the harness use the Ibex DV_SIM_WINDOW
# (configuration base 0x411f0000 + generated register offset 0x80).
OT_VL_TEST_STATUS_ADDR ?= 32'h411f0080
OT_VL_SW_DIR    := $(PROJECT_ROOT)/chip/top/dv/sim/sw_sim_verilator
OT_VL_SW_BUILD  := $(OT_TB_ROOT)/verilator/build_sw.sh
OT_VL_OTP_IMG   ?= $(OT_VL_SW_DIR)/otp_sim_verilator.vmem
OT_VL_ROM_IMG   ?= $(OT_VL_SW_DIR)/test_rom_sim_verilator.39.scr.vmem
OT_VL_FLASH_IMG ?= $(OT_VL_SW_DIR)/uart_smoketest_sim_verilator.64.scr.vmem
OT_VL_FLIST     := $(BUILD_DIR)/verilator_rtl.f

# RTL comes from the canonical chip/top filelist minus the ASIC top and all
# UVM/DV collateral; the Verilator harness, sim SRAM and DPI models are added.
OT_VL_EXCLUDE   := /dv/|/generic_dv/|chip_earlgrey_asic\.sv|chip_ral_pkg\.sv|\.(c|cc)$$|^//
OT_VL_SV := \
  $(OT_VL_HW)/dv/sv/dv_utils/dv_test_status_pkg.sv \
  $(OT_VL_HW)/dv/sv/str_utils/str_utils_pkg.sv \
  $(OT_VL_HW)/dv/sv/sw_test_status/sw_test_status_pkg.sv \
  $(OT_VL_HW)/dv/sv/sw_test_status/sw_test_status_if.sv \
  $(OT_VL_HW)/dv/sv/sim_sram/sim_sram_if.sv \
  $(OT_VL_HW)/dv/sv/sim_sram/tlul_sink.sv \
  $(OT_VL_HW)/dv/sv/sim_sram/sim_sram.sv \
  $(addprefix $(OT_VL_HW)/dv/dpi/,uartdpi/uartdpi.sv gpiodpi/gpiodpi.sv spidpi/spidpi.sv \
    usbdpi/usbdpi.sv dmidpi/dmidpi.sv jtagdpi/jtagdpi.sv) \
  $(OT_VL_HW)/top_earlgrey/rtl/chip_earlgrey_verilator.sv \
  $(OT_VL_HW)/top_earlgrey/dv/verilator/chip_sim_tb.sv \
  $(OT_TB_ROOT)/verilator/ot_sw_log.sv
OT_VL_CPP := \
  $(addprefix $(OT_VL_HW)/dv/dpi/,common/tcp_server/tcp_server.c dmidpi/dmidpi.c \
    gpiodpi/gpiodpi.c jtagdpi/jtagdpi.c spidpi/spidpi.c spidpi/monitor_spi.c uartdpi/uartdpi.c \
    usbdpi/usb_crc.c usbdpi/usb_monitor.c usbdpi/usb_transfer.c usbdpi/usb_utils.c \
    usbdpi/usbdpi.c usbdpi/usbdpi_stream.c usbdpi/usbdpi_test.c) \
  $(addprefix $(OT_VL_HW)/dv/verilator/cpp/,dpi_memutil.cc ecc32_mem_area.cc mem_area.cc \
    sv_scoped.cc verilator_memutil.cc) \
  $(addprefix $(OT_VL_HW)/dv/verilator/simutil_verilator/cpp/,verilator_sim_ctrl.cc \
    verilated_toplevel.cc) \
  $(OT_VL_HW)/ip/prim/dv/prim_secded/secded_enc.c \
  $(OT_VL_HW)/top_earlgrey/dv/verilator/chip_sim_tb.cc
OT_VL_INC := $(addprefix -I$(OT_VL_HW)/,dv/dpi/common/tcp_server dv/dpi/usbdpi dv/verilator/cpp \
  dv/verilator/simutil_verilator/cpp ip/prim/dv/prim_secded)

# The vendored harness advances its clock explicitly; timed AST behavioral
# processes are incompatible with that harness on Verilator 5.032.
OT_VL_FLAGS := --cc --exe --build -j $(OT_VL_JOBS) --no-timing -Wno-fatal -Wno-lint -Wno-style \
  +define+AST_BYPASS_CLK +define+DMIDirectTAP +define+RV_CORE_IBEX_SIM_SRAM \
  "+define+VERILATOR_TEST_STATUS_ADDR=$(OT_VL_TEST_STATUS_ADDR)" \
  --top-module chip_sim_tb -Mdir $(BUILD_DIR)/obj_dir -o Vchip_sim_tb \
  -CFLAGS "-std=c++17 $(OT_VL_OPT) $(OT_VL_INC) -DTOPLEVEL_NAME=chip_sim_tb -DVM_TRACE=0" \
  -LDFLAGS "-lelf -lutil -pthread"

BUILD_OUTPUT = $(BUILD_DIR)/obj_dir/Vchip_sim_tb
COMP_CMD = test "$(OT_VL_JOBS)" -ge 1 && test "$(OT_VL_JOBS)" -le 4 && cd $(BUILD_DIR) && \
           { grep '^+incdir' $(FILELIST); grep -v '^+' $(FILELIST) | grep -Ev '$(OT_VL_EXCLUDE)'; \
             printf '%s\n' $(OT_VL_SV); } > $(OT_VL_FLIST) && \
           timeout --signal=KILL 1800 $(VERILATOR) $(OT_VL_FLAGS) $(USER_COMPILE_FLAGS_VERILATOR) -f $(OT_VL_FLIST) $(OT_VL_CPP) \
             2>&1 | tee compile.log; test $${PIPESTATUS[0]} -eq 0
ELAB_CMD =
# Include harness/DPI sources and local options in the incremental build key.
BUILD_EXTRA_DEPS += $(OT_VL_SV) $(OT_VL_CPP)
BUILD_METADATA += |ot_vl_opt=$(OT_VL_OPT)|ot_vl_jobs=$(OT_VL_JOBS)|ot_vl_status=$(OT_VL_TEST_STATUS_ADDR)|ot_vl_user=$(USER_COMPILE_FLAGS_VERILATOR)
.PHONY: verilator-sw
verilator-sw:
	@timeout --signal=KILL 900 bash $(OT_VL_SW_BUILD)

sim: comp verilator-sw

SIM_CMD = { test "$(TEST)" = chip_sw_uart_smoketest || { echo "[SIM] Verilator SW recipe supports chip_sw_uart_smoketest only"; exit 2; }; \
          test "$(OT_VL_TIMEOUT)" -ge 1 && test "$(OT_VL_TIMEOUT)" -le 2400 || { echo "[SIM] timeout must be 1..2400 seconds"; exit 2; }; \
          rm -f gpio0-read gpio0-write; \
          timeout --signal=KILL $(OT_VL_TIMEOUT) stdbuf -oL -eL $(BUILD_OUTPUT) --term-after-cycles=$(OT_VL_MAX_CYCLES) --verbose-mem-load \
            --meminit=rom0,$(OT_VL_ROM_IMG) --meminit=flash0,$(OT_VL_FLASH_IMG) \
            --meminit=otp,$(OT_VL_OTP_IMG) +UARTDPI_LOG_uart0=uart0.log $(USER_SIM_FLAGS_VERILATOR) > verilator-run.log 2>&1; \
          rc=$$?; cat verilator-run.log; \
          if [ $$rc -eq 0 ] && ! grep -q "^TEST PASSED CHECKS$$" verilator-run.log; then echo "[SIM] No test-status PASS (cycle limit or early exit)"; rc=1; fi; \
          echo "--- uart0.log ---"; cat uart0.log 2>/dev/null; exit $$rc; }
