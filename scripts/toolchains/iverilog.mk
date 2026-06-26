COMP_CMD = $(IVERILOG) $(IVERILOG_FLAGS) -s $(TOP_MODULE) \
           -o $(BUILD_DIR)/sim.out $(FLIST_SRCS) \
           $(USER_COMPILE_FLAGS) 2>&1 | tee $(BUILD_DIR)/compile.log
SIM_CMD  = $(VVP) $(VVP_FLAGS) $(SIM_DIR)/sim.out $(USER_SIM_FLAGS)
BUILD_OUTPUT = $(BUILD_DIR)/sim.out
