COMP_CMD = { \
           $(VERILATOR) $(VERILATOR_SIM_FLAGS) --cc --exe \
             -CFLAGS "$(VERILATOR_CFLAGS)" -LDFLAGS "$(VERILATOR_LDFLAGS)" -Mdir $(SIM_DIR)/obj_dir \
             --top-module $(TOP_MODULE) $(VERILATOR_RTL_SRCS) $(VERILATOR_SV_FILES) $(VERILATOR_HARNESS) $(USER_COMPILE_FLAGS) && \
           $(MAKE) -C $(SIM_DIR)/obj_dir -f V$(TOP_MODULE).mk VERILATOR_ROOT="$(VERILATOR_ROOT)" V$(TOP_MODULE); \
         } 2>&1 | tee $(SIM_DIR)/compile.log
SIM_CMD  = $(SIM_DIR)/obj_dir/V$(TOP_MODULE) \
           $(if $(filter 1 true yes,$(VERILATOR_TRACE)),+trace +wavefile=$(SIM_DIR)/wave.$(if $(filter fst,$(VERILATOR_TRACE_FORMAT)),fst,vcd),) $(USER_SIM_FLAGS)
BUILD_OUTPUT = $(SIM_DIR)/obj_dir/V$(TOP_MODULE)
