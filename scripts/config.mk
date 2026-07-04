# Project-wide build defaults. Override from the command line or scripts/local.mk.

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
TMPDIR := /tmp
export TMPDIR
PYTHON3 ?= $(shell for name in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do \
  path=$$(command -v $$name 2>/dev/null); \
  if [ -n "$$path" ] && env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp $$path \
    -c 'import sys,tempfile; assert sys.version_info >= (3,8); assert tempfile.gettempdir() == "/tmp"' \
    >/dev/null 2>&1; then echo $$path; break; fi; \
done)
PYTHON_RUN := env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(TMPDIR) $(PYTHON3)

ifeq ($(strip $(PYTHON3)),)
  $(error Python 3.8 or newer is required for build automation)
endif

SUPPORTED_SIMULATORS := iverilog verilator vcs xcelium

SIMULATOR ?= vcs
LINT_TOOL ?= verilator
TIMESCALE ?= 1ns/1ps
SEED      ?= 1
TEST      ?= default
GUI       ?= 0
FSDB      ?= 0
PARTCOMP  ?= 1
FORCE     ?= 0
COVERAGE  ?= 0
SYN_TOOL  ?= yosys
SUPPORTED_SYN_TOOLS := yosys dc

REGRESS_TESTS      ?= default
REGRESS_SEEDS      ?= 1
REGRESS_JOBS       ?= 1
REGRESS_TEST_FILE  ?= $(MODULE_PATH)/dv/tests/tests.list
REGRESS_PASS_REGEX ?=

COV_METRICS ?= line+branch+cond+tgl+fsm+assert

