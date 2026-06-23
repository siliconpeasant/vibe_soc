# vibe_soc unified build entry.

PROJECT_ROOT := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))
MODULE       ?= chip/top
MODULE_DIR   := $(PROJECT_ROOT)/$(MODULE)
TARGET       ?= help

export PROJECT_ROOT

include $(PROJECT_ROOT)/scripts/config.mk

.DEFAULT_GOAL := help

.PHONY: help setup check-env check-repo list-modules print-config module \
        flist validate-flist comp sim run test regress report coverage \
        coverage-regress coverage-report wave verdi debug-gui lint syn \
        clean debugclean deepclean

help:
	@echo "vibe_soc SoC Build System"
	@echo "=========================="
	@echo "  make list-modules                 列出可构建模块"
	@echo "  make check-env                    检查本机工具链"
	@echo "  make check-repo                   检查隐私路径和 license 泄漏"
	@echo "  make <target> [MODULE=<path>]     构建指定模块（默认 chip/top）"
	@echo "  make module MODULE=<path> TARGET=<target>"
	@echo ""
	@echo "Targets: flist validate-flist comp sim test regress report coverage"
	@echo "         coverage-regress wave verdi debug-gui lint syn"
	@echo "         clean debugclean deepclean print-config"
	@echo "Example: make lint MODULE=ip/digital/uart"
	@echo "         make comp MODULE=chip/top SIMULATOR=iverilog"

setup check-env:
	@bash $(PROJECT_ROOT)/scripts/setup.sh --check

check-repo:
	@$(PYTHON_RUN) $(PROJECT_ROOT)/scripts/check_repo_hygiene.py --root $(PROJECT_ROOT)

list-modules:
	@find $(PROJECT_ROOT)/chip $(PROJECT_ROOT)/ip -mindepth 2 -maxdepth 3 \
		-name Makefile ! -path '*/de/Makefile' ! -path '*/dv/Makefile' \
		-printf '%h\n' | sed 's|^$(PROJECT_ROOT)/||' | sort

print-config:
	@echo "PROJECT_ROOT=$(PROJECT_ROOT)"
	@echo "MODULE=$(MODULE)"
	@echo "SIMULATOR=$(or $(SIMULATOR),vcs)"
	@echo "LINT_TOOL=$(or $(LINT_TOOL),verilator)"

module:
	@test -f "$(MODULE_DIR)/Makefile" || { \
		echo "[ERROR] Invalid MODULE '$(MODULE)': module Makefile not found"; exit 2; \
	}
	@$(MAKE) --no-print-directory -C "$(MODULE_DIR)" "$(TARGET)"

flist validate-flist comp sim run test regress report coverage \
coverage-regress coverage-report wave verdi debug-gui lint syn \
clean debugclean deepclean:
	@$(MAKE) --no-print-directory module TARGET=$@
