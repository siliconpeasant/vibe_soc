#!/bin/bash
# vibe_soc SoC 开发环境初始化脚本
# 兼容 bash/zsh/dash 等 POSIX shell

set -e

# ---------------------------------------------------------------------------
# 1. 推断 PROJECT_ROOT
# ---------------------------------------------------------------------------
if [ -n "${BASH_SOURCE[0]}" ]; then
    _script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
else
    _script_dir=$(cd "$(dirname "$0")" && pwd -P)
fi
PROJECT_ROOT=$(dirname "$_script_dir")

# 验证：PROJECT_ROOT 下必须有 chip/ 和 ip/ 目录
if [ ! -d "$PROJECT_ROOT/chip" ] || [ ! -d "$PROJECT_ROOT/ip" ]; then
    echo "[ERROR] 无法定位 vibe_soc 项目根目录"
    echo "        请从项目根目录或 scripts/ 目录下 source 本脚本"
    echo "        当前推断路径: $PROJECT_ROOT"
    exit 1
fi

export PROJECT_ROOT
export SOC="$PROJECT_ROOT"
export CHIP_PATH="$PROJECT_ROOT/chip"
export IP_PATH="$PROJECT_ROOT/ip"

# ---------------------------------------------------------------------------
# 2. 工具链检测
# ---------------------------------------------------------------------------
_check_tool() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "  ✓ $1"
        return 0
    else
        echo "  ✗ $1 (未安装)"
        return 1
    fi
}

echo ""
echo "[CHECK] 检测工具链 ..."
MISSING=0
_check_tool make   || MISSING=$((MISSING + 1))
_check_tool verilator || true
_check_tool iverilog  || true
_check_tool vvp       || true
_check_tool yosys     || true

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "[WARN] 检测到 $MISSING 个必需工具缺失"
    echo "       请先安装缺失工具再运行 make lint/sim/syn"
fi

# ---------------------------------------------------------------------------
# 3. 设置默认仿真器
# ---------------------------------------------------------------------------
export SIMULATOR=${SIMULATOR:-iverilog}

# ---------------------------------------------------------------------------
# 4. 输出
# ---------------------------------------------------------------------------
echo ""
echo "======================================"
echo " vibe_soc SoC 开发环境已初始化"
echo "======================================"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CHIP_PATH    : $CHIP_PATH"
echo "SIMULATOR    : $SIMULATOR"
echo "======================================"
echo ""
echo "可用命令:"
echo "  make lint   RTL_TOP=<模块>    # Lint 检查"
echo "  make comp   TOP_MODULE=<tb>   # 编译仿真"
echo "  make sim    TOP_MODULE=<tb>   # 运行仿真"
echo "  make syn    RTL_TOP=<模块>    # 逻辑综合"
echo "======================================"
