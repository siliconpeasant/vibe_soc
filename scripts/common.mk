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
else ifeq ($(LINT_TOOL),vc_static)
	@test -x "$(VC_STATIC_SHELL)" || { echo "[LINT] VC Static shell not found: $(VC_STATIC_SHELL)"; exit 127; }
	@test -f "$(VC_LINT_SCRIPT)" || { echo "[LINT] VC lint script not found: $(VC_LINT_SCRIPT)"; exit 2; }
	@mkdir -p "$(LINT_RUN_DIR)"
	@cd "$(LINT_RUN_DIR)" && \
	  DISPLAY="$(DISPLAY)" \
	  XAUTHORITY="$(XAUTHORITY)" \
	  VC_STATIC_HOME="$(VC_STATIC_HOME)" \
	  VC_LINT_FILELIST="$(RUN_DIR)/rtl.f" \
	  VC_LINT_TOP="$(RTL_TOP)" \
	  VC_LINT_REPORT="$(VC_LINT_REPORT)" \
	  VC_LINT_MODULE_DIR="$(MODULE_PATH)" \
	  VC_LINT_SETUP="$(MODULE_PATH)/de/lint/vc_lint_setup.tcl" \
	  VC_LINT_RULES="$(VC_LINT_RULES)" \
	  VC_LINT_SEARCH_PATH="$(RTL_PATH) $(MODULE_PATH)" \
	  VC_LINT_GUI="$(VC_LINT_GUI)" \
	  VC_LINT_ENABLE_TAGS="$(VC_LINT_ENABLE_TAGS)" \
	  "$(VC_STATIC_SHELL)" $(VC_STATIC_FLAGS) -out_dir "$(VC_STATIC_OUT_DIR)" \
	    -f "$(VC_LINT_SCRIPT)" -output_log_file "../$(notdir $(VC_STATIC_LOG))" 2>&1 | tee "$(LINT_LOG)"; \
	  status=$${PIPESTATUS[0]}; \
	  if [ $$status -eq 11 ]; then echo "[LINT] VC Static completed with warnings"; status=0; fi; \
	  if [ $$status -ne 0 ]; then exit $$status; fi; \
	  if [ "$(VC_LINT_GUI)" = "1" ]; then \
	    if [ -f "$(VC_STATIC_OUT_DIR)/novas.rc" ]; then \
	      sed -i 's/^thirdpartyIdx[[:space:]]*=.*/thirdpartyIdx = 0/' "$(VC_STATIC_OUT_DIR)/novas.rc"; \
	    fi; \
	    echo "[LINT] Opening VC Static GUI: $(VC_STATIC_OUT_DIR)"; \
	    DISPLAY="$(DISPLAY)" XAUTHORITY="$(XAUTHORITY)" HOME="$(LINT_RUN_DIR)" VC_STATIC_HOME="$(VC_STATIC_HOME)" \
	      nohup "$(VC_STATIC_SHELL)" $(VC_STATIC_FLAGS) -gui -restore \
	        -out_dir "$(VC_STATIC_OUT_DIR)" -output_log_file "../vc_static_gui.log" \
	        >/dev/null 2>&1 & \
	  fi
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
	@exit 2
endif
	@if [ "$(LINT_TOOL)" = "vc_static" ]; then \
		echo "[LINT] Report: $(LINT_LOG)"; \
		echo "[LINT] VC report: $(VC_LINT_REPORT)"; \
	else \
		echo "[LINT] Report: $(RUN_DIR)/lint.log"; \
	fi


# --- cdc: CDC check on RTL only ---
cdc: $(RTL_FLIST)
	@echo "[CDC] Tool: $(CDC_TOOL) | Top: $(RTL_TOP)"
