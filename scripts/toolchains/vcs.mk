# VCS/Verdi flow, adapted from xuanwu9000 defs.vcs.mk.
VCS_EXE     ?= vcs
VLOG_EXE    ?= vlogan
VERDI_EXE   ?= verdi

ifeq ($(strip $(VCS_HOME)),)
  VCS_HOME := $(patsubst %/bin/vlogan,%,$(realpath $(shell command -v $(VLOG_EXE) 2>/dev/null)))
endif
VCS_ARCH_OVERRIDE ?= linux
VCS_CC ?= gcc
VCS_DISABLE_POOL ?= 1
DISABLE_GC_POOL ?= 1
VCS_USE_MALLOC ?= 1
MALLOC_CHECK_ ?= 0
export VCS_HOME VCS_ARCH_OVERRIDE VCS_CC VCS_DISABLE_POOL DISABLE_GC_POOL VCS_USE_MALLOC MALLOC_CHECK_

VERDI_ROOT  := $(or $(VERDI_HOME),$(NOVAS_HOME))
VERDI_PLI_DIR ?= $(VERDI_ROOT)/share/PLI/VCS/LINUX64

VCS_FSDB_COMPILE_FLAGS :=
VCS_FSDB_ELAB_FLAGS :=
ifeq ($(FSDB),1)
  ifeq ($(wildcard $(VERDI_PLI_DIR)/novas.tab),)
    $(error FSDB=1 requires VERDI_HOME/NOVAS_HOME with VCS PLI under $(VERDI_PLI_DIR))
  endif
  VCS_FSDB_COMPILE_FLAGS += +define+FSDB_DUMP_ON
  VCS_FSDB_ELAB_FLAGS += -P $(VERDI_PLI_DIR)/novas.tab $(VERDI_PLI_DIR)/pli.a
endif

VCS_GUI_FLAGS :=
ifeq ($(GUI),1)
  VCS_GUI_FLAGS += -gui
endif

VCS_PARTCOMP_FLAGS :=
ifeq ($(PARTCOMP),1)
  VCS_PARTCOMP_FLAGS += -partcomp -partcomp_dir=.ptlib
endif

VCS_INCLUDE_FLAGS := +incdir+$(VCS_UVM_HOME) +incdir+$(RTL_PATH)
ifneq ($(wildcard $(RTL_PATH)/inc),)
  VCS_INCLUDE_FLAGS += +incdir+$(RTL_PATH)/inc
endif

VCS_DW_FLAGS :=
ifneq ($(strip $(VCS_DW_SIM_PATH)),)
  VCS_DW_FLAGS += -y $(VCS_DW_SIM_PATH) +incdir+$(VCS_DW_SIM_PATH)
endif

VCS_WORK_LIB := $(subst -,_,$(subst /,_,$(patsubst $(PROJECT_ROOT)/%,%,$(MODULE_PATH))))_worklib
VCS_WORK_DIR := $(SIM_DIR)/work/$(VCS_WORK_LIB)

VCS_COV_ELAB_FLAGS = $(if $(filter 1,$(COVERAGE)),-cm_name build -cm $(COV_METRICS) -cm_dir $(COV_DIR),)
VCS_COV_SIM_FLAGS = $(if $(filter 1,$(COVERAGE)),-cm $(COV_METRICS) -cm_dir $(COV_DIR) -cm_name $(TEST)_$(SEED),)
REGRESS_MATRIX_ARGS = $(if $(filter 1,$(COVERAGE)),-cm_name {test}_{seed},)

COMP_CMD = cd $(SIM_DIR) && \
           mkdir -p $(VCS_WORK_DIR) && \
           printf 'WORK > $(VCS_WORK_LIB)\n$(VCS_WORK_LIB) : ./work/$(VCS_WORK_LIB)\n' > synopsys_sim.setup && \
           $(VLOG_EXE) $(VCS_DW_FLAGS) $(VLOG_FLAGS) \
           +define+HW=$(VCS_HW_ROOT) $(VCS_FSDB_COMPILE_FLAGS) \
           $(VCS_INCLUDE_FLAGS) -timescale=$(TIMESCALE) \
           -f $(FILELIST) $(USER_COMPILE_FLAGS) -l compile.log
ELAB_CMD = cd $(SIM_DIR) && \
           $(VCS_EXE) $(TOP_MODULE) $(VCS_ELAB_FLAGS) \
           $(VCS_PARTCOMP_FLAGS) $(VCS_FSDB_ELAB_FLAGS) \
           $(VCS_COV_ELAB_FLAGS) -timescale=$(TIMESCALE) -o simv -l elab.log
SIM_CMD  = ./simv $(VCS_SIM_FLAGS) $(VCS_COV_SIM_FLAGS) $(VCS_GUI_FLAGS) $(USER_SIM_FLAGS)
BUILD_OUTPUT = $(SIM_DIR)/simv
COVERAGE_SUPPORTED = 1
COVERAGE_REPORT_CMD = env LD_LIBRARY_PATH=$(VCS_HOME)/amd64/lib \
                      VCS_DISABLE_POOL=1 DISABLE_GC_POOL=1 VCS_USE_MALLOC=1 MALLOC_CHECK_=0 \
                      $(VCS_HOME)/bin/urg -full64 -dir $(COV_DIR) -report $(COV_REPORT_DIR)

# Source view and compiled KDB view correspond to xuanwu9000's verdi/vcs_verdi.
VERDI_CMD     = $(VERDI_EXE) $(VERDI_FLAGS) -top $(TOP_MODULE) -f $(FILELIST) &
DEBUG_GUI_CMD = $(VERDI_EXE) -dbdir $(SIM_DIR)/simv.daidir &

ifeq ($(FSDB),1)
  WAVE_CMD = $(VERDI_EXE) -ssf $(SIM_DIR)/wave.fsdb &
else
  WAVE_CMD = dve -vpd $(SIM_DIR)/wave.vpd &
endif