IVERILOG ?= iverilog
VVP      ?= vvp
IVERILOG_FLAGS ?= -g2012
VVP_FLAGS      ?=
VERILATOR             ?= verilator
VERILATOR_BIN         := $(realpath $(shell command -v $(VERILATOR) 2>/dev/null))
VERILATOR_PREFIX      := $(patsubst %/bin/,%,$(dir $(VERILATOR_BIN)))
VERILATOR_ROOT        ?= $(VERILATOR_PREFIX)/share/verilator
VERILATOR_FLAGS        ?= -Wall --language 1800-2012
VERILATOR_LINT_FLAGS   ?= $(VERILATOR_FLAGS)
VERILATOR_THREADS      ?=
VERILATOR_TRACE        ?= 1
VERILATOR_TRACE_FORMAT ?= vcd
VERILATOR_MODEL        ?= V$(TOP_MODULE)
VERILATOR_TRACE_FLAGS  ?= $(if $(filter 1 true yes,$(VERILATOR_TRACE)),--trace $(if $(filter fst,$(VERILATOR_TRACE_FORMAT)),--trace-fst,) --trace-structs --trace-params --trace-max-array 1024,)
VERILATOR_SIM_FLAGS    ?= $(VERILATOR_FLAGS) -Wno-fatal --unroll-count 512 $(if $(strip $(VERILATOR_THREADS)),--threads $(VERILATOR_THREADS),) $(VERILATOR_TRACE_FLAGS)
VERILATOR_CFLAGS       ?= -std=c++11 -Wall $(if $(filter fst,$(VERILATOR_TRACE_FORMAT)),-DVM_TRACE_FMT_FST,) -DTOPLEVEL_NAME=$(VERILATOR_MODEL) -DTOPLEVEL_HEADER=$(VERILATOR_MODEL).h
VERILATOR_EXTRA_LDFLAGS ?=
VERILATOR_LDFLAGS      ?= -pthread -lutil $(VERILATOR_EXTRA_LDFLAGS)
VERILATOR_RTL_SRCS     ?= $(filter-out $(TB_FILES),$(FLIST_SRCS))
VERILATOR_SV_FILES     ?= $(wildcard $(TB_PATH)/*_verilator.sv $(TB_PATH)/*_verilator.v)
VERILATOR_CPP_FILES    ?= $(wildcard $(TB_PATH)/*_verilator.cc $(TB_PATH)/*_verilator.cpp $(MODULE_PATH)/dv/verif/*_verilator.cc $(MODULE_PATH)/dv/verif/*_verilator.cpp)
VERILATOR_HARNESS      ?= $(if $(strip $(VERILATOR_CPP_FILES)),$(VERILATOR_CPP_FILES),$(PROJECT_ROOT)/scripts/verilator/generic_main.cpp)
LINT_RUN_DIR        ?= $(RUN_DIR)/lint
LINT_LOG          ?= $(LINT_RUN_DIR)/lint.log
CDC_RUN_DIR         ?= $(RUN_DIR)/cdc
CDC_LOG             ?= $(CDC_RUN_DIR)/cdc.log
CDC_SDC             ?= $(firstword $(wildcard $(MODULE_PATH)/de/cdc/*.sdc $(MODULE_PATH)/de/syn/$(RTL_TOP).sdc $(MODULE_PATH)/de/syn/$(MODULE_NAME).sdc $(MODULE_PATH)/de/syn/final.sdc))
CDC_TOOL            ?= spyglass
SG_HOME             ?= $(if $(SPYGLASS_HOME),$(SPYGLASS_HOME),/usr/Synopsys/spyglass/latest)
SG_SHELL            ?= $(SG_HOME)/bin/sg_shell
SG_LINT_RUN_DIR     ?= $(RUN_DIR)/lint_spyglass
SG_LINT_LOG         ?= $(SG_LINT_RUN_DIR)/sg_lint.log
SG_LINT_REPORT      ?= $(SG_LINT_RUN_DIR)/moresimple.rpt
SG_LINT_TCL         ?= $(PROJECT_ROOT)/scripts/lint/sg_lint.tcl
SG_LINT_GOAL        ?= lint/lint_rtl
SG_LINT_METHODOLOGY ?= $(SG_HOME)/GuideWare/latest/soc/rtl_handoff
SG_LINT_PROJECT_DIR ?= $(SG_LINT_RUN_DIR)/$(RTL_TOP)_lint
SG_CDC_TCL          ?= $(PROJECT_ROOT)/scripts/cdc/sg_cdc.tcl
SG_CDC_GOAL         ?= cdc/cdc_verify_struct
SG_CDC_METHODOLOGY  ?= $(SG_HOME)/GuideWare/latest/soc/rtl_handoff
SG_CDC_SGDC         ?= $(firstword $(wildcard $(MODULE_PATH)/de/cdc/*.sgdc))
SG_CDC_CLOCK_PORT   ?= clk
SG_CDC_RESET_PORT   ?= rst_n
SG_CDC_RESET_VALUE  ?= 0
SG_CDC_PROJECT_DIR  ?= $(CDC_RUN_DIR)/$(RTL_TOP)_cdc
SG_CDC_GUI          ?= $(GUI)
SG_CDC_GUI_LOG      ?= $(CDC_RUN_DIR)/spyglass_gui.log
VLOG_FLAGS      ?= +systemverilogext+.sv+.svi+.svh+.v \
                   -extinclude \
                   +libext+.vlib+.v+.sv+.svi+.svh+.vt+.vp+.defs \
                   +vcs+lic+wait +lint=TFIPC-L \
                   +define+VCS +define+RTL_SIM +define+UVM1P2 \
                   -sverilog -nc -full64 -lca \
                   -xlrm floating_pnt_constraint
VCS_KDB         ?= 0
VCS_KDB_COMPILE_FLAGS ?= $(if $(filter 1 true yes,$(VCS_KDB)),-kdb,)
VCS_KDB_ELAB_FLAGS    ?= $(if $(filter 1 true yes,$(VCS_KDB)),-kdb -debug_access+pp,)
VCS_ELAB_FLAGS  ?= +vcs+lic+wait +notimingcheck -full64 -lca \
                   -xlrm floating_pnt_constraint \
                   +vcs+initreg+random $(VCS_KDB_ELAB_FLAGS)
VCS_SIM_FLAGS   ?= +vcs+lic+wait +ntb_random_seed=$(SEED) +vcs+flush+log +vcs+flush+dump
VCS_HW_ROOT     ?= $(PROJECT_ROOT)
VCS_UVM_HOME    ?= $(VCS_HOME)/etc/uvm-1.2
VCS_DW_SIM_PATH ?=
XCELIUM_FLAGS   ?= -64bit -sv -access +rwc
XCELIUM_SIM_FLAGS ?= -seed $(SEED)

YOSYS ?= yosys
DC_SHELL          ?= dc_shell
DC_SCRIPT         ?= $(PROJECT_ROOT)/scripts/syn/dc_synth.tcl
DC_SETUP_TCL      ?= $(firstword $(wildcard $(MODULE_PATH)/de/syn/dc_setup.tcl))
DC_SDC            ?= $(firstword $(wildcard $(MODULE_PATH)/de/syn/$(RTL_TOP).sdc $(MODULE_PATH)/de/syn/$(MODULE_NAME).sdc $(MODULE_PATH)/de/syn/final.sdc))
DC_RUN_DIR        ?= $(SYN_DIR)/dc
DC_WORK_DIR       ?= $(DC_RUN_DIR)/work
DC_REPORT_DIR     ?= $(DC_RUN_DIR)/reports
DC_OUTPUT_DIR     ?= $(DC_RUN_DIR)/outputs
SKY130HD_DC_DB    ?=
SKY130HD_DC_LIB   ?=
DC_TARGET_LIBRARY ?=
DC_LINK_LIBRARY   ?=
DC_SYMBOL_LIBRARY ?=
DC_SEARCH_PATH    ?= $(RTL_PATH) $(MODULE_PATH) $(PROJECT_ROOT)
DC_COMPILE_ULTRA  ?= 1
DC_CLOCK_GATING   ?= 0
DC_MAX_CORES      ?= 1

USER_COMPILE_FLAGS ?=
USER_SIM_FLAGS     ?=
VERDI_FLAGS        ?= -sverilog +libext+.v+.sv+.svh

# Optional per-user settings. This file is intentionally not required.
-include $(PROJECT_ROOT)/scripts/local.mk

# Support relocatable user-local Icarus installs. Some packaged iverilog
# binaries keep a compiled-in /usr/lib64/ivl backend path even when the real
# backend lives next to the binary under ~/.local/usr/lib64/ivl.
IVERILOG_REAL := $(realpath $(shell command -v $(IVERILOG) 2>/dev/null))
IVERILOG_PREFIX := $(patsubst %/bin/,%,$(dir $(IVERILOG_REAL)))
IVERILOG_BACKEND ?= $(firstword \
  $(wildcard $(IVERILOG_PREFIX)/lib64/ivl) \
  $(wildcard $(IVERILOG_PREFIX)/lib/ivl))
ifneq ($(wildcard $(IVERILOG_BACKEND)/ivlpp),)
  ifeq (,$(findstring -B,$(IVERILOG_FLAGS)))
    IVERILOG_FLAGS += -B $(IVERILOG_BACKEND)
  endif
  ifeq (,$(findstring -M,$(VVP_FLAGS)))
    VVP_FLAGS += -M $(IVERILOG_BACKEND)
  endif
endif

# Make/MCP child processes do not always inherit shell license variables.
export SNPSLMD_LICENSE_FILE LM_LICENSE_FILE CDS_LIC_FILE

ifeq (,$(filter $(SIMULATOR),$(SUPPORTED_SIMULATORS)))
  $(error Unsupported SIMULATOR '$(SIMULATOR)'; choose one of: $(SUPPORTED_SIMULATORS))
endif

ifeq (,$(filter $(SYN_TOOL),$(SUPPORTED_SYN_TOOLS)))
  $(error Unsupported SYN_TOOL '$(SYN_TOOL)'; choose one of: $(SUPPORTED_SYN_TOOLS))
endif
