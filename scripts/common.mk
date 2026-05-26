# =============================================================================
# Common Makefile for SoC Project
# =============================================================================
# Usage: In module Makefile, define PROJECT_ROOT and optionally MODULE_NAME,
# then include this file:
#
#   PROJECT_ROOT ?= $(shell cd ../.. && pwd -P)
#   MODULE_NAME   = my_module
#   include $(PROJECT_ROOT)/scripts/common.mk
# =============================================================================

ifndef PROJECT_ROOT
  $(error PROJECT_ROOT must be defined before including common.mk)
endif

# =============================================================================
# Module auto-detection
# =============================================================================

# Detect current directory (handle SUBDIR for de/dv/rtl wrapper calls)
CURRENT_DIR := $(notdir $(CURDIR))
ifdef SUBDIR
  CURRENT_DIR := $(SUBDIR)
endif

# Compute module root path (walk up from de/dv/rtl subdirs)
MODULE_PATH := $(CURDIR)
ifndef SUBDIR
ifeq ($(CURRENT_DIR),de)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),dv)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),rtl)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
  MODULE_PATH := $(patsubst %/,%,$(dir $(MODULE_PATH)))
endif
endif

# Auto-derive module name from directory if not explicitly defined
ifndef MODULE_NAME
  MODULE_NAME := $(notdir $(MODULE_PATH))
endif

RTL_PATH      = $(MODULE_PATH)/de/rtl
TB_PATH       = $(MODULE_PATH)/dv/tb

# Default top module: RTL module name in de/rtl, tb_ prefix otherwise
ifeq ($(CURRENT_DIR),de)
  TOP_MODULE ?= $(MODULE_NAME)
else ifeq ($(CURRENT_DIR),rtl)
  TOP_MODULE ?= $(MODULE_NAME)
else
  TOP_MODULE ?= tb_$(MODULE_NAME)
endif
RTL_TOP      ?= $(MODULE_NAME)

RUN_DIR       = $(MODULE_PATH)/de/run
SIM_DIR       = $(MODULE_PATH)/dv/sim
SIM_FLIST     = $(SIM_DIR)/dut.f
FILELIST     ?= $(SIM_FLIST)

SIMULATOR    ?= iverilog
SOC          ?= $(PROJECT_ROOT)

# If FILELIST is defined, extract sources (strip comments/empty lines, expand $SOC)
ifdef FILELIST
  FLIST_SRCS = $(shell sed '/^\#/d;/^\/\//d;/^$$/d' $(FILELIST) 2>/dev/null | sed 's|\$$SOC|$(SOC)|g')
endif

# =============================================================================
# Simulator-specific commands
# =============================================================================

# --------------- VCS ---------------
ifeq ($(SIMULATOR),vcs)
ifdef FILELIST
COMP_CMD = vcs -sverilog -full64 -timescale=1ns/1ps \
           +v2k -debug_access+all -kdb \
           -f $(FILELIST) \
           -o $(SIM_DIR)/simv
else
COMP_CMD = vcs -sverilog -full64 -timescale=1ns/1ps \
           +v2k -debug_access+all -kdb \
           $(RTL_FILES) $(TB_FILES) \
           -o $(SIM_DIR)/simv
endif
SIM_CMD  = $(SIM_DIR)/simv +vpdfile+$(SIM_DIR)/wave.vpd
WAVE_CMD = dve -vpd $(SIM_DIR)/wave.vpd &
endif

# --------------- Verilator ----------
ifeq ($(SIMULATOR),verilator)
ifdef FILELIST
COMP_CMD = verilator --cc --exe --build --trace \
           -CFLAGS "-std=c++17" \
           -Mdir $(SIM_DIR)/obj_dir \
           --top-module $(TOP_MODULE) \
           $(FLIST_SRCS) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = verilator --cc --exe --build --trace \
           -CFLAGS "-std=c++17" \
           -Mdir $(SIM_DIR)/obj_dir \
           --top-module $(TOP_MODULE) \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = $(SIM_DIR)/obj_dir/V$(TOP_MODULE) \
           +trace +wavefile=$(SIM_DIR)/wave.vcd
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
endif

# --------------- Icarus -------------
ifeq ($(SIMULATOR),iverilog)
ifdef FILELIST
COMP_CMD = iverilog -g2012 -s $(TOP_MODULE) -o $(SIM_DIR)/sim.out \
           $(FLIST_SRCS) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = iverilog -g2012 -s $(TOP_MODULE) -o $(SIM_DIR)/sim.out \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = vvp $(SIM_DIR)/sim.out +dumpfile=$(SIM_DIR)/wave.vcd
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
endif