ifeq ($(CDC_TOOL),spyglass)
	@test -x "$(SG_SHELL)" || { echo "[CDC] SpyGlass sg_shell not found: $(SG_SHELL)"; exit 127; }
	@test -f "$(SG_CDC_GEN)" || { echo "[CDC] SpyGlass CDC generator not found: $(SG_CDC_GEN)"; exit 2; }
	@mkdir -p "$(CDC_RUN_DIR)"
	@$(PYTHON_RUN) "$(SG_CDC_GEN)" \
	  --project-root "$(PROJECT_ROOT)" \
	  --run-dir "$(CDC_RUN_DIR)" \
	  --filelist "$(RUN_DIR)/rtl.f" \
	  --top "$(RTL_TOP)" \
	  --spyglass-home "$(SG_HOME)" \
	  --goal "$(SG_CDC_GOAL)" \
	  --methodology "$(SG_CDC_METHODOLOGY)" \
	  --clock-port "$(SG_CDC_CLOCK_PORT)" \
	  --reset-port "$(SG_CDC_RESET_PORT)" \
	  --reset-value "$(SG_CDC_RESET_VALUE)" \
	  $(if $(SG_CDC_SGDC),--sgdc "$(SG_CDC_SGDC)")
	@cd "$(CDC_RUN_DIR)" && \
	  SPYGLASS_HOME="$(SG_HOME)" \
	  SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(SG_SHELL)" -tcl run_sg_cdc.tcl -licqueue -shell_log_file "$(CDC_LOG)"
	@echo "[CDC] Log:      $(CDC_LOG)"
	@echo "[CDC] Reports:  $(SG_CDC_PROJECT_DIR)/consolidated_reports/cdc_cdc_verify_struct"
	@if [ "$(SG_CDC_GUI)" = "1" ]; then \
	  test -n "$(DISPLAY)" || { echo "[CDC] DISPLAY is empty; cannot open SpyGlass GUI"; exit 2; }; \
	  echo "[CDC] Opening SpyGlass GUI: $(SG_CDC_PROJECT_DIR)"; \
	  cd "$(CDC_RUN_DIR)" && \
	    setsid sh -c 'DISPLAY="$(DISPLAY)" XAUTHORITY="$(XAUTHORITY)" SPYGLASS_HOME="$(SG_HOME)" SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" LM_LICENSE_FILE="$(LM_LICENSE_FILE)" nohup "$(SG_HOME)/bin/spyglass" -project "$(notdir $(SG_CDC_PROJECT_DIR))" -disablesplashscreen > "$(SG_CDC_GUI_LOG)" 2>&1 &'; \
	fi
else ifeq ($(CDC_TOOL),vc_static)
	@test -x "$(VC_STATIC_SHELL)" || { echo "[CDC] VC Static shell not found: $(VC_STATIC_SHELL)"; exit 127; }
	@test -f "$(VC_CDC_SCRIPT)" || { echo "[CDC] VC CDC script not found: $(VC_CDC_SCRIPT)"; exit 2; }
	@if [ -n "$(CDC_SDC)" ]; then \
		test -f "$(CDC_SDC)" || { echo "[CDC] SDC not found: $(CDC_SDC)"; exit 2; }; \
		echo "[CDC] SDC: $(CDC_SDC)"; \
	else \
		echo "[CDC] WARNING: No CDC_SDC found; override with CDC_SDC=<path> for clock constraints"; \
	fi
	@mkdir -p "$(CDC_RUN_DIR)"
	@cd "$(CDC_RUN_DIR)" && \
	  DISPLAY="$(DISPLAY)" \
	  XAUTHORITY="$(XAUTHORITY)" \
	  VC_STATIC_HOME="$(VC_STATIC_HOME)" \
	  VC_CDC_FILELIST="$(RUN_DIR)/rtl.f" \
	  VC_CDC_TOP="$(RTL_TOP)" \
	  VC_CDC_SDC="$(CDC_SDC)" \
	  VC_CDC_REPORT="$(VC_CDC_REPORT)" \
	  VC_CDC_SUMMARY="$(VC_CDC_SUMMARY)" \
	  VC_CDC_SETUP="$(MODULE_PATH)/de/cdc/vc_cdc_setup.tcl" \
	  VC_CDC_SEARCH_PATH="$(RTL_PATH) $(MODULE_PATH)" \
	  VC_CDC_CHECK_ARGS="$(VC_CDC_CHECK_ARGS)" \
	  "$(VC_STATIC_SHELL)" $(VC_STATIC_FLAGS) -out_dir "$(VC_CDC_OUT_DIR)" \
	    -f "$(VC_CDC_SCRIPT)" -output_log_file "../$(notdir $(VC_CDC_LOG))" 2>&1 | tee "$(CDC_LOG)"; \
	  status=$${PIPESTATUS[0]}; \
	  if [ $$status -eq 11 ]; then echo "[CDC] VC Static completed with warnings"; status=0; fi; \
	  if [ $$status -ne 0 ]; then exit $$status; fi
	@echo "[CDC] Log:      $(CDC_LOG)"
	@echo "[CDC] Summary:  $(VC_CDC_SUMMARY)"
	@echo "[CDC] Detailed: $(VC_CDC_REPORT)"
else
	@echo "[CDC] Unknown CDC_TOOL: $(CDC_TOOL)"
	@exit 2
endif

# --- syn: Yosys synthesis ---
syn: $(RTL_FLIST)
	@echo "[SYN] Yosys | Top: $(RTL_TOP)"
	@mkdir -p $(SYN_DIR)
	@cp $(RTL_FLIST) $(SYN_DIR)/rtl.f
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
