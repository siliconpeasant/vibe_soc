# top module
PROJECT_ROOT ?= $(shell cd ../.. && pwd -P)
MODULE_NAME   = vibe_soc_top
TEST ?= default
LOCAL_CURRENT_DIR := $(if $(SUBDIR),$(SUBDIR),$(notdir $(CURDIR)))

OT_VENDOR := 1
OT_SMOKE_TESTS := chip_sw_uart_smoketest
ifeq ($(TEST),default)
  TEST := chip_sw_uart_smoketest
endif

  RTL_TOP    = chip_earlgrey_asic
  ifeq ($(LOCAL_CURRENT_DIR),de)
    TOP_MODULE = $(RTL_TOP)
  else
    TOP_MODULE ?= tb
  endif
  FSDB ?= 0
  VERDI_HOME ?= /usr/Synopsys/verdi/T-2022.06
  OT_WAVES ?= $(if $(filter 1,$(FSDB)),fsdb,none)
  ifeq ($(FSDB),1)
    VCS_KDB ?= 1
  endif
  OT_VENDOR_ROOT := $(PROJECT_ROOT)/chip/top/de/rtl/vendor/opentitan
  OT_HW_DV_ROOT := $(OT_VENDOR_ROOT)/hw/dv
  OT_SIM_TCL := $(OT_HW_DV_ROOT)/tools/sim.tcl
  OT_STATIC_GEN_ROOT := $(PROJECT_ROOT)/chip/top/de/rtl/generated/opentitan_fusesoc
  OT_STATIC_GEN_SRC_ROOT := $(OT_STATIC_GEN_ROOT)/src
  OT_TB_ROOT := $(PROJECT_ROOT)/chip/top/dv/tb
  OT_TEST_CFG_ROOT := $(OT_TB_ROOT)/tests
  OT_SW_ROOT := $(OT_TB_ROOT)/sw
  OT_OTP_DIR := $(OT_SW_ROOT)/common/otp
  OT_TEST_ROM_DIR := $(OT_SW_ROOT)/common/test_rom
  OT_CASE_SW_ROOT := $(OT_SW_ROOT)/cases
  OT_CASE_SW_DIR := $(OT_CASE_SW_ROOT)/$(TEST)
  OT_TEST_CFG := $(OT_TEST_CFG_ROOT)/opentitan_cases.manifest.json
  OT_TEST_CFG_PY := $(OT_TB_ROOT)/scripts/opentitan_test_cfg.py
  OT_TEST_CFG_PYTHON_BIN := $(shell for name in python3.12 python3.11 python3.10 python3.9 python3.8; do path=$$(command -v $$name 2>/dev/null); if [ -n "$$path" ]; then echo $$path; break; fi; done)
  ifeq ($(strip $(OT_TEST_CFG_PYTHON_BIN)),)
    $(error Python 3.8 or newer is required for OpenTitan test index queries)
  endif
  OT_TEST_CFG_PYTHON := env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp $(OT_TEST_CFG_PYTHON_BIN)
  ifeq ($(wildcard $(OT_TEST_CFG)),)
    $(error Missing OpenTitan test index manifest: $(OT_TEST_CFG))
  endif
  OT_CFG = $(shell $(OT_TEST_CFG_PYTHON) $(OT_TEST_CFG_PY) $(OT_TEST_CFG) $(TEST) $(1))
  OT_TEST_STATUS := $(call OT_CFG,status)
  ifeq ($(strip $(OT_TEST_STATUS)),)
    $(error Missing or invalid OpenTitan test in index: $(TEST))
  endif
  OT_UVM_TEST := $(call OT_CFG,uvm_test)
  OT_UVM_TEST_SEQ := $(call OT_CFG,uvm_sequence)
  OT_RUN_OPTS := $(call OT_CFG,run_opts)
  OT_COMPILE_OPTS := $(call OT_CFG,compile_opts)
  OT_SW_IMAGES := $(call OT_CFG,sw_images)
  OT_COPY_SW_COLLATERAL = find $(OT_OTP_DIR) $(OT_TEST_ROM_DIR) $(OT_CASE_SW_DIR) -maxdepth 1 -type f \( -name 'otp_ctrl_img_*.vmem' -o -name '*_sim_dv.logs.txt' -o -name '*_sim_dv.rodata.txt' \) -exec cp -f {} . \;
  OT_CLEAN_WAVES_IF_DISABLED = $(if $(filter 1,$(FSDB)),:,rm -f waves.fsdb wave.fsdb waves.fsdb.* wave.fsdb.* novas_dump.log)
  USER_COMPILE_FLAGS += +define+TOP_LEVEL_DV +define+UVM +define+UVM_NO_DEPRECATED
  USER_COMPILE_FLAGS += +define+UVM_REGEX_NO_DPI +define+UVM_NO_RELNOTES
  USER_COMPILE_FLAGS += +define+UVM_REG_ADDR_WIDTH=32 +define+UVM_REG_DATA_WIDTH=64
  USER_COMPILE_FLAGS += +define+UVM_REG_BYTENABLE_WIDTH=8 +define+SIMULATION
  USER_COMPILE_FLAGS += +define+DUT_HIER=tb.dut +define+VCS
  USER_COMPILE_FLAGS += -sverilog -full64 -licqueue -ntb_opts uvm-1.2
  USER_COMPILE_FLAGS += -lca +incdir+$(OT_STATIC_GEN_SRC_ROOT)
  USER_COMPILE_FLAGS += +warn=SV-NFIVC +warn=noUII-L +warn=noLCA_FEATURES_ENABLED +warn=noBNA
  USER_COMPILE_FLAGS += -assert svaext -xlrm uniq_prior_final
  USER_COMPILE_FLAGS += -debug_region=cell+lib -debug_access+f -debug_access
  USER_COMPILE_FLAGS += -error=IPDW -error=UPF_ISPND -error=IGPA -error=PCSRMIO
  USER_COMPILE_FLAGS += -error=AOUP -error=ELW_UNBOUND -error=IUWI -error=INAV
  USER_COMPILE_FLAGS += -error=SV-ISC -error=OSVF-NPVIUFPI -error=DPIMI
  USER_COMPILE_FLAGS += -error=IPDASP -error=CM-HIER-FNF -error=CWUC
  USER_COMPILE_FLAGS += -error=MATN -error=STASKW_NDTAZ1 -error=TMPO
  USER_COMPILE_FLAGS += -error=SV-OHCM -error=ENUMASSIGN -error=TEIF
  USER_COMPILE_FLAGS += -deraceclockdata $(VCS_KDB_COMPILE_FLAGS)
  USER_COMPILE_FLAGS += -xprop=$(OT_VENDOR_ROOT)/hw/top_earlgrey/dv/vcs_xprop.cfg -xprop=mmsopt
  USER_COMPILE_FLAGS += -Xcflags='-Wno-error=implicit-function-declaration'
  USER_COMPILE_FLAGS += -CFLAGS --std=c99 -CFLAGS -fno-extended-identifiers -CFLAGS -std=c++11
  USER_COMPILE_FLAGS += -CFLAGS -DEVP_CTRL_AEAD_GET_TAG=0x10 -CFLAGS -DEVP_CTRL_AEAD_SET_TAG=0x11
  USER_COMPILE_FLAGS += -LDFLAGS -Wl,--no-as-needed
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/ip/aes/model
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/ip/aes/dv/aes_model_dpi
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/ip/kmac/dv/dpi
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/ip/prim/dv/prim_prince/crypto_dpi_prince
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/ip/prim/dv/prim_present/crypto_dpi_present
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/dv/dpi/gpiodpi
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/dv/dpi/uartdpi
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/dv/dpi/usbdpi
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_VENDOR_ROOT)/hw/dv/dpi/common/tcp_server
  USER_COMPILE_FLAGS += -CFLAGS -I$(OT_STATIC_GEN_SRC_ROOT)
  USER_COMPILE_FLAGS += -LDFLAGS /usr/lib64/libelf.so.1
  ifneq ($(LOCAL_CURRENT_DIR),de)
    OT_BIND_TOPS += -top clkmgr_bind -top pwrmgr_bind -top rstmgr_bind
    OT_BIND_TOPS += -top sec_cm_prim_onehot_check_bind
    OT_BIND_TOPS += -top sec_cm_prim_sparse_fsm_flop_bind
    OT_BIND_TOPS += -top spi_host_bind -top top_earlgrey_error_injection_ifs_bind
    OT_BIND_TOPS += -top top_earlgrey_bind -top xbar_main_bind -top xbar_peri_bind
  endif
  USER_COMPILE_FLAGS += -lcrypto
  USER_COMPILE_FLAGS += -lutil
  USER_COMPILE_FLAGS += $(OT_COMPILE_OPTS)
  USER_SIM_FLAGS += +UVM_TESTNAME=$(OT_UVM_TEST)
  USER_SIM_FLAGS += +sw_build_device=sim_dv +cdc_instrumentation_enabled=1
  USER_SIM_FLAGS += +UVM_NO_RELNOTES +UVM_VERBOSITY=UVM_LOW
  USER_SIM_FLAGS += -licqueue -ucli -do $(OT_SIM_TCL)
  USER_SIM_FLAGS += -xlrm hier_inst_seed -assert nopostproc
  USER_SIM_FLAGS += +UVM_TEST_SEQ=$(OT_UVM_TEST_SEQ)
  USER_SIM_FLAGS += $(OT_RUN_OPTS)
  ifneq ($(strip $(OT_SW_IMAGES)),)
    USER_SIM_FLAGS += +sw_images=$(OT_SW_IMAGES)
  endif
  ifneq (,$(filter $(OT_SMOKE_TESTS),$(TEST)))
    OT_SMOKE_PREBUILT_SIMV ?= /project/xuanwu9000/user/silicon/opentitan-master/scratch/master/chip_earlgrey_asic-sim-vcs/default/simv
    OT_USE_PREBUILT_SIMV ?= 0
    REGRESS_PASS_REGEX ?= TEST PASSED CHECKS|SW TEST PASSED
  endif
