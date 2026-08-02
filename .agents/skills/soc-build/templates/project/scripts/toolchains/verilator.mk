COMP_CMD = { \
           timing_flags=""; \
           if [ "$(VERILATOR_TIMING_MODE)" = "on" ]; then \
             timing_flags="--timing"; \
           elif [ "$(VERILATOR_TIMING_MODE)" = "auto" ] && [ "$(VERILATOR_REQUIRE_TIMING)" = "1" ]; then \
             if $(VERILATOR) --help 2>&1 | grep -q -- '--timing'; then \
               timing_flags="--timing"; \
             else \
               echo "[VERILATOR] ordinary SystemVerilog testbenches require a Verilator build with --timing; provide a *_verilator.cpp harness for this installed version"; \
               exit 2; \
             fi; \
           fi; \
           $(VERILATOR) $(VERILATOR_SIM_FLAGS) $$timing_flags --cc --exe \
             -CFLAGS "$(VERILATOR_CFLAGS)" -LDFLAGS "$(VERILATOR_LDFLAGS)" -Mdir $(BUILD_DIR)/obj_dir \
             --top-module $(TOP_MODULE) $(VERILATOR_RTL_SRCS) $(VERILATOR_SV_FILES) $(VERILATOR_HARNESS) $(USER_COMPILE_FLAGS) && \
           $(MAKE) -C $(BUILD_DIR)/obj_dir -f V$(TOP_MODULE).mk VERILATOR_ROOT="$(VERILATOR_ROOT)" V$(TOP_MODULE); \
         } 2>&1 | tee $(BUILD_DIR)/compile.log
SIM_CMD  = $(SIM_DIR)/obj_dir/V$(TOP_MODULE) \
           +max_cycles=$(VERILATOR_MAX_CYCLES) \
           $(if $(filter 1 true yes,$(VERILATOR_TRACE)),+trace +wavefile=$(SIM_DIR)/wave.$(if $(filter fst,$(VERILATOR_TRACE_FORMAT)),fst,vcd),) $(USER_SIM_FLAGS)
BUILD_OUTPUT = $(BUILD_DIR)/obj_dir/V$(TOP_MODULE)
