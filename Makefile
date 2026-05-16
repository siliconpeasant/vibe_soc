# vibe_soc SoC Top-Level Makefile

PROJECT_ROOT = $(shell pwd -P)
export PROJECT_ROOT

.PHONY: help setup lint clean

help:
	@echo "vibe_soc SoC Build System"
	@echo "==========================="
	@echo "  make setup   - 初始化开发环境"
	@echo "  make lint    - 代码静态检查"
	@echo "  make syn     - Yosys 综合（模块级）"
	@echo "  make clean   - 清理所有生成文件"
	@echo ""
	@echo "模块级命令 (cd chip/xxx 或 ip/xxx):"
	@echo "  make flist   - 生成 RTL 文件列表"
	@echo "  make comp    - 编译仿真"
	@echo "  make run     - 运行仿真"
	@echo "  make lint    - Lint 检查"
	@echo "  make syn     - Yosys 综合"
	@echo ""
	@echo "环境变量:"
	@echo "  SIMULATOR=vcs|verilator|iverilog|xcelium"

setup:
	@echo "[SETUP] Sourcing environment ..."
	@bash scripts/setup.sh

lint:
	@echo "[LINT] Running static check ..."
	@verilator --lint-only -Ichip $(shell find chip -name "*.v" -o -name "*.sv")

clean:
	@echo "[CLEAN] Cleaning generated files ..."
	@find . -type d -name run -o -type d -name sim | xargs rm -rf
