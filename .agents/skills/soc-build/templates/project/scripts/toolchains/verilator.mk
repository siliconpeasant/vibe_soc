COMP_CMD = verilator $(VERILATOR_FLAGS) --cc --exe --build --trace \
           -CFLAGS "-std=c++17" -Mdir $(SIM_DIR)/obj_dir \
           --top-module $(TOP_MODULE) $(FLIST_SRCS) $(TB_FILES) \
           $(USER_COMPILE_FLAGS) 2>&1 | tee $(SIM_DIR)/compile.log
SIM_CMD  = $(SIM_DIR)/obj_dir/V$(TOP_MODULE) \
           +trace +wavefile=$(SIM_DIR)/wave.vcd $(USER_SIM_FLAGS)
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
BUILD_OUTPUT = $(SIM_DIR)/obj_dir/V$(TOP_MODULE)