include $(PROJECT_ROOT)/scripts/common.mk

ifeq ($(FSDB),1)
  # OpenTitan's VCS wave mode uses the KDB/debug build mode and switches dumping at
  # runtime through WAVES=fsdb. Avoid the generic scaffold FSDB compile/link flags.
  VCS_FSDB_COMPILE_FLAGS :=
  VCS_FSDB_ELAB_FLAGS :=
  VCS_SIM_FLAGS := +vcs+lic+wait +ntb_random_seed=$(SEED)
endif

ifeq ($(OT_USE_PREBUILT_SIMV),1)
BUILD_OUTPUT = $(SIM_DIR)/.ot_smoke_prebuilt_simv
COMP_CMD = test -x $(OT_SMOKE_PREBUILT_SIMV) && touch $(BUILD_OUTPUT)
ELAB_CMD =
SIM_CMD = $(OT_COPY_SW_COLLATERAL) && $(OT_CLEAN_WAVES_IF_DISABLED) && \
          env SIMULATOR=vcs WAVES=$(OT_WAVES) GUI=$(GUI) GUI_DEBUG=0 TB_TOP=tb \
          VERDI_HOME=$(VERDI_HOME) NOVAS_HOME=$(VERDI_HOME) dv_root=$(OT_HW_DV_ROOT) $(OT_SMOKE_PREBUILT_SIMV) $(VCS_SIM_FLAGS) $(USER_SIM_FLAGS)
else
COMP_CMD = cd $(BUILD_DIR) && \
           $(VCS_EXE) $(USER_COMPILE_FLAGS) $(VCS_FSDB_COMPILE_FLAGS) $(VCS_FSDB_ELAB_FLAGS) \
           -timescale=$(TIMESCALE) -Mdir=$(BUILD_DIR)/simv.csrc \
           $(OT_BIND_TOPS) -top $(TOP_MODULE) -f $(FILELIST) -o simv -l compile.log
ELAB_CMD =
SIM_CMD = $(OT_COPY_SW_COLLATERAL) && $(OT_CLEAN_WAVES_IF_DISABLED) && \
          env SIMULATOR=vcs WAVES=$(OT_WAVES) GUI=$(GUI) GUI_DEBUG=0 TB_TOP=tb \
          VERDI_HOME=$(VERDI_HOME) NOVAS_HOME=$(VERDI_HOME) dv_root=$(OT_HW_DV_ROOT) ./simv $(VCS_SIM_FLAGS) $(USER_SIM_FLAGS)
endif
