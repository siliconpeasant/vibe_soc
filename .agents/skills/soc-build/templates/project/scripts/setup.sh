#!/bin/bash
# vibe_soc SoC 开发环境初始化脚本
# 兼容 bash/zsh/dash 等 POSIX shell

set -e

CHECK_ONLY=0
if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=1
fi

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

# Optional site/user environment (tool homes, license servers, module commands).
if [ -f "$PROJECT_ROOT/scripts/local.sh" ]; then
    . "$PROJECT_ROOT/scripts/local.sh"
fi

_prepend_path() {
    [ -d "$1" ] || return 0
    case ":$PATH:" in
        *":$1:"*) ;;
        *) PATH="$1:$PATH" ;;
    esac
}

_prepend_path "${VCS_HOME:-}/bin"
_prepend_path "${VERDI_HOME:-}/bin"
_prepend_path "${XCELIUM_HOME:-}/tools.lnx86/bin"
export PATH

export PROJECT_ROOT
export SOC="$PROJECT_ROOT"
export CHIP_PATH="$PROJECT_ROOT/chip"
export IP_PATH="$PROJECT_ROOT/ip"
export SIMULATOR=${SIMULATOR:-vcs}
export LINT_TOOL=${LINT_TOOL:-verilator}

# ---------------------------------------------------------------------------
# 2. 工具链检测
# ---------------------------------------------------------------------------
_check_tool() {
    _tool=$1
    shift
    if command -v "$_tool" >/dev/null 2>&1 && "$_tool" "$@" >/dev/null 2>&1; then
        echo "  ✓ $_tool"
        return 0
    else
        echo "  ✗ $_tool (未安装或运行异常)"
        return 1
    fi
}

_check_iverilog() {
    if command -v iverilog >/dev/null 2>&1 && \
       printf 'module toolcheck; endmodule\n' | iverilog -tnull - >/dev/null 2>&1; then
        echo "  ✓ iverilog"
        return 0
    fi
    echo "  ✗ iverilog (前端存在，但编译后端缺失或运行异常)"
    return 1
}

_check_presence() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "  ✓ $1"
        return 0
    fi
    echo "  - $1 (当前环境不可用)"
    return 1
}

echo ""
echo "[CHECK] 检测工具链 ..."
MISSING=0
_check_tool make --version || MISSING=$((MISSING + 1))
_check_tool verilator --version || {
    [ "$LINT_TOOL" != "verilator" ] || MISSING=$((MISSING + 1))
}
_check_iverilog || {
    [ "$SIMULATOR" != "iverilog" ] || MISSING=$((MISSING + 1))
}
_check_tool vvp -V || {
    [ "$SIMULATOR" != "iverilog" ] || MISSING=$((MISSING + 1))
}
_check_tool yosys -V || true
_check_tool vcs -ID || {
    [ "$SIMULATOR" != "vcs" ] || MISSING=$((MISSING + 1))
}
_check_presence verdi || true
_check_tool xrun -version || {
    [ "$SIMULATOR" != "xcelium" ] || MISSING=$((MISSING + 1))
}

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "[WARN] 检测到 $MISSING 个必需工具缺失"
    echo "       请先安装缺失工具再运行 make lint/sim/syn"
fi

# ---------------------------------------------------------------------------
# 3. 输出
# ---------------------------------------------------------------------------
echo ""
echo "======================================"
echo " vibe_soc SoC 开发环境已初始化"
echo "======================================"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CHIP_PATH    : $CHIP_PATH"
echo "SIMULATOR    : $SIMULATOR"
echo "VCS_HOME     : ${VCS_HOME:-<unset>}"
echo "VERDI_HOME   : ${VERDI_HOME:-<unset>}"
echo "XCELIUM_HOME : ${XCELIUM_HOME:-<unset>}"
echo "======================================"
echo ""
echo "可用命令:"
echo "  make lint   RTL_TOP=<模块>    # Lint 检查"
echo "  make comp   TOP_MODULE=<tb>   # HDL 编译 + elaboration"
echo "  make sim    TOP_MODULE=<tb>   # 运行仿真"
echo "  make syn    RTL_TOP=<模块>    # 逻辑综合"
echo "  make verdi  MODULE=<模块>     # Verdi 源码浏览"
echo "  make debug-gui SIMULATOR=vcs # Verdi KDB 调试"
echo "======================================"

if [ "$CHECK_ONLY" -eq 1 ]; then
    exit "$MISSING"
fi
