#!/usr/bin/env python3
"""
SoC Project Init - 生成标准化 SoC 前端开发项目目录结构
支持 IP 独立仿真，chip/IP/sim 共享 common.mk 环境
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


PROJECT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "project"
CHIP_SUBMODULES = ("core", "bus", "periph", "interconnect", "top", "lib")
MODULE_DIRECTORIES = (
    "docs",
    "de/rtl",
    "de/lint",
    "de/cdc",
    "de/syn",
    "de/formal",
    "de/run",
    "dv/tb",
    "dv/verif",
    "dv/tests",
    "dv/sim",
    "dv/cov",
)


def _module_makefile(module_name: str, project_depth: int, rtl_entry: bool = False) -> str:
    """Return the thin module Makefile used by the current shared build system."""
    parent_chain = "/".join(".." for _ in range(project_depth))
    lines = [
        f"# {module_name} module",
        f"PROJECT_ROOT ?= $(shell cd {parent_chain} && pwd -P)",
        f"MODULE_NAME   = {module_name}",
    ]
    if rtl_entry:
        lines.extend(
            [
                f"RTL_TOP       = {module_name}",
                f"TOP_MODULE    = {module_name}",
            ]
        )
    lines.append("include $(PROJECT_ROOT)/scripts/common.mk")
    return "\n".join(lines) + "\n"


def _install_project_templates(root: Path, project_name: str) -> None:
    """Install the versioned project build template and render its project name."""
    if not PROJECT_TEMPLATE_DIR.is_dir():
        raise FileNotFoundError(f"project template directory not found: {PROJECT_TEMPLATE_DIR}")
    shutil.copytree(PROJECT_TEMPLATE_DIR, root, dirs_exist_ok=True, copy_function=shutil.copy2)
    for path in root.rglob("*"):
        if path.is_file() and path.parent != root / ".git":
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rendered = content.replace("vibe_soc", project_name)
            if rendered != content:
                path.write_text(rendered, encoding="utf-8")

# =============================================================================
# 模板内容
# =============================================================================

MAKEFILE_TOP = """# {project_name} unified build entry

PROJECT_ROOT := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))
MODULE       ?= chip/top
MODULE_DIR   := $(PROJECT_ROOT)/$(MODULE)
TARGET       ?= help

export PROJECT_ROOT

.DEFAULT_GOAL := help

.PHONY: help setup list-modules module flist comp sim lint syn clean

help:
	@echo "{project_name} SoC Build System"
	@echo "==========================="
	@echo "  make list-modules"
	@echo "  make <target> [MODULE=<path>]"
	@echo "Targets: flist comp sim lint syn clean"

setup:
	@bash $(PROJECT_ROOT)/scripts/setup.sh

list-modules:
	@find $(PROJECT_ROOT)/chip $(PROJECT_ROOT)/ip -mindepth 2 -maxdepth 3 \
		-name Makefile ! -path '*/de/Makefile' ! -path '*/dv/Makefile' \
		-printf '%h\n' | sed 's|^$(PROJECT_ROOT)/||' | sort

module:
	@test -f "$(MODULE_DIR)/Makefile" || {{ \
		echo "[ERROR] Invalid MODULE '$(MODULE)'"; exit 2; \
	}}
	@$(MAKE) --no-print-directory -C "$(MODULE_DIR)" "$(TARGET)"

flist comp sim lint syn clean:
	@$(MAKE) --no-print-directory module TARGET=$@
"""

SETUP_SH = """#!/bin/bash
# {project_name} SoC 开发环境初始化脚本

export PROJECT_ROOT=$(cd "$(dirname "${{BASH_SOURCE[0]}}")/.." && pwd -P)
export SOC="$PROJECT_ROOT"
export CHIP_PATH="$PROJECT_ROOT/chip"
export IP_PATH="$PROJECT_ROOT/ip"

# 工具链检测
export SIMULATOR=${{SIMULATOR:-"iverilog"}}   # 可选: vcs, verilator, iverilog, xcelium

echo "======================================"
echo " {project_name} SoC 开发环境已初始化"
echo "======================================"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CHIP_PATH    : $CHIP_PATH"
echo "SIMULATOR    : $SIMULATOR"
echo "======================================"
"""

README_MD = """# {project_name} SoC 前端开发项目

## 目录结构

```
{project_name}/
├── chip/                 # SoC 芯片设计源码 (RTL)
│   ├── core/             # 处理器核心 (RISC-V Core)
│   ├── bus/              # 总线架构 (AXI/AHB/APB)
│   ├── periph/           # 外设 IP (UART/SPI/I2C/PWM/Timer等)
│   ├── interconnect/     # 互联与交叉开关
│   ├── top/              # SoC 顶层模块
│   └── lib/              # 通用库 / 标准单元封装
├── ip/
│   ├── third_party/      # 第三方 IP / 外购软核
│   └── digital/          # 自研 IP / 复用模块
│       └── template_ip/  # IP 模板示例 (可独立编译仿真)
│           ├── docs/
│           ├── de/       # rtl/lint/cdc/syn/formal/run
│           ├── dv/       # tb/verif/tests/sim/cov
│           └── Makefile
├── scripts/              # 项目级公共脚本
│   ├── setup.sh          # 环境初始化与工具检查
│   ├── paths.mk          # 集中路径定义
│   ├── config.mk         # 工具链与项目默认配置
│   ├── common.mk         # 公共构建规则
│   ├── toolchains/       # 仿真器专用配置
│   └── validate_filelist.py
├── doc/                  # 文档
│   ├── arch/             # 架构设计文档
│   └── spec/             # 接口规范与需求
└── Makefile              # 顶层构建入口
```

## 快速开始

### 1. 环境初始化
```bash
source scripts/setup.sh
```

### 2. IP 独立仿真
```bash
cd ip/digital/template_ip
make comp    # 编译 IP 级 testbench
make sim     # 运行 IP 级仿真
make wave    # 查看波形
```

### 3. Chip 级仿真
```bash
cd chip/core && make comp && make sim
cd chip/top  && make comp && make sim
```

## 工具链支持

- **仿真**: VCS, Verilator, Iverilog, Xcelium

## 开发规范

- 所有 RTL 文件使用 `*.v` / `*.sv` 扩展名
- 模块名与文件名保持一致
- 每个 IP 独立目录，包含 RTL + 可独立编译的 testbench
- 顶层模块统一放在 `chip/top/`
- 所有子目录 Makefile 均引用 `scripts/common.mk`，确保编译环境一致
"""

TB_TOP_SV = """// {project_name} SoC Top-Level Testbench
// TODO: Replace with actual DUT instantiation

