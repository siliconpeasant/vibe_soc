#!/bin/bash
# vibe_soc SoC 开发环境初始化脚本

export PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
export SOC="$PROJECT_ROOT"
export CHIP_PATH="$PROJECT_ROOT/chip"
export IP_PATH="$PROJECT_ROOT/ip"

# 工具链检测
export SIMULATOR=${SIMULATOR:-"iverilog"}   # 可选: vcs, verilator, iverilog, xcelium

echo "======================================"
echo " vibe_soc SoC 开发环境已初始化"
echo "======================================"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CHIP_PATH    : $CHIP_PATH"
echo "SIMULATOR    : $SIMULATOR"
echo "======================================"
