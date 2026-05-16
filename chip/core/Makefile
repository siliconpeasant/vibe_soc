# core Module Makefile
PROJECT_ROOT ?= $(shell cd ../.. && pwd -P)
MODULE_NAME   = core
# 检测当前工作目录或代理调用的子目录
CURRENT_DIR := $(notdir $(CURDIR))
ifdef SUBDIR
  CURRENT_DIR := $(SUBDIR)
endif

MODULE_PATH   = $(CURDIR)
ifeq ($(CURRENT_DIR),de)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),dv)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),rtl)
  MODULE_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
  MODULE_PATH := $(patsubst %/,%,$(dir $(MODULE_PATH)))
endif
RTL_PATH      = $(MODULE_PATH)/de/rtl
TB_PATH       = $(MODULE_PATH)/dv/tb

# 默认顶层：de/ 或 rtl/ 下用 RTL 模块，其他用 testbench
ifeq ($(CURRENT_DIR),de)
  TOP_MODULE ?= $(MODULE_NAME)
else ifeq ($(CURRENT_DIR),rtl)
  TOP_MODULE ?= $(MODULE_NAME)
else
  TOP_MODULE ?= tb_$(MODULE_NAME)
endif
RTL_TOP      ?= $(MODULE_NAME)

RUN_DIR       = $(MODULE_PATH)/de/run
SIM_DIR       = $(MODULE_PATH)/dv/sim
SIM_FLIST     = $(SIM_DIR)/dut.f

FILELIST      = $(SIM_FLIST)

include $(PROJECT_ROOT)/scripts/common.mk

LINT_TOOL    ?= verilator

# 综合配置
SYN_DIR       = $(MODULE_PATH)/de/syn
SYN_NETLIST   = $(SYN_DIR)/$(RTL_TOP)_netlist.v
SYN_REPORT    = $(SYN_DIR)/synth.log

# =============================================================================
# 依赖管理
# =============================================================================
# 通过 filelist.mk 自动管理依赖（推荐）
# 取消下面一行的注释，并编辑 de/rtl/filelist.mk 配置依赖
# include $(RTL_PATH)/filelist.mk
# =============================================================================

.PHONY: flist lint syn

# 生成 rtl/filelist.f（仅当不存在时自动生成，用户可手动编辑）
flist:
	@mkdir -p $(RTL_PATH) $(TB_PATH) $(RUN_DIR) $(SIM_DIR)
	@if [ ! -f $(RTL_PATH)/filelist.f ]; then 		find $(RTL_PATH) -maxdepth 1 \( -name "*.v" -o -name "*.sv" \) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort > $(RTL_PATH)/filelist.f; 		echo "[FLIST] Generated $(RTL_PATH)/filelist.f"; 	else 		echo "[FLIST] $(RTL_PATH)/filelist.f already exists, skip"; 	fi

# 生成 dv/sim/dut.f（每次 comp 都重新生成）
$(SIM_FLIST): flist
	@mkdir -p $(SIM_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do 		if [ -f $$fl ]; then 			echo "// -f $$fl" >> $@; 			cat $$fl >> $@; 			echo "" >> $@; 		fi; 	done
else
	@cat $(RTL_PATH)/filelist.f >> $@

endif
	@find $(TB_PATH) \( -name "*.v" -o -name "*.sv" \) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort >> $@
	@echo "[FLIST] Generated $@"

comp: $(SIM_FLIST)

# Lint（每次执行都重新生成 de/run/rtl.f 并检查 RTL）
lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do 		if [ -f $$fl ]; then 			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; 			sed 's|\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; 			echo "" >> $(RUN_DIR)/rtl.f; 		fi; 	done
else
	@sed 's|\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
	@verilator --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log || true
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log || true
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
endif
	@echo "[LINT] Report: $(RUN_DIR)/lint.log"
# Yosys synthesis
syn: flist
	@echo "[SYN] Yosys | Top: $(RTL_TOP)"
	@mkdir -p $(SYN_DIR)
	@> $(SYN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			sed 's|[$$]SOC|$(PROJECT_ROOT)|g' $$fl >> $(SYN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|[$$]SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(SYN_DIR)/rtl.f
endif
	@if [ ! -s $(SYN_DIR)/rtl.f ]; then \
		echo "[SYN] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
	@echo "# Auto-generated Yosys synthesis script for $(RTL_TOP)" > $(SYN_DIR)/syn.ys
	@echo "read_verilog $$(grep -v '^#' $(SYN_DIR)/rtl.f | grep -v '^//' | grep -v '^$$' | tr '\n' ' ')" >> $(SYN_DIR)/syn.ys
	@echo "hierarchy -check -top $(RTL_TOP)" >> $(SYN_DIR)/syn.ys
	@echo "proc; flatten; opt; fsm; opt; memory; opt; techmap; opt" >> $(SYN_DIR)/syn.ys
	@echo "write_verilog $$(notdir $(SYN_NETLIST))" >> $(SYN_DIR)/syn.ys
	@echo "stat" >> $(SYN_DIR)/syn.ys
	@cd $(SYN_DIR) && yosys syn.ys 2>&1 | tee $$(notdir $(SYN_REPORT))
	@echo "[SYN] Netlist: $(SYN_NETLIST)"
	@echo "[SYN] Report:  $(SYN_REPORT)"
