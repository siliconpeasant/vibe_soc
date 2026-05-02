# vibe_soc SoC Top-Level Makefile

PROJECT_ROOT = $(shell pwd -P)
export PROJECT_ROOT

.PHONY: help setup lint clean

help:
	@echo "vibe_soc SoC Build System"
	@echo "==========================="
	@echo "  make setup   - 初始化开发环境"
	@echo "  make lint    - 代码静态检查"
	@echo "  make clean   - 清理所有生成文件"
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
