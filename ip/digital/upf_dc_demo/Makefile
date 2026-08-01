# upf_dc_demo module
PROJECT_ROOT ?= $(shell cd ../../.. && pwd -P)
MODULE_NAME   = upf_dc_demo
DC_SCRIPT    := $(CURDIR)/de/syn/dc_upf_synth.tcl
DC_SETUP_TCL := $(PROJECT_ROOT)/scripts/syn/sky130hd_dc_setup.tcl
MACRO_PG_LIB := $(CURDIR)/de/syn/macro_pg_stub.lib
MACRO_PG_DB  := $(CURDIR)/de/syn/macro_pg_stub.db
TEACHING_MV_SCRIPT := $(CURDIR)/de/syn/build_teaching_mv_lib.py
TEACHING_LH_LIB := $(CURDIR)/de/syn/sky130hd_teaching_lh_1v2_1v8.lib
TEACHING_LH_DB  := $(CURDIR)/de/syn/sky130hd_teaching_lh_1v2_1v8.db
TEACHING_HL_LIB := $(CURDIR)/de/syn/sky130hd_teaching_hl_1v8_1v2.lib
TEACHING_HL_DB  := $(CURDIR)/de/syn/sky130hd_teaching_hl_1v8_1v2.db
include $(PROJECT_ROOT)/scripts/common.mk

# The PLL, SRAM, and IO behavioral macro models are used by lint/compile only.
# DC links the same four cell names from this PG-aware teaching stub so their
# supplies exist only as Liberty pg_pin objects connected by canonical UPF.
# PSW_SW/ACC/PERI/MEDIA remain virtual UPF rules; backend owns switch cells.
# The local Sky130 file is characterized only at 1.8 V.  Two generated,
# explicitly non-signoff variants provide the library voltage maps needed to
# exercise 1.2 V standard cells and both LS directions in Power Compiler.
ifeq ($(strip $(SKY130HD_DC_DB)),)
SKY130HD_DC_DB := $(CURDIR)/de/syn/sky130_fd_sc_hd__tt_025C_1v80.db
endif
DC_TARGET_LIBRARY := $(SKY130HD_DC_DB) $(TEACHING_LH_DB) $(TEACHING_HL_DB)
DC_LINK_LIBRARY := * $(DC_TARGET_LIBRARY) $(MACRO_PG_DB)

$(SKY130HD_DC_DB): $(SKY130HD_DC_LIB)
	@test -s "$(SKY130HD_DC_LIB)" || { echo "[LIBDB] set SKY130HD_DC_LIB to the matching Sky130 HD Liberty source"; exit 2; }
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$(SKY130HD_DC_LIB)" --db "$(SKY130HD_DC_DB)" \
	  --work-dir "$(CURDIR)/de/syn/sky130hd_lc_work"
	@test -s "$(SKY130HD_DC_DB)" || { echo "[LIBDB] missing output: $(SKY130HD_DC_DB)"; exit 2; }

