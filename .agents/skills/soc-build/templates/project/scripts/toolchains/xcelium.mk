# Xcelium multi-step flow, adapted from xuanwu9000 defs.xcelium.mk.
XRUN_EXE    ?= xrun
SIMVISION_EXE ?= simvision
VERDI_EXE   ?= verdi
XCELIUM_WORK := $(SIM_DIR)/xcelium.d

XCELIUM_GUI_FLAGS :=
ifeq ($(GUI),1)
  XCELIUM_GUI_FLAGS += -gui
endif

COMP_CMD = $(XRUN_EXE) $(XCELIUM_FLAGS) -compile \
           -timescale $(TIMESCALE) -f $(FILELIST) \
           -xmlibdirname $(XCELIUM_WORK) $(USER_COMPILE_FLAGS) \
           -l $(SIM_DIR)/compile.log
ELAB_CMD = $(XRUN_EXE) $(XCELIUM_FLAGS) -elaborate \
           -top $(TOP_MODULE) -xmlibdirname $(XCELIUM_WORK) \
           -l $(SIM_DIR)/elab.log
SIM_CMD  = $(XRUN_EXE) -R -xmlibdirname $(XCELIUM_WORK) \
           $(XCELIUM_SIM_FLAGS) $(XCELIUM_GUI_FLAGS) $(USER_SIM_FLAGS)
WAVE_CMD = $(SIMVISION_EXE) $(SIM_DIR)/waves.shm &

VERDI_CMD     = $(VERDI_EXE) $(VERDI_FLAGS) -top $(TOP_MODULE) -f $(FILELIST) &
DEBUG_GUI_CMD = $(SIMVISION_EXE) $(SIM_DIR)/waves.shm &
BUILD_OUTPUT = $(XCELIUM_WORK)
