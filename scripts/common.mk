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

# Default top module: DUT top in de/rtl, tb_ prefix otherwise
ifeq ($(CURRENT_DIR),de)
  TOP_MODULE ?= $(RTL_TOP)
else ifeq ($(CURRENT_DIR),rtl)
  TOP_MODULE ?= $(RTL_TOP)
else
  TOP_MODULE ?= tb_$(MODULE_NAME)
endif
RTL_TOP      ?= $(MODULE_NAME)

FILELIST     ?= $(if $(filter de rtl,$(CURRENT_DIR)),$(RTL_FLIST),$(CANONICAL_FLIST))

# Dependency filelists must be loaded before the rules below are parsed.
# This preserves the reference project's paths -> defs -> filelist -> rules order.
-include $(RTL_PATH)/filelist.mk

TB_FILELIST ?= $(TB_PATH)/filelist.f
TB_FILES := $(shell find $(TB_PATH) -type f \( -name "*.v" -o -name "*.sv" \) 2>/dev/null | sort)
ACTIVE_FILELISTS := $(if $(strip $(MODULE_FILELISTS)),$(MODULE_FILELISTS),$(RTL_PATH)/filelist.f)
ACTIVE_DV_FILELISTS := $(if $(filter de rtl,$(CURRENT_DIR)),,$(wildcard $(TB_FILELIST)))
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

BUILD_METADATA = simulator=$(SIMULATOR)|top=$(TOP_MODULE)|timescale=$(TIMESCALE)|fsdb=$(FSDB)|coverage=$(COVERAGE)|partcomp=$(PARTCOMP)|vlog=$(VLOG_FLAGS)|vcs_kdb=$(VCS_KDB)|vcs_kdb_compile=$(VCS_KDB_COMPILE_FLAGS)|elab=$(VCS_ELAB_FLAGS)|includes=$(VCS_INCLUDE_FLAGS)|iverilog=$(IVERILOG_FLAGS)|verilator_bin=$(VERILATOR)|verilator_root=$(VERILATOR_ROOT)|verilator=$(VERILATOR_SIM_FLAGS)|verilator_cflags=$(VERILATOR_CFLAGS)|verilator_ldflags=$(VERILATOR_LDFLAGS)|verilator_harness=$(VERILATOR_HARNESS)|verilator_sv=$(VERILATOR_SV_FILES)|user_compile=$(USER_COMPILE_FLAGS)
BUILD_CONFIG_DEPS := $(PROJECT_ROOT)/scripts/common.mk $(PROJECT_ROOT)/scripts/config.mk $(TOOLCHAIN_MK) $(MODULE_PATH)/Makefile
BUILD_EXTRA_DEPS := $(BUILD_CONFIG_DEPS) $(RTL_PATH) $(if $(filter de rtl,$(CURRENT_DIR)),,$(TB_PATH) $(ACTIVE_DV_FILELISTS))

# Verdi source browsing is simulator-independent; toolchains may override it.
VERDI_CMD ?= cd $(SIM_DIR) && verdi $(VERDI_FLAGS) -top $(TOP_MODULE) -f $(FILELIST) &

# =============================================================================
# Lint & Synthesis configuration
# =============================================================================

SYN_NETLIST   = $(SYN_DIR)/$(RTL_TOP)_netlist.v
SYN_REPORT    = $(SYN_DIR)/synth.log
YOSYS_SYN_SCRIPT = $(SYN_DIR)/syn.ys
DC_NETLIST    = $(DC_OUTPUT_DIR)/$(RTL_TOP)_netlist.v
DC_DDC        = $(DC_OUTPUT_DIR)/$(RTL_TOP).ddc
DC_SDF        = $(DC_OUTPUT_DIR)/$(RTL_TOP).sdf
DC_SDC_OUT    = $(DC_OUTPUT_DIR)/$(RTL_TOP).sdc
DC_LOG        = $(DC_RUN_DIR)/dc_shell.log

# =============================================================================
# Public targets
# =============================================================================

.PHONY: setup comp sim run test regress report coverage coverage-regress \
        coverage-report verdi clean debugclean deepclean \
        flist validate-flist lint cdc syn

setup:
	@echo "[SETUP] vibe_soc environment setup"
	@$(PROJECT_ROOT)/scripts/setup

