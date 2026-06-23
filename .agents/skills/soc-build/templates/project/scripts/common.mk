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

PROJECT_ROOT := $(realpath $(PROJECT_ROOT))

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

include $(PROJECT_ROOT)/scripts/paths.mk
include $(PROJECT_ROOT)/scripts/config.mk

# Default top module: RTL module name in de/rtl, tb_ prefix otherwise
ifeq ($(CURRENT_DIR),de)
  TOP_MODULE ?= $(MODULE_NAME)
else ifeq ($(CURRENT_DIR),rtl)
  TOP_MODULE ?= $(MODULE_NAME)
else
  TOP_MODULE ?= tb_$(MODULE_NAME)
endif
RTL_TOP      ?= $(MODULE_NAME)

FILELIST     ?= $(CANONICAL_FLIST)

# Dependency filelists must be loaded before the rules below are parsed.
# This preserves the reference project's paths -> defs -> filelist -> rules order.
-include $(RTL_PATH)/filelist.mk

TB_FILES := $(shell find $(TB_PATH) -type f \( -name "*.v" -o -name "*.sv" \) 2>/dev/null | sort)
ACTIVE_FILELISTS := $(if $(strip $(MODULE_FILELISTS)),$(sort $(MODULE_FILELISTS)),$(RTL_PATH)/filelist.f)
FILELIST_MK_DEPS := $(sort $(filter %/filelist.mk,$(MAKEFILE_LIST)))

# If FILELIST is defined, extract sources (strip comments/empty lines, expand $SOC)
ifdef FILELIST
  FLIST_SRCS = $(shell sed '/^\#/d;/^\/\//d;/^$$/d' $(FILELIST) 2>/dev/null | sed 's|\$$SOC|$(SOC)|g')
endif

# Tool-specific commands are isolated like xuanwu9000's defs.<tool>.mk files.
TOOLCHAIN_MK := $(PROJECT_ROOT)/scripts/toolchains/$(SIMULATOR).mk
ifeq ($(wildcard $(TOOLCHAIN_MK)),)
  $(error Missing toolchain configuration: $(TOOLCHAIN_MK))
endif
include $(TOOLCHAIN_MK)

BUILD_METADATA = simulator=$(SIMULATOR)|top=$(TOP_MODULE)|timescale=$(TIMESCALE)|fsdb=$(FSDB)|coverage=$(COVERAGE)|partcomp=$(PARTCOMP)|vlog=$(VLOG_FLAGS)|elab=$(VCS_ELAB_FLAGS)|includes=$(VCS_INCLUDE_FLAGS)|iverilog=$(IVERILOG_FLAGS)|verilator=$(VERILATOR_FLAGS)|user_compile=$(USER_COMPILE_FLAGS)
BUILD_CONFIG_DEPS := $(PROJECT_ROOT)/scripts/common.mk $(PROJECT_ROOT)/scripts/config.mk $(TOOLCHAIN_MK) $(MODULE_PATH)/Makefile
BUILD_EXTRA_DEPS := $(BUILD_CONFIG_DEPS) $(RTL_PATH) $(TB_PATH)

# Verdi source browsing is simulator-independent; toolchains may override it.
VERDI_CMD ?= verdi $(VERDI_FLAGS) -top $(TOP_MODULE) -f $(FILELIST) &

# =============================================================================
# Lint & Synthesis configuration
# =============================================================================

SYN_NETLIST   = $(SYN_DIR)/$(RTL_TOP)_netlist.v
SYN_REPORT    = $(SYN_DIR)/synth.log

# =============================================================================
# Public targets
# =============================================================================

.PHONY: setup comp sim run test regress report coverage coverage-regress \
        coverage-report wave verdi debug-gui clean debugclean deepclean \
        flist validate-flist lint syn

setup:
	@echo "[SETUP] vibe_soc environment setup"
	@$(PROJECT_ROOT)/scripts/setup

comp: $(CANONICAL_FLIST)
	@mkdir -p $(SIM_DIR)
	@set -e; \
	new_fp="$$($(PYTHON_RUN) $(PROJECT_ROOT)/scripts/build_fingerprint.py \
		--filelist $(CANONICAL_FLIST) --metadata "$(BUILD_METADATA)" \
		$(foreach file,$(BUILD_EXTRA_DEPS),--extra $(file)))"; \
	if [[ "$(FORCE)" != "1" && -f "$(BUILD_FINGERPRINT)" && \
	      "$$new_fp" == "$$(cat $(BUILD_FINGERPRINT))" && -e "$(BUILD_OUTPUT)" ]]; then \
		echo "[COMP] Up to date: $(TOP_MODULE) ($(SIMULATOR))"; \
	else \
		echo "[COMP] Building: $(TOP_MODULE) ($(SIMULATOR))"; \
		$(COMP_CMD); \
		$(if $(ELAB_CMD),echo "[ELAB] Building: $(TOP_MODULE) ($(SIMULATOR))"; $(ELAB_CMD);) \
		printf '%s\n' "$$new_fp" > $(BUILD_FINGERPRINT).tmp; \
		mv $(BUILD_FINGERPRINT).tmp $(BUILD_FINGERPRINT); \
		echo "[COMP] Fingerprint: $$new_fp"; \
	fi

sim:
	@echo "[SIM] Running $(TOP_MODULE) ..."
	@mkdir -p $(SIM_DIR)
	@cd $(SIM_DIR) && $(SIM_CMD) | tee $(SIM_DIR)/sim.log