$(MACRO_PG_DB): $(MACRO_PG_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$(MACRO_PG_LIB)" --db "$(MACRO_PG_DB)" \
	  --work-dir "$(CURDIR)/de/syn/macro_pg_lc_work"
	@test -s "$(MACRO_PG_DB)" || { echo "[LIBDB] missing output: $(MACRO_PG_DB)"; exit 2; }

$(TEACHING_LH_LIB): $(TEACHING_MV_SCRIPT)
	@test -s "$(SKY130HD_DC_LIB)" || { echo "[LIBDB] set SKY130HD_DC_LIB to the matching Sky130 HD Liberty source"; exit 2; }
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  "$(TEACHING_MV_SCRIPT)" --source "$(SKY130HD_DC_LIB)" \
	  --output "$@" --variant lh

$(TEACHING_HL_LIB): $(TEACHING_MV_SCRIPT)
	@test -s "$(SKY130HD_DC_LIB)" || { echo "[LIBDB] set SKY130HD_DC_LIB to the matching Sky130 HD Liberty source"; exit 2; }
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  "$(TEACHING_MV_SCRIPT)" --source "$(SKY130HD_DC_LIB)" \
	  --output "$@" --variant hl

$(TEACHING_LH_DB): $(TEACHING_LH_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$<" --db "$@" --work-dir "$(CURDIR)/de/syn/teaching_lh_lc_work"
	@test -s "$@" || { echo "[LIBDB] missing output: $@"; exit 2; }

$(TEACHING_HL_DB): $(TEACHING_HL_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(PROJECT_ROOT)/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$<" --db "$@" --work-dir "$(CURDIR)/de/syn/teaching_hl_lc_work"
	@test -s "$@" || { echo "[LIBDB] missing output: $@"; exit 2; }

syn: $(SKY130HD_DC_DB) $(MACRO_PG_DB) $(TEACHING_LH_DB) $(TEACHING_HL_DB)

# This module exercises Power Compiler power intent and therefore must not use
# the repository's generic non-UPF DC driver.
# Publish the canonical stage artifacts directly under de/syn while retaining
# transient work and detailed reports under de/syn/dc.
DC_NETLIST := $(SYN_DIR)/$(RTL_TOP)_netlist.v
DC_DDC     := $(SYN_DIR)/$(RTL_TOP).ddc
DC_SDF     := $(SYN_DIR)/$(RTL_TOP).sdf
DC_SDC_OUT := $(SYN_DIR)/$(RTL_TOP)_synth.sdc
DC_LOG     := $(SYN_DIR)/synth.log
DC_SVF     := $(SYN_DIR)/$(RTL_TOP).svf
DC_SYNTH_UPF := $(SYN_DIR)/upf/$(RTL_TOP)_synth.upf
FORMAL_NETLIST ?= $(DC_NETLIST)
FORMAL_REFERENCE_UPF ?= $(SYN_DIR)/upf/$(RTL_TOP).upf
FORMAL_IMPLEMENTATION_UPF ?= $(DC_SYNTH_UPF)
FORMAL_SVF ?= $(DC_SVF)
CLP_REFERENCE_UPF ?= $(SYN_DIR)/upf/$(RTL_TOP).upf

FORMAL_SCRIPT_DIR := $(CURDIR)/de/syn/formal
FORMALITY_SCRIPT := $(FORMAL_SCRIPT_DIR)/formality_upf_verify.tcl
CLP_SCRIPT := $(FORMAL_SCRIPT_DIR)/clp_rtl_upf_check.tcl
FORMALITY_RUN_DIR := $(CURDIR)/de/run/formality
CLP_RUN_DIR := $(CURDIR)/de/run/clp
FM_SHELL ?= fm_shell
CLP_SHELL ?= lec

.PHONY: formal-upf clp-upf

formal-upf: $(FORMALITY_SCRIPT)
	@test "$(SILICON_CREW_UPF_GEN_MCP_ACTIVE)" = "1" || { echo "[FORMAL] run through registered upf-gen MCP"; exit 2; }
	@command -v "$(FM_SHELL)" >/dev/null 2>&1 || test -x "$(FM_SHELL)" || { echo "[FORMAL] fm_shell not found: $(FM_SHELL)"; exit 127; }
	@for input in "$(SYN_DIR)/rtl.f" "$(FORMAL_NETLIST)" "$(FORMAL_REFERENCE_UPF)" "$(FORMAL_IMPLEMENTATION_UPF)" "$(FORMAL_SVF)" $(DC_TARGET_LIBRARY) "$(MACRO_PG_DB)"; do \
	  test -s "$$input" || { echo "[FORMAL] missing input: $$input"; exit 2; }; \
	done
	@mkdir -p "$(FORMALITY_RUN_DIR)"
	@rm -f "$(FORMALITY_RUN_DIR)/formality.log" \
	  "$(FORMALITY_RUN_DIR)/setup_status.rpt" \
	  "$(FORMALITY_RUN_DIR)/upf_reference.rpt" \
	  "$(FORMALITY_RUN_DIR)/upf_implementation.rpt" \
	  "$(FORMALITY_RUN_DIR)/library_defects.rpt" \
	  "$(FORMALITY_RUN_DIR)/match_status.rpt" \
	  "$(FORMALITY_RUN_DIR)/verification_status.rpt"
	@cd "$(FORMALITY_RUN_DIR)" && \
	  PROJECT_ROOT="$(PROJECT_ROOT)" \
	  FM_TOP="$(RTL_TOP)" \
	  FM_RTL_FILELIST="$(SYN_DIR)/rtl.f" \
	  FM_NETLIST="$(FORMAL_NETLIST)" \
	  FM_REFERENCE_UPF="$(FORMAL_REFERENCE_UPF)" \
	  FM_IMPLEMENTATION_UPF="$(FORMAL_IMPLEMENTATION_UPF)" \
	  FM_SVF="$(FORMAL_SVF)" \
	  FM_LIB_DB="$(DC_TARGET_LIBRARY) $(MACRO_PG_DB)" \
	  FM_RUN_DIR="$(FORMALITY_RUN_DIR)" \
	  SNPSLMD_LICENSE_FILE="$(SNPSLMD_LICENSE_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(FM_SHELL)" -f "$(FORMALITY_SCRIPT)" 2>&1 | tee "$(FORMALITY_RUN_DIR)/formality.log"; \
	  status=$${PIPESTATUS[0]}; \
	  exit $$status

clp-upf: $(CLP_SCRIPT)
	@test "$(SILICON_CREW_UPF_GEN_MCP_ACTIVE)" = "1" || { echo "[CLP] run through registered upf-gen MCP"; exit 2; }
	@command -v "$(CLP_SHELL)" >/dev/null 2>&1 || test -x "$(CLP_SHELL)" || { echo "[CLP] lec not found: $(CLP_SHELL)"; exit 127; }
	@for input in "$(SYN_DIR)/rtl.f" "$(CLP_REFERENCE_UPF)" "$(TEACHING_LH_LIB)" "$(TEACHING_HL_LIB)" "$(MACRO_PG_LIB)"; do \
	  test -s "$$input" || { echo "[CLP] missing input: $$input"; exit 2; }; \
	done
	@mkdir -p "$(CLP_RUN_DIR)"
	@rm -f "$(CLP_RUN_DIR)/clp.log" \
	  "$(CLP_RUN_DIR)/rules_1801_summary.rpt" \
	  "$(CLP_RUN_DIR)/rules_1801_errors.rpt" \
	  "$(CLP_RUN_DIR)/rules_1801_errors.xml" \
	  "$(CLP_RUN_DIR)/power_intent.rpt" \
	  "$(CLP_RUN_DIR)/lowpower.rpt" \
	  "$(CLP_RUN_DIR)/design_data.rpt" \
	  "$(CLP_RUN_DIR)/black_boxes.rpt"
	@cd "$(CLP_RUN_DIR)" && \
	  PROJECT_ROOT="$(PROJECT_ROOT)" \
	  CLP_TOP="$(RTL_TOP)" \
	  CLP_RTL_FILELIST="$(SYN_DIR)/rtl.f" \
	  CLP_UPF="$(CLP_REFERENCE_UPF)" \
	  CLP_LIB_FILES="$(TEACHING_LH_LIB) $(TEACHING_HL_LIB) $(MACRO_PG_LIB)" \
	  CLP_RUN_DIR="$(CLP_RUN_DIR)" \
	  CDS_LIC_FILE="$(CDS_LIC_FILE)" \
	  LM_LICENSE_FILE="$(LM_LICENSE_FILE)" \
	  "$(CLP_SHELL)" -lp -nogui -dofile "$(CLP_SCRIPT)" 2>&1 | tee "$(CLP_RUN_DIR)/clp.log"; \
	  status=$${PIPESTATUS[0]}; \
	  exit $$status