comp: $(FILELIST)
	@mkdir -p $(BUILD_DIR)
	@set -e; \
	new_fp="$$($(PYTHON_RUN) $(PROJECT_ROOT)/scripts/build_fingerprint.py \
		--filelist $(FILELIST) --metadata "$(BUILD_METADATA)" \
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
	@cd $(SIM_DIR) && $(SIM_CMD) > $(SIM_DIR)/sim.log 2>&1
	@cat $(SIM_DIR)/sim.log

run: sim

test: comp
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/run_regression.py \
		--sim-dir $(SIM_DIR) --output-dir $(REGRESS_DIR)/single \
		--command "$(SIM_CMD)" --tests "$(TEST)" --seeds "$(SEED)" \
		--jobs 1 --pass-regex "$(REGRESS_PASS_REGEX)" \
		--matrix-args "$(REGRESS_MATRIX_ARGS)"

ifeq ($(REGRESS_RECURSIVE_MAKE),1)
regress:
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/run_regression.py \
		--sim-dir $(SIM_DIR) --output-dir $(REGRESS_DIR) \
		--make-module-dir $(MODULE_PATH) --make-simulator "$(SIMULATOR)" \
		--make-top-module "$(TOP_MODULE)" --tests-file $(REGRESS_TEST_FILE) \
		--tests "$(REGRESS_TESTS)" --seeds "$(REGRESS_SEEDS)" \
		--jobs $(REGRESS_JOBS) --pass-regex "$(REGRESS_PASS_REGEX)" \
		--matrix-args "$(REGRESS_MATRIX_ARGS)"
else
regress: comp
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/run_regression.py \
		--sim-dir $(SIM_DIR) --output-dir $(REGRESS_DIR) \
		--command "$(SIM_CMD)" --tests-file $(REGRESS_TEST_FILE) \
		--tests "$(REGRESS_TESTS)" --seeds "$(REGRESS_SEEDS)" \
		--jobs $(REGRESS_JOBS) --pass-regex "$(REGRESS_PASS_REGEX)" \
		--matrix-args "$(REGRESS_MATRIX_ARGS)"
endif

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


verdi: $(CANONICAL_FLIST)
	@command -v verdi >/dev/null 2>&1 || { echo "[VERDI] verdi not found"; exit 127; }
	@echo "[VERDI] Opening source database for $(TOP_MODULE) ..."
	$(VERDI_CMD)


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
$(SIM_FLIST): $(ACTIVE_FILELISTS) $(ACTIVE_DV_FILELISTS) $(FILELIST_MK_DEPS) $(TB_FILES) $(MODULE_PATH)/Makefile
	@mkdir -p $(SIM_DIR)
	@> $@
	@for fl in $(ACTIVE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
	@for fl in $(ACTIVE_DV_FILELISTS); do \
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

# --- Generate DUT-only RTL filelist for de/lint/syn/PD flows ---
$(RTL_RAW_FLIST): $(ACTIVE_FILELISTS) $(FILELIST_MK_DEPS) $(MODULE_PATH)/Makefile
	@mkdir -p $(RUN_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			sed 's|\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@sed 's|\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $@
endif
	@if [ ! -s $@ ]; then \
		echo "[FLIST] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
	@echo "[FLIST] Generated $@"

$(RTL_FLIST): $(RTL_RAW_FLIST) $(PROJECT_ROOT)/scripts/validate_filelist.py
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/validate_filelist.py $(RTL_RAW_FLIST) --output $@

# --- lint: static check on RTL only ---
lint: $(RTL_FLIST)
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
ifeq ($(LINT_TOOL),verilator)
	@verilator $(VERILATOR_LINT_FLAGS) --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog $(IVERILOG_FLAGS) -s $(RTL_TOP) -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),spyglass)
	@test -x "$(SG_SHELL)" || { echo "[LINT] SpyGlass sg_shell not found: $(SG_SHELL)"; exit 127; }
	@test -f "$(SG_LINT_TCL)" || { echo "[LINT] SpyGlass lint Tcl not found: $(SG_LINT_TCL)"; exit 2; }
	@mkdir -p "$(SG_LINT_RUN_DIR)"
	@cd "$(SG_LINT_RUN_DIR)" && \
	  PROJECT_ROOT="$(PROJECT_ROOT)" \
	  SPYGLASS_HOME="$(SG_HOME)" \
	  SG_FILELIST="$(RUN_DIR)/rtl.f" \
	  SG_TOP="$(RTL_TOP)" \
	  SG_GOAL="$(SG_LINT_GOAL)" \
	  SG_METHODOLOGY="$(SG_LINT_METHODOLOGY)" \
	  SG_PROJECT_NAME="$(RTL_TOP)_lint" \
	  SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(SG_SHELL)" -tcl "$(SG_LINT_TCL)" -licqueue -shell_log_file "$(SG_LINT_LOG)"
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
	@exit 2
