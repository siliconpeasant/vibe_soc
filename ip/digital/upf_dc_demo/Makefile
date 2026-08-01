# upf_dc_demo module
PROJECT_ROOT ?= $(shell cd ../../.. && pwd -P)
MODULE_NAME   = upf_dc_demo
DC_SCRIPT    := $(PROJECT_ROOT)/scripts/syn/dc_upf_synth.tcl
DC_SETUP_TCL := $(PROJECT_ROOT)/scripts/syn/sky130hd_dc_setup.tcl
DC_UPF       := $(CURDIR)/de/syn/upf/upf_dc_demo.upf
DC_SAVED_UPF := $(CURDIR)/de/syn/upf/upf_dc_demo_synth.upf
DC_UPF_CHECKS_TCL := $(CURDIR)/de/syn/upf_checks.tcl
DC_COMPILE_OPTIONS := -no_autoungroup
DC_NETLIST   := $(CURDIR)/de/syn/upf_dc_demo_netlist.v
DC_DDC       := $(CURDIR)/de/syn/upf_dc_demo.ddc
DC_SDF       := $(CURDIR)/de/syn/upf_dc_demo.sdf
DC_SDC_OUT   := $(CURDIR)/de/syn/upf_dc_demo_synth.sdc
DC_SVF       := $(CURDIR)/de/syn/upf_dc_demo.svf
DC_TIMING_REPORT  := $(CURDIR)/de/syn/timing.rpt
DC_TIMING_SUMMARY := $(CURDIR)/de/syn/timing_summary.rpt
MACRO_PG_LIB := $(CURDIR)/de/syn/macro_pg_stub.lib
MACRO_PG_DB  := $(CURDIR)/de/syn/macro_pg_stub.db
TEACHING_MV_SCRIPT := $(CURDIR)/de/syn/build_teaching_mv_lib.py
TEACHING_LH_LIB := $(CURDIR)/de/syn/sky130hd_teaching_lh_1v2_1v8.lib
TEACHING_LH_DB  := $(CURDIR)/de/syn/sky130hd_teaching_lh_1v2_1v8.db
TEACHING_HL_LIB := $(CURDIR)/de/syn/sky130hd_teaching_hl_1v8_1v2.lib
TEACHING_HL_DB  := $(CURDIR)/de/syn/sky130hd_teaching_hl_1v8_1v2.db
FORMAL_NETLIST := $(DC_NETLIST)
FORMAL_REFERENCE_UPF := $(DC_UPF)
FORMAL_IMPLEMENTATION_UPF := $(DC_SAVED_UPF)
FORMAL_SVF := $(DC_SVF)
FORMAL_LIB_DB = $(DC_TARGET_LIBRARY) $(MACRO_PG_DB)
CLP_REFERENCE_UPF := $(DC_UPF)
CLP_LIB_FILES := $(TEACHING_LH_LIB) $(TEACHING_HL_LIB) $(MACRO_PG_LIB)
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
DC_LOG     := $(SYN_DIR)/synth.log