`timescale 1ns / 1ps

module tb_top;

  logic clk;
  logic rst_n;

  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;  // 100 MHz
  end

  // Reset generation
  initial begin
    rst_n = 0;
    #100;  // 10 clock cycles
    rst_n = 1;
  end

  // DUT instantiation placeholder
  // {top_module} u_dut (
  //   .clk   (clk),
  //   .rst_n (rst_n),
  //   ...
  // );

  // Waveform dump
  initial begin
    $dumpfile("run/wave.vcd");
    $dumpvars(0, tb_top);
  end

  // Test sequence
  initial begin
    $display("==================================");
    $display(" {project_name} SoC Simulation Start ");
    $display("==================================");

    // TODO: Add stimulus here

    #10000;  // 1000 clock cycles

    $display("==================================");
    $display(" {project_name} SoC Simulation Done  ");
    $display("==================================");
    $finish;
  end

endmodule
"""

SDC_TEMPLATE = """# SDC Constraints for {top_module}
# Please customize according to your PPA targets and clock definitions

set clk_name      clk
set clk_period    10.0      ;# 100 MHz default
set clk_uncertainty 0.1
set clk_transition  0.05

create_clock -name $clk_name -period $clk_period [get_ports clk]
set_clock_uncertainty $clk_uncertainty [get_clocks $clk_name]
set_clock_transition  $clk_transition  [get_clocks $clk_name]

# Input / Output delays
set_input_delay  -clock $clk_name -max [expr $clk_period * 0.3] [all_inputs]
set_output_delay -clock $clk_name -max [expr $clk_period * 0.3] [all_outputs]

# Drive / Load assumptions
set_drive_cell  -lib_cell BUFX2 [all_inputs]
set_load        0.05 [all_outputs]

# Set false paths for reset if asynchronous
# set_false_path -from [get_ports rst_n]
"""

YOSYS_TCL = """# Yosys Synthesis Script for {project_name}

set TOP_MODULE $::env(TOP_MODULE)
set CHIP_PATH  $::env(CHIP_PATH)
set RESULTS    $::env(RESULTS_PATH)
set REPORTS    $::env(REPORTS_PATH)

yosys read_verilog [glob -nocomplain $CHIP_PATH/*/de/rtl/*.v $CHIP_PATH/*/de/rtl/*.sv]
yosys hierarchy -check -top $TOP_MODULE
yosys proc
yosys flatten
yosys opt
yosys fsm
yosys opt
yosys memory
yosys opt
yosys techmap
yosys opt

yosys write_verilog $RESULTS/${{TOP_MODULE}}_netlist.v
yosys stat > $REPORTS/${{TOP_MODULE}}_area.rpt
yosys show -format dot -prefix $REPORTS/${{TOP_MODULE}}

puts "Yosys synthesis completed."
puts "Netlist: $RESULTS/${{TOP_MODULE}}_netlist.v"
"""

DC_TCL = """# Design Compiler Synthesis Script for {project_name}

set TOP_MODULE      [lindex $argv 0]
set CHIP_PATH       [lindex $argv 1]
set RESULTS_PATH    [lindex $argv 2]
set REPORTS_PATH    [lindex $argv 3]
set CONSTRAINT_FILE [lindex $argv 4]

# set target_library "your_stdcell.db"
# set link_library   "* $target_library"

set rtl_files [glob -nocomplain $CHIP_PATH/*/de/rtl/*.v $CHIP_PATH/*/de/rtl/*.sv]
read_verilog $rtl_files

current_design $TOP_MODULE
link_design

if {{[file exists $CONSTRAINT_FILE]}} {{
    source $CONSTRAINT_FILE
}}

compile_ultra

write_file -format verilog -hierarchy -output $RESULTS_PATH/${{TOP_MODULE}}_netlist.v
write_file -format ddc     -hierarchy -output $RESULTS_PATH/${{TOP_MODULE}}.ddc
write_sdc -version 2.0               -output $RESULTS_PATH/${{TOP_MODULE}}.sdc

report_timing  > $REPORTS_PATH/${{TOP_MODULE}}_timing.rpt
report_area    > $REPORTS_PATH/${{TOP_MODULE}}_area.rpt
report_power   > $REPORTS_PATH/${{TOP_MODULE}}_power.rpt
report_qor     > $REPORTS_PATH/${{TOP_MODULE}}_qor.rpt

puts "DC synthesis completed."
"""

COMMON_MK = r"""# =============================================================================
# Common Makefile for SoC Project Simulation
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
# 使用方式：在子 Makefile 中定义以下变量，然后 include 本文件
#
#   PROJECT_ROOT  = $(shell cd <relative_to_root> && pwd)
#   RTL_FILES     = $(shell find <rtl_dir> -name "*.v" -o -name "*.sv")
#   TB_FILES      = $(shell find <tb_dir> -name "*.v" -o -name "*.sv")
#   TOP_MODULE    ?= tb_top
#   RUN_DIR       ?= $(PWD)/run
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

# --------------- VCS ---------------
ifeq ($(SIMULATOR),vcs)
COMP_CMD = vcs -sverilog -full64 -timescale=1ns/1ps \
           +v2k -debug_access+all -kdb \
           $(RTL_FILES) $(TB_FILES) \
           -o $(RUN_DIR)/simv
SIM_CMD  = $(RUN_DIR)/simv +vpdfile+$(RUN_DIR)/wave.vpd
WAVE_CMD = dve -vpd $(RUN_DIR)/wave.vpd &
endif

# --------------- Verilator ----------
ifeq ($(SIMULATOR),verilator)
COMP_CMD = verilator --cc --exe --build --trace \
           -CFLAGS "-std=c++17" \
           -Mdir $(RUN_DIR)/obj_dir \
           --top-module $(TOP_MODULE) \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(RUN_DIR)/compile.log
SIM_CMD  = $(RUN_DIR)/obj_dir/V$(TOP_MODULE) \
           +trace +wavefile=$(RUN_DIR)/wave.vcd
WAVE_CMD = gtkwave $(RUN_DIR)/wave.vcd &
endif

# --------------- Icarus -------------
ifeq ($(SIMULATOR),iverilog)
COMP_CMD = iverilog -g2012 -o $(RUN_DIR)/sim.out \
           $(RTL_FILES) $(TB_FILES) \
           2>&1 | tee $(RUN_DIR)/compile.log
SIM_CMD  = vvp $(RUN_DIR)/sim.out +dumpfile=$(RUN_DIR)/wave.vcd
WAVE_CMD = gtkwave $(RUN_DIR)/wave.vcd &
endif

# --------------- Xcelium ------------
ifeq ($(SIMULATOR),xcelium)
COMP_CMD = xrun -sv -timescale 1ns/1ps -access +rwc \
           $(RTL_FILES) $(TB_FILES) \
           -xmlibdirpath $(RUN_DIR)/work \
           2>&1 | tee $(RUN_DIR)/compile.log
SIM_CMD  = xrun -R -input $(RUN_DIR)/wave.tcl
WAVE_CMD = simvisdbutil $(RUN_DIR)/wave.shm &
endif

# =============================================================================
# 公共目标
# =============================================================================

.PHONY: comp sim wave clean

comp:
	@echo "[COMP] Simulator: $(SIMULATOR) | Top: $(TOP_MODULE)"
	@mkdir -p $(RUN_DIR)
	$(COMP_CMD)

sim: comp
	@echo "[SIM] Running $(TOP_MODULE) ..."
	@mkdir -p $(RUN_DIR)
	$(SIM_CMD) | tee $(RUN_DIR)/sim.log

wave:
	@echo "[WAVE] Opening waveform ..."
	$(WAVE_CMD)

clean:
	@echo "[CLEAN] Removing run artifacts ..."
	rm -rf $(RUN_DIR)/* $(RUN_DIR)/.vlogan* csrc simv* ucli.key vc_hdrs.h
	rm -rf obj_dir work *.log *.vpd *.vcd
"""

SIM_MAKEFILE = """# {project_name} SoC 仿真 Makefile (全芯片级)
# 支持 filelist 方式编译，可指定任意顶层
#
# Usage:
#   make flist              # 生成各模块 rtl/filelist.f
#   make comp               # 编译仿真，顶层 = tb_top
#   make comp TOP_MODULE=x  # 指定任意顶层
#   make sim                # 运行仿真
#   make lint               # Lint 检查（只检查 RTL）

PROJECT_ROOT ?= $(shell cd .. && pwd -P)
CHIP_PATH     = $(PROJECT_ROOT)/chip
IP_PATH       = $(PROJECT_ROOT)/ip

TOP_MODULE   ?= {top_module}
RTL_TOP      ?= {top_module}

# =============================================================================
# 依赖管理
# =============================================================================
# 通过 filelist.mk 自动管理依赖。
-include $(PROJECT_ROOT)/chip/top/de/rtl/filelist.mk
# =============================================================================

RUN_DIR       = $(PROJECT_ROOT)/sim/run
SIM_FLIST     = $(RUN_DIR)/dut.f

FILELIST      = $(SIM_FLIST)

include $(PROJECT_ROOT)/scripts/common.mk

LINT_TOOL    ?= verilator

.PHONY: flist lint

# 生成各模块 rtl/filelist.f（使用 $$SOC 绝对路径）
flist:
	@for mod in $(CHIP_PATH)/*; do \
		if [ -d $$mod/de/rtl ]; then \
			find $$mod/de/rtl -type f \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort > $$mod/de/rtl/filelist.f; \
		fi; \
	done
	@for ip in $(IP_PATH)/digital/* $(IP_PATH)/third_party/*; do \
		if [ -d $$ip/de/rtl ]; then \
			find $$ip/de/rtl -type f \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort > $$ip/de/rtl/filelist.f; \
		fi; \
	done

# 生成 run/dut.f = 各模块 rtl/filelist.f（纯 RTL，不含 TB）
$(SIM_FLIST): flist
	@mkdir -p $(RUN_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@cat $(CHIP_PATH)/rtl/filelist.f >> $@
	@for ip in $(IP_PATH)/digital/* $(IP_PATH)/third_party/*; do \
		if [ -f $$ip/de/rtl/filelist.f ]; then \
			cat $$ip/de/rtl/filelist.f >> $@; \
		fi; \
	done

endif
	@echo "[FLIST] Generated $@"

comp: $(SIM_FLIST)

lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; \
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; \
			echo "" >> $(RUN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(CHIP_PATH)/rtl/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
	@verilator -Wall --lint-only -I$(CHIP_PATH)/rtl -I$(IP_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
endif
	@echo "[LINT] Report: $(RUN_DIR)/lint.log"
"""

SYN_MAKEFILE = """# {project_name} SoC 逻辑综合 Makefile

PROJECT_ROOT    ?= $(shell cd .. && pwd -P)
CHIP_PATH        = $(PROJECT_ROOT)/chip
CONS_PATH        = $(PROJECT_ROOT)/syn/constraints
RESULTS_PATH     = $(PROJECT_ROOT)/syn/results
REPORTS_PATH     = $(PROJECT_ROOT)/syn/reports
SCRIPTS_PATH     = $(PROJECT_ROOT)/syn/scripts

SYN_TOOL        ?= yosys
TOP_MODULE      ?= {top_module}
RTL_FILES       ?= $(shell find $(CHIP_PATH) -name "*.v" -o -name "*.sv")
CONSTRAINT_FILE ?= $(CONS_PATH)/$(TOP_MODULE).sdc

ifeq ($(SYN_TOOL),dc)
SYN_CMD = dc_shell -f $(SCRIPTS_PATH)/dc_syn.tcl \
          -x "set TOP_MODULE $(TOP_MODULE); set CHIP_PATH $(CHIP_PATH); set RESULTS_PATH $(RESULTS_PATH); set REPORTS_PATH $(REPORTS_PATH); set CONSTRAINT_FILE $(CONSTRAINT_FILE)" \
          2>&1 | tee $(RESULTS_PATH)/syn.log
endif

ifeq ($(SYN_TOOL),genus)
SYN_CMD = genus -f $(SCRIPTS_PATH)/genus_syn.tcl \
          -log $(RESULTS_PATH)/syn.log \
          -cmd "set TOP_MODULE $(TOP_MODULE); set CHIP_PATH $(CHIP_PATH); set RESULTS_PATH $(RESULTS_PATH); set REPORTS_PATH $(REPORTS_PATH); set CONSTRAINT_FILE $(CONSTRAINT_FILE)"
endif

ifeq ($(SYN_TOOL),yosys)
SYN_CMD = yosys -c $(SCRIPTS_PATH)/yosys_syn.tcl \
          2>&1 | tee $(RESULTS_PATH)/syn.log
endif

.PHONY: syn flist clean report

flist:
	@mkdir -p $(RESULTS_PATH) $(REPORTS_PATH)
	@echo "# RTL Files" > $(RESULTS_PATH)/rtl.f
	@echo "$(RTL_FILES)" | tr ' ' '\\n' >> $(RESULTS_PATH)/rtl.f
	@echo "RTL filelist generated at $(RESULTS_PATH)/rtl.f"

syn: flist
	@echo "[SYN] Running synthesis with $(SYN_TOOL) ..."
	@mkdir -p $(RESULTS_PATH) $(REPORTS_PATH)
	$(SYN_CMD)

report:
	@echo "[SYN] Synthesis reports:"
	@ls -lh $(REPORTS_PATH)/ 2>/dev/null || echo "No reports yet."

clean:
	rm -rf $(RESULTS_PATH)/* $(REPORTS_PATH)/* 
	rm -rf command.log default.svf filenames.log
"""

CHIP_MAKEFILE = """# {project_name} SoC Chip-Level Makefile
# 汇总所有子模块 rtl/filelist.f
#
# Usage:
#   make flist              # 生成 chip/rtl/filelist.f
#   make comp               # 编译仿真，顶层 = tb_chip_top
#   make comp TOP_MODULE=x  # 指定任意顶层
#   make lint               # Lint 检查（只检查 RTL）

PROJECT_ROOT ?= $(shell cd .. && pwd -P)
CHIP_PATH     = $(PROJECT_ROOT)/chip

TOP_MODULE   ?= tb_chip_top
RTL_TOP      ?= {top_module}

# =============================================================================
# 依赖管理
# =============================================================================
# 通过 filelist.mk 自动管理依赖（推荐）
# 取消下面一行的注释，并编辑对应模块的 de/rtl/filelist.mk 配置依赖
# include $(CHIP_PATH)/core/de/rtl/filelist.mk
# =============================================================================

RUN_DIR       = $(CHIP_PATH)/run
SIM_FLIST     = $(RUN_DIR)/dut.f

FILELIST      = $(SIM_FLIST)

include $(PROJECT_ROOT)/scripts/common.mk

LINT_TOOL    ?= verilator

.PHONY: flist lint

# 生成 chip/rtl/filelist.f（自动遍历 chip/ 下所有带 rtl/ 的子模块）
flist:
	@mkdir -p $(CHIP_PATH)/rtl $(RUN_DIR)
	@> $(CHIP_PATH)/rtl/filelist.f
	@for subdir in $(CHIP_PATH)/*/; do \
		subdir=$${{subdir%/}}; \
		if [ -d $${{subdir}}/de/rtl ]; then \
			find $${{subdir}}/de/rtl -maxdepth 1 \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort >> $(CHIP_PATH)/rtl/filelist.f; \
		fi; \
	done
	@echo "[FLIST] Generated $(CHIP_PATH)/rtl/filelist.f"

# 生成 run/dut.f（直接展开）
$(SIM_FLIST): flist
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@cat $(CHIP_PATH)/rtl/filelist.f >> $@

endif
	@echo "[FLIST] Generated $@"

comp: $(SIM_FLIST)

lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; \
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; \
			echo "" >> $(RUN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(CHIP_PATH)/rtl/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
		@verilator -Wall --lint-only -I$(CHIP_PATH)/rtl --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
		@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
else
	@echo "[LINT] Unknown LINT_TOOL: $(LINT_TOOL)"
endif
	@echo "[LINT] Report: $(RUN_DIR)/lint.log"
"""

IP_RTL_V = """// {ip_name} - Self-Developed IP Template
// TODO: Replace with actual IP logic

`timescale 1ns / 1ps