endif
	@if [ "$(LINT_TOOL)" = "spyglass" ]; then \
		echo "[LINT] Log:     $(SG_LINT_LOG)"; \
		echo "[LINT] Report:  $(SG_LINT_REPORT)"; \
		echo "[LINT] Reports: $(SG_LINT_PROJECT_DIR)/consolidated_reports/lint_lint_rtl"; \
	else \
		echo "[LINT] Report: $(RUN_DIR)/lint.log"; \
	fi


# --- cdc: CDC check on RTL only ---
cdc: $(RTL_FLIST)
	@echo "[CDC] Tool: $(CDC_TOOL) | Top: $(RTL_TOP)"
ifeq ($(CDC_TOOL),spyglass)
	@test -x "$(SG_SHELL)" || { echo "[CDC] SpyGlass sg_shell not found: $(SG_SHELL)"; exit 127; }
	@test -f "$(SG_CDC_TCL)" || { echo "[CDC] SpyGlass CDC Tcl not found: $(SG_CDC_TCL)"; exit 2; }
	@mkdir -p "$(CDC_RUN_DIR)"
	@cd "$(CDC_RUN_DIR)" && \
	  PROJECT_ROOT="$(PROJECT_ROOT)" \
	  SPYGLASS_HOME="$(SG_HOME)" \
	  SG_FILELIST="$(RUN_DIR)/rtl.f" \
	  SG_TOP="$(RTL_TOP)" \
	  SG_GOAL="$(SG_CDC_GOAL)" \
	  SG_METHODOLOGY="$(SG_CDC_METHODOLOGY)" \
	  SG_PROJECT_NAME="$(RTL_TOP)_cdc" \
	  SG_SGDC="$(SG_CDC_SGDC)" \
	  SG_CLOCK_PORT="$(SG_CDC_CLOCK_PORT)" \
	  SG_RESET_PORT="$(SG_CDC_RESET_PORT)" \
	  SG_RESET_VALUE="$(SG_CDC_RESET_VALUE)" \
	  SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(SG_SHELL)" -tcl "$(SG_CDC_TCL)" -licqueue -shell_log_file "$(CDC_LOG)"
	@echo "[CDC] Log:      $(CDC_LOG)"
	@echo "[CDC] Reports:  $(SG_CDC_PROJECT_DIR)/consolidated_reports/cdc_cdc_verify_struct"
	@if [ "$(SG_CDC_GUI)" = "1" ]; then \
	  test -n "$(DISPLAY)" || { echo "[CDC] DISPLAY is empty; cannot open SpyGlass GUI"; exit 2; }; \
	  echo "[CDC] Opening SpyGlass GUI: $(SG_CDC_PROJECT_DIR)"; \
	  cd "$(CDC_RUN_DIR)" && \
	    setsid sh -c 'DISPLAY="$(DISPLAY)" XAUTHORITY="$(XAUTHORITY)" SPYGLASS_HOME="$(SG_HOME)" SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" LM_LICENSE_FILE="$(LM_LICENSE_FILE)" nohup "$(SG_HOME)/bin/spyglass" -project "$(notdir $(SG_CDC_PROJECT_DIR))" -disablesplashscreen > "$(SG_CDC_GUI_LOG)" 2>&1 &'; \
	fi
else
	@echo "[CDC] Unknown CDC_TOOL: $(CDC_TOOL)"
	@exit 2
endif

# --- syn: synthesis ---
syn: $(RTL_FLIST)
	@echo "[SYN] Tool: $(SYN_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(SYN_DIR)
	@cp $(RTL_FLIST) $(SYN_DIR)/rtl.f
	@if [ ! -s $(SYN_DIR)/rtl.f ]; then \
		echo "[SYN] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