# --------------- Xcelium ------------
ifeq ($(SIMULATOR),xcelium)
ifdef FILELIST
COMP_CMD = xrun -sv -timescale 1ns/1ps -access +rwc \
           -f $(FILELIST) \
           -xmlibdirpath $(SIM_DIR)/work \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = xrun -sv -timescale 1ns/1ps -access +rwc \
           $(RTL_FILES) $(TB_FILES) \
           -xmlibdirpath $(SIM_DIR)/work \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = xrun -R -input $(SIM_DIR)/wave.tcl
WAVE_CMD = simvisdbutil $(SIM_DIR)/wave.shm &
endif

# =============================================================================
# Lint & Synthesis configuration
# =============================================================================

LINT_TOOL    ?= verilator

SYN_DIR       = $(MODULE_PATH)/de/syn
SYN_NETLIST   = $(SYN_DIR)/$(RTL_TOP)_netlist.v
SYN_REPORT    = $(SYN_DIR)/synth.log

# =============================================================================
# Public targets
# =============================================================================

.PHONY: setup comp sim run wave clean flist lint syn

setup:
	@echo "[SETUP] vibe_soc environment setup"
	@$(PROJECT_ROOT)/scripts/setup

comp:
	@echo "[COMP] Simulator: $(SIMULATOR) | Top: $(TOP_MODULE)"
	@mkdir -p $(SIM_DIR)
ifndef RTL_FILES
	@$(MAKE) $(SIM_FLIST)
endif
	$(COMP_CMD)

sim:
	@echo "[SIM] Running $(TOP_MODULE) ..."
	@mkdir -p $(SIM_DIR)
	@cd $(SIM_DIR) && $(SIM_CMD) | tee $(SIM_DIR)/sim.log

run: sim

wave:
	@echo "[WAVE] Opening waveform ..."
	$(WAVE_CMD)

clean:
	@echo "[CLEAN] Removing run artifacts ..."
	rm -rf $(RUN_DIR)/* $(RUN_DIR)/.vlogan* csrc simv* ucli.key vc_hdrs.h
	rm -rf $(SIM_DIR)/* $(SIM_DIR)/.vlogan* csrc simv* ucli.key vc_hdrs.h
	rm -rf obj_dir work *.log *.vpd *.vcd

# --- flist: generate RTL filelist ---
flist:
	@mkdir -p $(RTL_PATH) $(TB_PATH) $(RUN_DIR) $(SIM_DIR)
	@if [ ! -f $(RTL_PATH)/filelist.f ]; then \
		find $(RTL_PATH) -maxdepth 1 \( -name "*.v" -o -name "*.sv" \) | sed 's|^$(PROJECT_ROOT)/|\$$SOC/|' | sort > $(RTL_PATH)/filelist.f; \
		echo "[FLIST] Generated $(RTL_PATH)/filelist.f"; \
	else \
		echo "[FLIST] $(RTL_PATH)/filelist.f already exists, skip"; \
	fi

# --- Generate simulation filelist (RTL + TB) ---
$(SIM_FLIST): flist
	@mkdir -p $(SIM_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@cat $(RTL_PATH)/filelist.f >> $@
endif
	@find $(TB_PATH) \( -name "*.v" -o -name "*.sv" \) | sed 's|^$(PROJECT_ROOT)/|\$$SOC/|' | sort >> $@
	@echo "[FLIST] Generated $@"

# --- lint: static check on RTL only ---
lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; \
			sed 's|\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; \
			echo "" >> $(RUN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
	@verilator --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log || true
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log || true
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
endif
	@echo "[LINT] Report: $(RUN_DIR)/lint.log"

# --- syn: Yosys synthesis ---
syn: flist
	@echo "[SYN] Yosys | Top: $(RTL_TOP)"
	@mkdir -p $(SYN_DIR)
	@> $(SYN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			sed 's|\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(SYN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(SYN_DIR)/rtl.f
endif
	@if [ ! -s $(SYN_DIR)/rtl.f ]; then \
		echo "[SYN] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
	@echo "# Auto-generated Yosys synthesis script for $(RTL_TOP)" > $(SYN_DIR)/syn.ys
	@echo "read_verilog $$(grep -v '^#' $(SYN_DIR)/rtl.f | grep -v '^//' | grep -v '^$$' | tr '\n' ' ')" >> $(SYN_DIR)/syn.ys
	@echo "hierarchy -check -top $(RTL_TOP)" >> $(SYN_DIR)/syn.ys
	@echo "proc; flatten; opt; fsm; opt; memory; opt; techmap; opt" >> $(SYN_DIR)/syn.ys
	@echo "write_verilog $(notdir $(SYN_NETLIST))" >> $(SYN_DIR)/syn.ys
	@echo "stat" >> $(SYN_DIR)/syn.ys
	@cd $(SYN_DIR) && yosys syn.ys 2>&1 | tee $(notdir $(SYN_REPORT))
	@echo "[SYN] Netlist: $(SYN_NETLIST)"
	@echo "[SYN] Report:  $(SYN_REPORT)"