module {ip_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data_in,
    input  wire        valid_in,
    output reg  [7:0]  data_out,
    output reg         valid_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out  <= 8'b0;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            data_out  <= data_in + 1'b1;  // Example logic
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end

endmodule
"""

IP_TB_SV = """// {ip_name} - IP Level Testbench
// Self-checking testbench, compatible with iverilog / vcs / verilator 5.0+

`timescale 1ns / 1ps

module tb_{ip_name};

    logic clk;
    logic rst_n;
    logic [7:0] data_in;
    logic       valid_in;
    logic [7:0] data_out;
    logic       valid_out;

    int         error_cnt = 0;
    int         check_cnt = 0;

    // Clock generation: 100 MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #50;  // 5 clock cycles
        rst_n = 1;
    end

    // DUT instantiation
    {ip_name} u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .data_in   (data_in),
        .valid_in  (valid_in),
        .data_out  (data_out),
        .valid_out (valid_out)
    );

    // Waveform dump
    initial begin
        $dumpfile("dv/sim/wave.vcd");
        $dumpvars(0, tb_{ip_name});
    end

    // Self-checking: verify output when valid_out is high
    always @(posedge clk) begin
        if (valid_out) begin
            check_cnt++;
            if (data_out !== (data_in + 1'b1)) begin
                $error("[FAIL] check #%0d: expected 0x%02X, got 0x%02X",
                       check_cnt, data_in + 1'b1, data_out);
                error_cnt++;
            end else begin
                $display("[PASS] check #%0d: data_out = 0x%02X (expected 0x%02X)",
                         check_cnt, data_out, data_in + 1'b1);
            end
        end
    end

    // Stimulus
    initial begin
        $display("==================================");
        $display(" {ip_name} IP Simulation Start ");
        $display("==================================");

        data_in  = 8'h00;
        valid_in = 1'b0;

        #70;  // wait for reset release + 2 cycles

        // Test case 1
        #10;
        data_in  = 8'hAA;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // 5 clock cycles

        // Test case 2
        #10;
        data_in  = 8'h55;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // 5 clock cycles

        // Test case 3: boundary value 0xFF
        #10;
        data_in  = 8'hFF;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // wait for last check

        $display("==================================");
        if (error_cnt == 0)
            $display("  ALL PASSED (%0d checks)", check_cnt);
        else
            $display("  FAILED: %0d / %0d checks failed", error_cnt, check_cnt);
        $display(" {ip_name} IP Simulation Done  ");
        $display("==================================");
        $finish;
    end

endmodule
"""

IP_MAKEFILE = """# {ip_name} IP Level Makefile
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
IP_NAME       = {ip_name}
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
# 通过 filelist.mk 自动管理依赖。
-include $(RTL_PATH)/filelist.mk
# =============================================================================

RUN_DIR       = $(IP_PATH)/de/run
SIM_DIR       = $(IP_PATH)/dv/sim
SIM_FLIST     = $(SIM_DIR)/dut.f

# 默认使用 run/dut.f 编译
FILELIST      = $(SIM_FLIST)

include $(PROJECT_ROOT)/scripts/common.mk

# Lint 工具配置
LINT_TOOL    ?= verilator

# 综合配置
SYN_DIR       = $(IP_PATH)/de/syn
SYN_NETLIST   = $(SYN_DIR)/$(RTL_TOP)_netlist.v
SYN_REPORT    = $(SYN_DIR)/synth.log

.PHONY: flist lint syn

# 生成 rtl/filelist.f（仅当不存在时自动生成，用户可手动编辑）
flist:
	@mkdir -p $(RTL_PATH) $(RUN_DIR) $(SIM_DIR)
	@if [ ! -f $(RTL_PATH)/filelist.f ]; then \
		find $(RTL_PATH) -type f \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort > $(RTL_PATH)/filelist.f; \
		echo "[FLIST] Generated $(RTL_PATH)/filelist.f"; \
	else \
		echo "[FLIST] $(RTL_PATH)/filelist.f already exists, skip"; \
	fi

# 生成 dv/sim/dut.f（每次 comp 都重新生成）
$(SIM_FLIST): flist
	@mkdir -p $(SIM_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@cat $(RTL_PATH)/filelist.f >> $@

endif
	@find $(TB_PATH) \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort >> $@
	@echo "[FLIST] Generated $@"

# comp 默认依赖 dv/sim/dut.f
comp: $(SIM_FLIST)

# Lint（每次执行都重新生成 de/run/rtl.f 并检查 RTL）
lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; \
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; \
			echo "" >> $(RUN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
	@verilator -Wall --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
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
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(SYN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(SYN_DIR)/rtl.f
endif
	@if [ ! -s $(SYN_DIR)/rtl.f ]; then \
		echo "[SYN] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
	@echo "# Auto-generated Yosys synthesis script for $(RTL_TOP)" > $(SYN_DIR)/syn.ys
	@echo "read_verilog $$(grep -v '^#' $(SYN_DIR)/rtl.f | grep -v '^//' | grep -v '^$$' | tr '\\n' ' ')" >> $(SYN_DIR)/syn.ys
	@echo "hierarchy -check -top $(RTL_TOP)" >> $(SYN_DIR)/syn.ys
	@echo "proc; flatten; opt; fsm; opt; memory; opt; techmap; opt" >> $(SYN_DIR)/syn.ys
	@echo "write_verilog $(notdir $(SYN_NETLIST))" >> $(SYN_DIR)/syn.ys
	@echo "stat" >> $(SYN_DIR)/syn.ys
	@cd $(SYN_DIR) && yosys syn.ys 2>&1 | tee $(notdir $(SYN_REPORT))
	@echo "[SYN] Netlist: $(SYN_NETLIST)"
	@echo "[SYN] Report:  $(SYN_REPORT)"
"""

IP_README_MD = """# {ip_name} IP

## 简介

{ip_name} 是自研 IP 模块。

## 目录结构

```
{ip_name}/
├── de/
│   ├── rtl/      # RTL 源码
│   ├── lint/     # Lint 脚本/报告
│   ├── cdc/      # CDC 配置
│   ├── syn/      # 综合约束/脚本
│   ├── formal/   # 形式验证
│   └── run/      # 设计生成文件
├── dv/
│   ├── tb/       # Testbench (可独立编译仿真)
│   ├── verif/    # 验证脚本
│   ├── tests/    # Test case
│   └── sim/      # 验证生成文件
├── Makefile      # IP 级仿真入口
└── README.md     # 本文档
```

## 独立仿真

```bash
cd ip/digital/{ip_name}       # 根目录执行
cd ip/digital/{ip_name}/de    # de 目录下也能执行
cd ip/digital/{ip_name}/dv    # dv 目录下也能执行
make comp    # 编译
make sim     # 运行仿真
make wave    # 查看波形
make clean   # 清理
```

## 集成到 Chip

将 RTL 文件放入 `chip/periph/de/rtl/` 或 `chip/bus/de/rtl/` 等对应目录，
然后在 `chip/top/de/rtl/` 的顶层模块中实例化。

## 端口说明

| 信号名 | 方向 | 位宽 | 说明 |
|--------|------|------|------|
| clk    | input | 1 | 时钟 |
| rst_n  | input | 1 | 异步复位，低有效 |
| data_in | input | 8 | 输入数据 |
| valid_in | input | 1 | 输入有效 |
| data_out | output | 8 | 输出数据 |
| valid_out | output | 1 | 输出有效 |
"""

FILELIST_MK = """# {module_name} - RTL Filelist Dependencies
# 用法: 在其他 Makefile 中 include $(PROJECT_ROOT)/.../de/rtl/filelist.mk

ifndef {module_name_upper}_FILELIST_MK
{module_name_upper}_FILELIST_MK := 1

# 本模块 RTL filelist（自动推导当前目录）
{module_name_upper}_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f

# ---------------------------------------------------------------------------
# 依赖的子模块：取消注释并添加你依赖的其他模块的 filelist.mk
# ---------------------------------------------------------------------------

# include $(PROJECT_ROOT)/ip/digital/sub_ip/de/rtl/filelist.mk

# ---------------------------------------------------------------------------

# 注册到全局收集变量（去重：已存在则不重复添加）
ifeq (,$(filter $({module_name_upper}_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $({module_name_upper}_FILELIST)
endif

endif
"""

CHIP_SUB_MAKEFILE = """# {module_name} Module Makefile
PROJECT_ROOT ?= $(shell cd ../.. && pwd -P)
MODULE_NAME   = {module_name}
# 检测当前工作目录或代理调用的子目录
CURRENT_DIR := $(notdir $(CURDIR))
ifdef SUBDIR
  CURRENT_DIR := $(SUBDIR)
endif

MODULE_PATH   = $(CURDIR)
ifndef SUBDIR
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
# 通过 filelist.mk 自动管理依赖。
-include $(RTL_PATH)/filelist.mk
# =============================================================================

.PHONY: flist lint syn

# 生成 rtl/filelist.f（仅当不存在时自动生成，用户可手动编辑）
flist:
	@mkdir -p $(RTL_PATH) $(TB_PATH) $(RUN_DIR) $(SIM_DIR)
	@if [ ! -f $(RTL_PATH)/filelist.f ]; then \
		find $(RTL_PATH) -type f \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort > $(RTL_PATH)/filelist.f; \
		echo "[FLIST] Generated $(RTL_PATH)/filelist.f"; \
	else \
		echo "[FLIST] $(RTL_PATH)/filelist.f already exists, skip"; \
	fi

# 生成 dv/sim/dut.f（每次 comp 都重新生成）
$(SIM_FLIST): flist
	@mkdir -p $(SIM_DIR)
	@> $@
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $@; \
			cat $$fl >> $@; \
			echo "" >> $@; \
		fi; \
	done
else
	@cat $(RTL_PATH)/filelist.f >> $@

endif
	@find $(TB_PATH) \\( -name "*.v" -o -name "*.sv" \\) | sed 's|^$(PROJECT_ROOT)/|$$SOC/|' | sort >> $@
	@echo "[FLIST] Generated $@"

comp: $(SIM_FLIST)

# Lint（每次执行都重新生成 de/run/rtl.f 并检查 RTL）
lint: flist
	@echo "[LINT] Tool: $(LINT_TOOL) | Top: $(RTL_TOP)"
	@mkdir -p $(RUN_DIR)
	@> $(RUN_DIR)/rtl.f
ifneq (,$(MODULE_FILELISTS))
	@for fl in $(MODULE_FILELISTS); do \
		if [ -f $$fl ]; then \
			echo "// -f $$fl" >> $(RUN_DIR)/rtl.f; \
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(RUN_DIR)/rtl.f; \
			echo "" >> $(RUN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(RUN_DIR)/rtl.f
endif
ifeq ($(LINT_TOOL),verilator)
	@verilator -Wall --lint-only -I$(RTL_PATH) --top-module $(RTL_TOP) -f $(RUN_DIR)/rtl.f 2>&1 | tee $(RUN_DIR)/lint.log
else ifeq ($(LINT_TOOL),iverilog)
	@iverilog -g2012 -o /dev/null $$(grep -v '^//' $(RUN_DIR)/rtl.f 2>/dev/null | sed '/^$$/d') 2>&1 | tee $(RUN_DIR)/lint.log
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
			sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $$fl >> $(SYN_DIR)/rtl.f; \
		fi; \
	done
else
	@sed 's|\\$$SOC|$(PROJECT_ROOT)|g' $(RTL_PATH)/filelist.f > $(SYN_DIR)/rtl.f
endif
	@if [ ! -s $(SYN_DIR)/rtl.f ]; then \
		echo "[SYN] ERROR: No RTL files found in $(RTL_PATH)"; \
		exit 1; \
	fi
	@echo "# Auto-generated Yosys synthesis script for $(RTL_TOP)" > $(SYN_DIR)/syn.ys
	@echo "read_verilog $$(grep -v '^#' $(SYN_DIR)/rtl.f | grep -v '^//' | grep -v '^$$' | tr '\\n' ' ')" >> $(SYN_DIR)/syn.ys
	@echo "hierarchy -check -top $(RTL_TOP)" >> $(SYN_DIR)/syn.ys
	@echo "proc; flatten; opt; fsm; opt; memory; opt; techmap; opt" >> $(SYN_DIR)/syn.ys
	@echo "write_verilog $(notdir $(SYN_NETLIST))" >> $(SYN_DIR)/syn.ys
	@echo "stat" >> $(SYN_DIR)/syn.ys
	@cd $(SYN_DIR) && yosys syn.ys 2>&1 | tee $(notdir $(SYN_REPORT))
	@echo "[SYN] Netlist: $(SYN_NETLIST)"
	@echo "[SYN] Report:  $(SYN_REPORT)"
"""

CHIP_SUB_README_MD = """# {module_name} Module

## 简介

{module_name} 是芯片 {project_name} 的子模块。

## 目录结构

```
{module_name}/
├── de/
│   ├── rtl/      # RTL 源码
│   ├── lint/     # Lint 脚本/报告
│   ├── cdc/      # CDC 配置
│   ├── syn/      # 综合约束/脚本
│   ├── formal/   # 形式验证
│   └── run/      # 设计生成文件
├── dv/
│   ├── tb/       # Testbench
│   ├── verif/    # 验证脚本
│   ├── tests/    # Test case
│   └── sim/      # 验证生成文件
└── Makefile      # 模块级仿真 / lint 入口
```

## 使用

```bash
cd chip/{module_name}       # 根目录执行
cd chip/{module_name}/de    # de 目录下也能执行
cd chip/{module_name}/dv    # dv 目录下也能执行
make flist    # 生成 rtl/filelist.f
make lint     # 语法检查
make comp     # 编译仿真
make sim      # 运行仿真
```
"""

CHIP_SUB_TB_SV = """// {module_name} - Module Level Testbench
// Placeholder: please instantiate your DUT and add stimulus

`timescale 1ns / 1ps

module tb_{module_name};

    logic clk;
    logic rst_n;

    // Clock generation: 100 MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #50;
        rst_n = 1;
    end

    // Waveform dump
    initial begin
        $dumpfile("dv/sim/wave.vcd");
        $dumpvars(0, tb_{module_name});
    end

    // TODO: Instantiate DUT here

    initial begin
        $display("==================================");
        $display(" {module_name} Simulation Start ");
        $display("==================================");
        #200;
        $display("==================================");
        $display(" {module_name} Simulation Done  ");
        $display("==================================");
        $finish;
    end

endmodule
"""

SUBDIR_MAKEFILE = """# Wrapper Makefile: delegates to parent directory
.PHONY: all flist lint comp sim wave clean

all flist lint comp sim wave clean:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@

%:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
"""

CHIP_SUB_RTL_V = """// {module_name} - Chip Sub-Module
// Generated by soc-build skill

`timescale 1ns / 1ps

module {module_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data_in,
    input  wire        valid_in,
    output reg  [7:0]  data_out,
    output reg         valid_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out  <= 8'b0;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            data_out  <= data_in + 8'h1;
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end

endmodule
"""

CHIP_TOP_SV = """// {top_module} - SoC Top-Level Module
// Generated by soc-build skill

`timescale 1ns / 1ps

module {top_module} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  gpio_in,
    output reg  [7:0]  gpio_out
);

    reg [31:0] counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter  <= 32'b0;
            gpio_out <= 8'b0;
        end else begin
            counter  <= counter + 1'b1;
            gpio_out <= gpio_in ^ counter[7:0];
        end
    end