ifeq ($(SYN_TOOL),yosys)
	@echo "# Auto-generated Yosys synthesis script for $(RTL_TOP)" > $(YOSYS_SYN_SCRIPT)
	@echo "read_verilog $$(grep -v '^#' $(SYN_DIR)/rtl.f | grep -v '^//' | grep -v '^$$' | tr '\n' ' ')" >> $(YOSYS_SYN_SCRIPT)
	@echo "hierarchy -check -top $(RTL_TOP)" >> $(YOSYS_SYN_SCRIPT)
	@echo "proc; flatten; opt; fsm; opt; memory; opt; techmap; opt" >> $(YOSYS_SYN_SCRIPT)
	@echo "write_verilog $(notdir $(SYN_NETLIST))" >> $(YOSYS_SYN_SCRIPT)
	@echo "stat" >> $(YOSYS_SYN_SCRIPT)
	@cd $(SYN_DIR) && $(YOSYS) $(notdir $(YOSYS_SYN_SCRIPT)) 2>&1 | tee $(notdir $(SYN_REPORT))
	@echo "[SYN] Netlist: $(SYN_NETLIST)"
	@echo "[SYN] Report:  $(SYN_REPORT)"
else ifeq ($(SYN_TOOL),dc)
	@command -v "$(DC_SHELL)" >/dev/null 2>&1 || test -x "$(DC_SHELL)" || { echo "[SYN] Design Compiler not found: $(DC_SHELL)"; exit 127; }
	@test -f "$(DC_SCRIPT)" || { echo "[SYN] DC script not found: $(DC_SCRIPT)"; exit 2; }
	@if [ -n "$(DC_SETUP_TCL)" ]; then test -f "$(DC_SETUP_TCL)" || { echo "[SYN] DC setup Tcl not found: $(DC_SETUP_TCL)"; exit 2; }; fi
	@if [ -n "$(DC_SDC)" ]; then test -f "$(DC_SDC)" || { echo "[SYN] DC SDC not found: $(DC_SDC)"; exit 2; }; else echo "[SYN] WARNING: No DC_SDC found; override DC_SDC=<path> for timing constraints"; fi
	@if [ -z "$(strip $(DC_TARGET_LIBRARY)$(DC_SETUP_TCL))" ]; then echo "[SYN] WARNING: No DC_TARGET_LIBRARY or DC_SETUP_TCL configured; technology mapping may fail"; fi
	@mkdir -p "$(DC_RUN_DIR)" "$(DC_WORK_DIR)" "$(DC_REPORT_DIR)" "$(DC_OUTPUT_DIR)"
	@cd "$(DC_RUN_DIR)" && \
	  PROJECT_ROOT="$(PROJECT_ROOT)" \
	  DC_TOP="$(RTL_TOP)" \
	  DC_FILELIST="$(SYN_DIR)/rtl.f" \
	  DC_SDC="$(DC_SDC)" \
	  DC_SETUP_TCL="$(DC_SETUP_TCL)" \
	  DC_WORK_DIR="$(DC_WORK_DIR)" \
	  DC_REPORT_DIR="$(DC_REPORT_DIR)" \
	  DC_OUTPUT_DIR="$(DC_OUTPUT_DIR)" \
	  DC_NETLIST="$(DC_NETLIST)" \
	  DC_DDC="$(DC_DDC)" \
	  DC_SDF="$(DC_SDF)" \
	  DC_SDC_OUT="$(DC_SDC_OUT)" \
	  DC_TARGET_LIBRARY="$(DC_TARGET_LIBRARY)" \
	  DC_LINK_LIBRARY="$(DC_LINK_LIBRARY)" \
	  DC_SYMBOL_LIBRARY="$(DC_SYMBOL_LIBRARY)" \
	  SKY130HD_DC_DB="$(SKY130HD_DC_DB)" \
	  SKY130HD_DC_LIB="$(SKY130HD_DC_LIB)" \
	  DC_SEARCH_PATH="$(DC_SEARCH_PATH)" \
	  DC_COMPILE_ULTRA="$(DC_COMPILE_ULTRA)" \
	  DC_CLOCK_GATING="$(DC_CLOCK_GATING)" \
	  DC_MAX_CORES="$(DC_MAX_CORES)" \
	  SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(DC_SHELL)" -f "$(DC_SCRIPT)" 2>&1 | tee "$(DC_LOG)"; \
	  status=$${PIPESTATUS[0]}; \
	  exit $$status
	@echo "[SYN] Netlist: $(DC_NETLIST)"
	@echo "[SYN] DDC:     $(DC_DDC)"
	@echo "[SYN] Reports: $(DC_REPORT_DIR)"
	@echo "[SYN] Log:     $(DC_LOG)"
else
	@echo "[SYN] Unknown SYN_TOOL: $(SYN_TOOL)"
	@exit 2
endif
