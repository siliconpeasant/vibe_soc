# template_ip IP Level Makefile
# 支持 filelist 方式编译、lint 检查、独立仿真
#
# Usage:
#   make flist              # 生成 rtl/filelist.f（本层 RTL 文件列表）
#   make comp               # 编译仿真（DUT + TB），顶层 = tb_<ip_name>
#   make comp TOP_MODULE=x  # 指定任意顶层
#   make sim                # 运行仿真
#   make lint               # Lint 检查（只检查 RTL）
#   make lint LINT_TOOL=iverilog  # 使用 iverilog 做语法检查

PROJECT_ROOT ?= $(shell cd ../../.. && pwd -P)
IP_NAME       = template_ip
# 检测当前工作目录或代理调用的子目录
CURRENT_DIR := $(notdir $(CURDIR))
ifdef SUBDIR
  CURRENT_DIR := $(SUBDIR)
endif

IP_PATH       = $(CURDIR)
ifeq ($(CURRENT_DIR),de)
  IP_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),dv)
  IP_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
endif
ifeq ($(CURRENT_DIR),rtl)
  IP_PATH := $(patsubst %/,%,$(dir $(CURDIR)))
  IP_PATH := $(patsubst %/,%,$(dir $(IP_PATH)))
endif
RTL_PATH      = $(IP_PATH)/de/rtl
TB_PATH       = $(IP_PATH)/dv/tb

# 默认顶层：de/ 或 rtl/ 下用 RTL 模块，其他用 testbench
ifeq ($(CURRENT_DIR),de)
  TOP_MODULE ?= $(IP_NAME)
else ifeq ($(CURRENT_DIR),rtl)
  TOP_MODULE ?= $(IP_NAME)
else
  TOP_MODULE ?= tb_$(IP_NAME)
endif
RTL_TOP      ?= $(IP_NAME)

# =============================================================================
# 依赖管理
# =============================================================================
# 通过 filelist.mk 自动管理依赖（推荐）
# 取消下面一行的注释，并编辑 de/rtl/filelist.mk 配置依赖
# include $(RTL_PATH)/filelist.mk
# =============================================================================

RUN_DIR       = $(IP_PATH)/de/run
SIM_DIR       = $(IP_PATH)/dv/sim
SIM_FLIST     = $(SIM_DIR)/dut.f

# 默认使用 run/dut.f 编译
FILELIST      = $(SIM_FLIST)

include $(PROJECT_ROOT)/scripts/common.mk

# Lint 工具配置
LINT_TOOL    ?= verilator

.PHONY: flist lint

# 生成 rtl/filelist.f（仅当不存在时自动生成，用户可手动编辑）
flist:
	@mkdir -p $(RTL_PATH) $(RUN_DIR) $(SIM_DIR)
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

# comp 默认依赖 dv/sim/dut.f
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