endmodule
"""

CLAUDE_MD = """# {project_name} SoC 项目规范

## SoC 设计流程（强制）

所有 RTL 模块设计必须遵循 `doc -> rtl -> {{verif, syn}}` 门控流程：

1. **阶段 1 — 文档**: `soc-doc-engineer` 编写 design_spec.md / interface_spec.md / regmap.md / verification_plan.md
2. **阶段 2 — RTL**: `soc-rtl-designer` 编写可综合 Verilog-2005 RTL，verilator -Wall lint-clean
3. **阶段 3 — 验证**: `soc-verification-engineer` 编写自检 testbench，通过 `soc_sim` 执行真实仿真
4. **阶段 4 — 综合**: `soc-synthesis-engineer` 通过 `soc_syn` 产出网表和综合日志；仅真实 STA 报告可证明时序

### RTL 阶段特化 agent

阶段 2 (RTL) 根据子模块类型可选择特化 agent，产物必须落在 `de/rtl/` 和 `de/syn/`：

- **`soc-crg-engineer`** — 子模块是 CRG (时钟复位生成)，从 Excel 配置 (top_info/clk_gen/rst_gen sheet) 驱动。**必须用 `crg_gen` MCP 工具**，禁止手写时钟分频/复位同步逻辑
- **`soc-integrator`** — 顶层集成，把多个 rtl=done 的子模块拼成 top。**必须用 `soc_integrate` MCP 工具生成 top.v、`soc_flist` MCP 工具生成 filelist**，禁止手写

