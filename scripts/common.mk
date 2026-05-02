# =============================================================================
# Common Makefile for SoC Project Simulation
# =============================================================================
# 使用方式：在子 Makefile 中定义以下变量，然后 include 本文件
#
#   PROJECT_ROOT  = $(shell cd <relative_to_root> && pwd)
#   RTL_FILES     = $(shell find <rtl_dir> -name "*.v" -o -name "*.sv")
#   TB_FILES      = $(shell find <tb_dir> -name "*.v" -o -name "*.sv")
#   TOP_MODULE    ?= tb_top
#   RUN_DIR       ?= $(PWD)/run
#   SIM_DIR       ?= $(RUN_DIR)              (仿真输出目录，默认与 RUN_DIR 相同)
#   FILELIST      ?= $(RUN_DIR)/filelist.f   (可选)
#
#   include $(PROJECT_ROOT)/scripts/common.mk
# =============================================================================

ifndef PROJECT_ROOT
  $(error PROJECT_ROOT must be defined before including common.mk)
endif

ifndef TOP_MODULE
  $(error TOP_MODULE must be defined before including common.mk)
endif

SIMULATOR    ?= iverilog
RUN_DIR      ?= $(PWD)/run
SIM_DIR      ?= $(RUN_DIR)

# 统一项目根目录变量（支持环境变量或 Makefile 计算）
SOC          ?= $(PROJECT_ROOT)

# 如果定义了 FILELIST，提取文件路径（过滤注释/空行）并替换 $$SOC 变量
ifdef FILELIST
  FLIST_SRCS = $(shell sed '/^\#/d;/^\/\//d;/^$$/d' $(FILELIST) 2>/dev/null | sed 's|\$$SOC|$(SOC)|g')
endif

# --------------- VCS ---------------
ifeq ($(SIMULATOR),vcs)
ifdef FILELIST
COMP_CMD = vcs -sverilog -full64 -timescale=1ns/1ps \
           +v2k -debug_access+all -kdb \
           -f $(FILELIST) \
           -o $(SIM_DIR)/simv
else
COMP_CMD = vcs -sverilog -full64 -timescale=1ns/1ps \
           +v2k -debug_access+all -kdb \
           $(RTL_FILES) $(TB_FILES) \
           -o $(SIM_DIR)/simv
endif
SIM_CMD  = $(SIM_DIR)/simv +vpdfile+$(SIM_DIR)/wave.vpd
WAVE_CMD = dve -vpd $(SIM_DIR)/wave.vpd &
endif

# --------------- Verilator ----------
ifeq ($(SIMULATOR),verilator)
ifdef FILELIST
COMP_CMD = verilator --cc --exe --build --trace \
           -CFLAGS "-std=c++17" \
           -Mdir $(SIM_DIR)/obj_dir \
           --top-module $(TOP_MODULE) \
           $(FLIST_SRCS) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = verilator --cc --exe --build --trace \
           -CFLAGS "-std=c++17" \
           -Mdir $(SIM_DIR)/obj_dir \
           --top-module $(TOP_MODULE) \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = $(SIM_DIR)/obj_dir/V$(TOP_MODULE) \
           +trace +wavefile=$(SIM_DIR)/wave.vcd
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
endif

# --------------- Icarus -------------
ifeq ($(SIMULATOR),iverilog)
ifdef FILELIST
COMP_CMD = iverilog -g2012 -o $(SIM_DIR)/sim.out \
           $(FLIST_SRCS) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = iverilog -g2012 -o $(SIM_DIR)/sim.out \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = vvp $(SIM_DIR)/sim.out +dumpfile=$(SIM_DIR)/wave.vcd
WAVE_CMD = gtkwave $(SIM_DIR)/wave.vcd &
endif

# --------------- Xcelium ------------
ifeq ($(SIMULATOR),xcelium)
ifdef FILELIST
COMP_CMD = xrun -sv -timescale 1ns/1ps -access +rwc \
           -f $(FILELIST) \
           -xmlibdirpath $(SIM_DIR)/work \
           2>&1 | tee $(SIM_DIR)/compile.log
else
COMP_CMD = xrun -sv -timescale 1ns/1ps -access +rwc \
           $(RTL_FILES) $(TB_FILES) \
           -xmlibdirpath $(SIM_DIR)/work \
           2>&1 | tee $(SIM_DIR)/compile.log
endif
SIM_CMD  = xrun -R -input $(SIM_DIR)/wave.tcl
WAVE_CMD = simvisdbutil $(SIM_DIR)/wave.shm &
endif

# =============================================================================
# 公共目标
# =============================================================================

.PHONY: comp sim wave clean

comp:
	@echo "[COMP] Simulator: $(SIMULATOR) | Top: $(TOP_MODULE)"
	@mkdir -p $(SIM_DIR)
	$(COMP_CMD)

sim:
	@echo "[SIM] Running $(TOP_MODULE) ..."
	@mkdir -p $(SIM_DIR)
	$(SIM_CMD) | tee $(SIM_DIR)/sim.log

wave:
	@echo "[WAVE] Opening waveform ..."
	$(WAVE_CMD)

clean:
	@echo "[CLEAN] Removing run artifacts ..."
	rm -rf $(RUN_DIR)/* $(RUN_DIR)/.vlogan* csrc simv* ucli.key vc_hdrs.h
	rm -rf $(SIM_DIR)/* $(SIM_DIR)/.vlogan* csrc simv* ucli.key vc_hdrs.h
	rm -rf obj_dir work *.log *.vpd *.vcd