run: sim

test: comp
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/run_regression.py \
		--sim-dir $(SIM_DIR) --output-dir $(REGRESS_DIR)/single \
		--command "$(SIM_CMD)" --tests "$(TEST)" --seeds "$(SEED)" \
		--jobs 1 --pass-regex "$(REGRESS_PASS_REGEX)" \
		--matrix-args "$(REGRESS_MATRIX_ARGS)"

regress: comp
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/run_regression.py \
		--sim-dir $(SIM_DIR) --output-dir $(REGRESS_DIR) \
		--command "$(SIM_CMD)" --tests-file $(REGRESS_TEST_FILE) \
		--tests "$(REGRESS_TESTS)" --seeds "$(REGRESS_SEEDS)" \
		--jobs $(REGRESS_JOBS) --pass-regex "$(REGRESS_PASS_REGEX)" \
		--matrix-args "$(REGRESS_MATRIX_ARGS)"

report:
	@test -f $(REGRESS_DIR)/summary.txt || { echo "[REPORT] No regression summary"; exit 2; }
	@cat $(REGRESS_DIR)/summary.txt

coverage:
	@test "$(COVERAGE_SUPPORTED)" = "1" || { echo "[COV] $(SIMULATOR) coverage is not configured"; exit 2; }
	@$(MAKE) --no-print-directory comp COVERAGE=1 FORCE=$(FORCE)
	@$(MAKE) --no-print-directory sim COVERAGE=1
	@$(MAKE) --no-print-directory coverage-report COVERAGE=1

coverage-regress:
	@test "$(COVERAGE_SUPPORTED)" = "1" || { echo "[COV] $(SIMULATOR) coverage is not configured"; exit 2; }
	@$(MAKE) --no-print-directory comp COVERAGE=1 FORCE=$(FORCE)
	@$(MAKE) --no-print-directory regress COVERAGE=1
	@$(MAKE) --no-print-directory coverage-report COVERAGE=1

coverage-report:
	@test "$(COVERAGE_SUPPORTED)" = "1" || { echo "[COV] $(SIMULATOR) coverage is not configured"; exit 2; }
	@mkdir -p $(COV_REPORT_DIR)
	$(COVERAGE_REPORT_CMD)
	@echo "[COV] Report: $(COV_REPORT_DIR)"

wave:
	@echo "[WAVE] Opening waveform ..."
	$(WAVE_CMD)

verdi: $(CANONICAL_FLIST)
	@command -v verdi >/dev/null 2>&1 || { echo "[VERDI] verdi not found"; exit 127; }
	@echo "[VERDI] Opening source database for $(TOP_MODULE) ..."
	$(VERDI_CMD)

debug-gui:
	@test -n "$(DEBUG_GUI_CMD)" || { echo "[GUI] No compiled debug GUI for $(SIMULATOR)"; exit 2; }
	$(DEBUG_GUI_CMD)

clean:
	@echo "[CLEAN] Removing runtime artifacts; preserving compile cache ..."
	rm -rf $(SIM_DIR)/sim.log $(SIM_DIR)/wave.* $(SIM_DIR)/regress \
		$(SIM_DIR)/*.fsdb $(SIM_DIR)/*.vpd $(SIM_DIR)/*.vcd \
		$(SIM_DIR)/coverage.vdb $(MODULE_PATH)/dv/cov

debugclean: clean
	@echo "[DEBUGCLEAN] Removing reports and debug logs; preserving compiled image ..."
	rm -rf $(RUN_DIR)/* $(SIM_DIR)/verdiLog $(SIM_DIR)/novas.* \
		$(SIM_DIR)/urgReport $(SIM_DIR)/*.key

deepclean:
	@echo "[DEEPCLEAN] Removing all transient compile/simulation artifacts; preserving synthesis deliverables ..."
	rm -rf $(RUN_DIR) $(SIM_DIR) $(MODULE_PATH)/dv/cov
	rm -f $(SYN_DIR)/*.log

# --- flist: generate and validate a canonical filelist ---
flist: $(CANONICAL_FLIST)

validate-flist: $(CANONICAL_FLIST)
	@echo "[FLIST] Validation passed: $(CANONICAL_FLIST)"

$(RTL_PATH)/filelist.f:
	@mkdir -p $(RTL_PATH)
	@find $(RTL_PATH) -type f \( -name "*.v" -o -name "*.sv" \) \
		| sed 's|^$(PROJECT_ROOT)/|\$$SOC/|' | sort > $@
	@echo "[FLIST] Generated $@"

# --- Generate simulation filelist (RTL + TB) ---
$(SIM_FLIST): $(ACTIVE_FILELISTS) $(FILELIST_MK_DEPS) $(TB_FILES)
	@mkdir -p $(SIM_DIR)
	@> $@
	@for fl in $(ACTIVE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
	@find $(TB_PATH) \( -name "*.v" -o -name "*.sv" \) | sed 's|^$(PROJECT_ROOT)/|\$$SOC/|' | sort >> $@
	@echo "[FLIST] Generated $@"

$(CANONICAL_FLIST): $(SIM_FLIST) $(PROJECT_ROOT)/scripts/validate_filelist.py
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/validate_filelist.py $(SIM_FLIST) --output $@

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
	@verilator $(VERILATOR_FLAGS) --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog $(IVERILOG_FLAGS) -s $(RTL_TOP) -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
	@exit 2
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