选择规则:
- 普通组合/时序/状态机 → `soc-rtl-designer` (默认)
- CRG 子模块 + Excel 配置 → `soc-crg-engineer`
- 顶层集成 (已有多个子模块 rtl=done) → `soc-integrator`

## 工具链

- **Lint**: `verilator --lint-only -Wall`（通过 soc-build MCP `soc_lint`）
- **仿真**: 通过 soc-build MCP `soc_sim`（内部先编译再运行）
- **综合**: `yosys`（通过 soc-build MCP 或 soc-synthesis-engineer）
- **端口管理**: soc-integrate MCP `soc_extract`, `soc_snapshot`, `soc_update`

## 例外规则

- `std_cell/` 下的简单组合逻辑标准单元可跳过阶段 1，但仍需阶段 2→4
- 经批准的 Bug 修复/小改动可记录文档阶段例外，再执行 RTL 与验证

## 编码规范

- 语言: Verilog-2001，可综合，无 latch 推断
- 复位: 异步低有效 `rst_n`，所有时序逻辑必须复位
- 参数: 使用 `parameter`，localparam 用于派生常量
- 文件命名: `<module_name>.v`，与模块名一致
"""


# =============================================================================
# 目录与文件配置
# =============================================================================

DIRECTORIES = [
    # chip sub-modules
    "chip/core/de/rtl",
    "chip/core/de/lint",
    "chip/core/de/cdc",
    "chip/core/de/syn",
    "chip/core/de/formal",
    "chip/core/dv/tb",
    "chip/core/dv/verif",
    "chip/core/dv/tests",
    "chip/core/de/run",
    "chip/core/dv/sim",
    "chip/bus/de/rtl",
    "chip/bus/de/lint",
    "chip/bus/de/cdc",
    "chip/bus/de/syn",
    "chip/bus/de/formal",
    "chip/bus/dv/tb",
    "chip/bus/dv/verif",
    "chip/bus/dv/tests",
    "chip/bus/de/run",
    "chip/bus/dv/sim",
    "chip/periph/de/rtl",
    "chip/periph/de/lint",
    "chip/periph/de/cdc",
    "chip/periph/de/syn",
    "chip/periph/de/formal",
    "chip/periph/dv/tb",
    "chip/periph/dv/verif",
    "chip/periph/dv/tests",
    "chip/periph/de/run",
    "chip/periph/dv/sim",
    "chip/interconnect/de/rtl",
    "chip/interconnect/de/lint",
    "chip/interconnect/de/cdc",
    "chip/interconnect/de/syn",
    "chip/interconnect/de/formal",
    "chip/interconnect/dv/tb",
    "chip/interconnect/dv/verif",
    "chip/interconnect/dv/tests",
    "chip/interconnect/de/run",
    "chip/interconnect/dv/sim",
    "chip/top/de/rtl",
    "chip/top/de/lint",
    "chip/top/de/cdc",
    "chip/top/de/syn",
    "chip/top/de/formal",
    "chip/top/dv/tb",
    "chip/top/dv/verif",
    "chip/top/dv/tests",
    "chip/top/de/run",
    "chip/top/dv/sim",
    "chip/lib/de/rtl",
    "chip/lib/de/lint",
    "chip/lib/de/cdc",
    "chip/lib/de/syn",
    "chip/lib/de/formal",
    "chip/lib/dv/tb",
    "chip/lib/dv/verif",
    "chip/lib/dv/tests",
    "chip/lib/de/run",
    "chip/lib/dv/sim",
    # project-level dirs
    "ip/third_party",
    "ip/digital",
    "scripts",
    "doc/arch",
    "doc/spec",
]

FILES = {
    "Makefile": MAKEFILE_TOP,
    "scripts/setup.sh": SETUP_SH,
    "README.md": README_MD,
    "CLAUDE.md": CLAUDE_MD,
    # chip/Makefile 已移除，芯片级入口统一为 chip/top/Makefile
    "chip/top/de/rtl/{top_module}.v": CHIP_TOP_SV,
}


def create_ip_template(root: Path, ip_name: str, project_name: str, ip_type: str = "digital"):
    """在 ip/<type>/ 下创建可独立编译的 IP 模板"""
    ip_dir = root / "ip" / ip_type / ip_name
    for d in MODULE_DIRECTORIES:
        (ip_dir / d).mkdir(parents=True, exist_ok=True)

    fmt = {"ip_name": ip_name, "project_name": project_name}
    (ip_dir / "de" / "rtl" / f"{ip_name}.v").write_text(IP_RTL_V.format(**fmt), encoding="utf-8")
    (ip_dir / "de" / "rtl" / "filelist.f").write_text(
        f"$SOC/ip/{ip_type}/{ip_name}/de/rtl/{ip_name}.v\n", encoding="utf-8"
    )
    (ip_dir / "dv" / "tb" / f"tb_{ip_name}.sv").write_text(IP_TB_SV.format(**fmt), encoding="utf-8")
    (ip_dir / "de" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
    (ip_dir / "dv" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
    (ip_dir / "Makefile").write_text(_module_makefile(ip_name, 3), encoding="utf-8")
    (ip_dir / "README.md").write_text(IP_README_MD.format(**fmt), encoding="utf-8")
    fl_fmt = {"module_name": ip_name, "module_name_upper": ip_name.upper().replace("-", "_")}
    (ip_dir / "de" / "rtl" / "filelist.mk").write_text(FILELIST_MK.format(**fl_fmt), encoding="utf-8")
    (ip_dir / ".gitignore").write_text(
        "de/run/\ndv/sim/\ndv/cov/\n.pipeline_state.lock\n*.vcd\n*.vpd\n*.log\n",
        encoding="utf-8",
    )


def init_project(project_name, output_path, top_module=None):
    if top_module is None:
        top_module = f"{project_name}_top"

    root = Path(output_path) / project_name
    if root.exists():
        print(f"[ERROR] Directory already exists: {root}")
        return 1

    # Create directories
    for d in DIRECTORIES:
        (root / d).mkdir(parents=True, exist_ok=True)
    for sub in CHIP_SUBMODULES:
        for d in MODULE_DIRECTORIES:
            (root / "chip" / sub / d).mkdir(parents=True, exist_ok=True)

    # Write files
    fmt = {"project_name": project_name, "top_module": top_module}
    for rel_path, template in FILES.items():
        file_path = root / rel_path.format(**fmt)
        file_path.write_text(template.format(**fmt), encoding="utf-8")

    # Install the current shared build system after legacy embedded templates so
    # the versioned project template is authoritative.
    _install_project_templates(root, project_name)

    # Create chip sub-module files (Makefile, README, TB, filelist.mk)
    for sub in CHIP_SUBMODULES:
        module_name = top_module if sub == "top" else sub
        sub_fmt = {"module_name": module_name, "project_name": project_name}
        fl_fmt = {"module_name": module_name, "module_name_upper": module_name.upper().replace("-", "_")}
        (root / "chip" / sub / "Makefile").write_text(
            _module_makefile(module_name, 2, rtl_entry=sub == "top"), encoding="utf-8"
        )
        (root / "chip" / sub / "README.md").write_text(CHIP_SUB_README_MD.format(**sub_fmt), encoding="utf-8")
        (root / "chip" / sub / "dv" / "tb" / f"tb_{module_name}.sv").write_text(CHIP_SUB_TB_SV.format(**sub_fmt), encoding="utf-8")
        (root / "chip" / sub / "de" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
        (root / "chip" / sub / "dv" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
        rtl_file = root / "chip" / sub / "de" / "rtl" / f"{module_name}.v"
        if sub != "top":
            rtl_file.write_text(CHIP_SUB_RTL_V.format(**sub_fmt), encoding="utf-8")
        (root / "chip" / sub / "de" / "rtl" / "filelist.f").write_text(
            f"$SOC/chip/{sub}/de/rtl/{module_name}.v\n", encoding="utf-8"
        )
        (root / "chip" / sub / "de" / "rtl" / "filelist.mk").write_text(FILELIST_MK.format(**fl_fmt), encoding="utf-8")

    # Create IP template
    create_ip_template(root, "template_ip", project_name, "digital")

    # Keep entrypoints executable after template rendering/copying.
    for entrypoint in ("setup", "setup.sh", "setup.csh"):
        (root / "scripts" / entrypoint).chmod(0o755)

    print(f"[OK] SoC project '{project_name}' initialized at: {root.absolute()}")
    print(f"[INFO] Top module default: {top_module}")
    print(f"[INFO] IP template created: ip/digital/template_ip (support standalone simulation)")
    return 0


def add_ip(ip_name, project_path, ip_type="digital"):
    root = Path(project_path).resolve()
    if not root.exists():
        print(f"[ERROR] Project not found: {root}")
        return 1

    if not (root / "scripts/common.mk").exists():
        print(f"[ERROR] Not a valid SoC project (missing scripts/common.mk): {root}")
        return 1

    ip_dir = root / "ip" / ip_type / ip_name
    if ip_dir.exists():
        print(f"[ERROR] IP already exists: {ip_dir}")
        return 1

    project_name = root.name
    create_ip_template(root, ip_name, project_name, ip_type)

    print(f"[OK] IP '{ip_name}' added to {root}/ip/{ip_type}/{ip_name}")
    print(f"[INFO] Run 'cd ip/{ip_type}/{ip_name} && make comp' to simulate independently")
    return 0


def add_chip_module(module_name, project_path):
    root = Path(project_path).resolve()
    if not root.exists():
        print(f"[ERROR] Project not found: {root}")
        return 1

    if not (root / "scripts/common.mk").exists():
        print(f"[ERROR] Not a valid SoC project (missing scripts/common.mk): {root}")
        return 1

    module_dir = root / "chip" / module_name
    if module_dir.exists():
        print(f"[ERROR] Chip module already exists: {module_dir}")
        return 1

    project_name = root.name

    # 创建目录
    for d in MODULE_DIRECTORIES:
        (module_dir / d).mkdir(parents=True, exist_ok=True)

    # 写入 Makefile、README、Testbench 和子目录 wrapper Makefile
    fmt = {"module_name": module_name, "project_name": project_name}
    (module_dir / "Makefile").write_text(_module_makefile(module_name, 2), encoding="utf-8")
    (module_dir / "README.md").write_text(CHIP_SUB_README_MD.format(**fmt), encoding="utf-8")
    (module_dir / "dv" / "tb" / f"tb_{module_name}.sv").write_text(CHIP_SUB_TB_SV.format(**fmt), encoding="utf-8")
    (module_dir / "de" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
    (module_dir / "dv" / "Makefile").write_text(SUBDIR_MAKEFILE, encoding="utf-8")
    (module_dir / "de" / "rtl" / f"{module_name}.v").write_text(
        CHIP_SUB_RTL_V.format(**fmt), encoding="utf-8"
    )
    (module_dir / "de" / "rtl" / "filelist.f").write_text(
        f"$SOC/chip/{module_name}/de/rtl/{module_name}.v\n", encoding="utf-8"
    )

    fl_fmt = {"module_name": module_name, "module_name_upper": module_name.upper().replace("-", "_")}
    (module_dir / "de" / "rtl" / "filelist.mk").write_text(FILELIST_MK.format(**fl_fmt), encoding="utf-8")

    print(f"[OK] Chip module '{module_name}' added to {root}/chip/{module_name}")
    print(f"[INFO] Run 'cd chip/{module_name} && make comp' to simulate")
    return 0


def main():
    parser = argparse.ArgumentParser(description="SoC Project Directory Init / Add IP / Add Chip Module")
    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init', help='初始化 SoC 项目目录结构')
    init_parser.add_argument("project_name", help="项目名称")
    init_parser.add_argument("-o", "--output", default=".", help="输出父目录 (默认: 当前目录)")
    init_parser.add_argument("-t", "--top", help="顶层模块名 (默认: <project_name>_top)")

    addip_parser = subparsers.add_parser('add_ip', help='在项目中新增 IP (digital / third_party)')
    addip_parser.add_argument("ip_name", help="IP 模块名")
    addip_parser.add_argument("-p", "--project", default=".", help="SoC 项目根目录")
    addip_parser.add_argument("-t", "--type", default="digital", choices=["digital", "third_party"],
                              help="IP 类型: digital(自研, 默认) 或 third_party(第三方)")

    addchip_parser = subparsers.add_parser('add_chip', help='在 chip/ 下新增子模块')
    addchip_parser.add_argument("module_name", help="子模块名 (如: crypto, dma)")
    addchip_parser.add_argument("-p", "--project", default=".", help="SoC 项目根目录")

    args = parser.parse_args()

    if args.command == 'add_ip':
        return add_ip(args.ip_name, args.project, args.type)
    elif args.command == 'add_chip':
        return add_chip_module(args.module_name, args.project)
    else:
        # 兼容旧用法：直接传 project_name 作为 init
        if args.command == 'init' or args.command is None:
            if hasattr(args, 'project_name'):
                return init_project(args.project_name, args.output, args.top)
            parser.print_help()
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
