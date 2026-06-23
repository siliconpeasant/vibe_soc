COMP_CMD = $(IVERILOG) $(IVERILOG_FLAGS) -s $(TOP_MODULE) \
           -o $(SIM_DIR)/sim.out $(FLIST_SRCS) \
           $(USER_COMPILE_FLAGS) 2>&1 | tee $(SIM_DIR)/compile.log
SIM_CMD  = $(VVP) $(VVP_FLAGS) $(SIM_DIR)/sim.out $(USER_SIM_FLAGS)
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
BUILD_OUTPUT = $(SIM_DIR)/sim.out
