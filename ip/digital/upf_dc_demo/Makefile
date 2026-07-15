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
DC_TARGET_LIBRARY := $(SKY130HD_DC_DB) $(TEACHING_LH_DB) $(TEACHING_HL_DB)
DC_LINK_LIBRARY := * $(DC_TARGET_LIBRARY) $(MACRO_PG_DB)

$(MACRO_PG_DB): $(MACRO_PG_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$(MACRO_PG_LIB)" --db "$(MACRO_PG_DB)" \
	  --work-dir "$(CURDIR)/de/syn/macro_pg_lc_work"
	@test -s "$(MACRO_PG_DB)" || { echo "[LIBDB] missing output: $(MACRO_PG_DB)"; exit 2; }

$(TEACHING_LH_LIB): $(TEACHING_MV_SCRIPT)
	@test -s "$(SKY130HD_DC_LIB)" || { echo "[LIBDB] set SKY130HD_DC_LIB to the matching Sky130 HD Liberty source"; exit 2; }
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp python3.12 \
	  "$(TEACHING_MV_SCRIPT)" --source "$(SKY130HD_DC_LIB)" \
	  --output "$@" --variant lh

$(TEACHING_HL_LIB): $(TEACHING_MV_SCRIPT)
	@test -s "$(SKY130HD_DC_LIB)" || { echo "[LIBDB] set SKY130HD_DC_LIB to the matching Sky130 HD Liberty source"; exit 2; }
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp python3.12 \
	  "$(TEACHING_MV_SCRIPT)" --source "$(SKY130HD_DC_LIB)" \
	  --output "$@" --variant hl

$(TEACHING_LH_DB): $(TEACHING_LH_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$<" --db "$@" --work-dir "$(CURDIR)/de/syn/teaching_lh_lc_work"
	@test -s "$@" || { echo "[LIBDB] missing output: $@"; exit 2; }

$(TEACHING_HL_DB): $(TEACHING_HL_LIB)
	@env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp python3.12 \
	  $(PROJECT_ROOT)/.agents/skills/lib-db-gen/scripts/lib_db_gen.py convert \
	  --lib "$<" --db "$@" --work-dir "$(CURDIR)/de/syn/teaching_hl_lc_work"
	@test -s "$@" || { echo "[LIBDB] missing output: $@"; exit 2; }

syn: $(MACRO_PG_DB) $(TEACHING_LH_DB) $(TEACHING_HL_DB)

# This module exercises Power Compiler power intent and therefore must not use
# the repository's generic non-UPF DC driver.
# Publish the canonical stage artifacts directly under de/syn while retaining
# transient work and detailed reports under de/syn/dc.
DC_NETLIST := $(SYN_DIR)/$(RTL_TOP)_netlist.v
DC_DDC     := $(SYN_DIR)/$(RTL_TOP).ddc
DC_SDF     := $(SYN_DIR)/$(RTL_TOP).sdf
DC_SDC_OUT := $(SYN_DIR)/$(RTL_TOP)_synth.sdc
DC_LOG     := $(SYN_DIR)/synth.log
