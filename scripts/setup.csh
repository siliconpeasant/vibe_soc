#!/bin/csh
# vibe_soc SoC 开发环境初始化脚本 (csh 版本)
# 加固版：路径验证 + 工具链检测 + 向上查找 fallback

set _ok = 0
set _script_dir = ""

# ---------------------------------------------------------------------------
# 1. 优先从当前目录向上查找包含 chip/ + ip/ 的项目根目录。
#    source scripts/setup.csh 时 csh 的 $0 通常是 shell 名，不是脚本路径。
# ---------------------------------------------------------------------------
set _cwd = `pwd -P`
set _candidate = "$_cwd"
while ("$_candidate" != "/" && "$_candidate" != "")
    if (-d "$_candidate/chip" && -d "$_candidate/ip" && -d "$_candidate/scripts") then
        set _script_dir = "$_candidate/scripts"
        set _ok = 1
        break
    endif
    set _candidate = `dirname "$_candidate"`
end

# ---------------------------------------------------------------------------
# 2. Fallback：脚本被 csh scripts/setup.csh 直接执行时，$0 可能可用。
# ---------------------------------------------------------------------------
if ($_ok == 0 && $?0) then
    if ("$0" =~ /*) then
        set _script_dir = `dirname "$0"`
    else if (-e "$0") then
        set _script_dir = `dirname "$0"`
    endif
    if ("$_script_dir" != "") then
        set _candidate = `\cd "$_script_dir/.." >& /dev/null && pwd -P`
        if (-d "$_candidate/chip" && -d "$_candidate/ip") then
            set _script_dir = "$_candidate/scripts"
            set _ok = 1
        endif
    endif
endif

# ---------------------------------------------------------------------------
# 4. 仍然找不到 → 报错退出
# ---------------------------------------------------------------------------
if ($_ok == 0) then
    echo "[ERROR] 无法定位 vibe_soc 项目根目录"
    echo "        请 cd 到项目根目录或任意子目录后重新 source"
    exit 1
endif

setenv PROJECT_ROOT `dirname "$_script_dir"`
setenv SOC "$PROJECT_ROOT"
setenv CHIP_PATH "$PROJECT_ROOT/chip"
setenv IP_PATH "$PROJECT_ROOT/ip"

if (-f "$PROJECT_ROOT/scripts/local.csh") then
    source "$PROJECT_ROOT/scripts/local.csh"
endif

if ($?VCS_HOME) then
    if (-d "$VCS_HOME/bin") set path = ("$VCS_HOME/bin" $path)
endif
if ($?VERDI_HOME) then
    if (-d "$VERDI_HOME/bin") set path = ("$VERDI_HOME/bin" $path)
endif
if ($?XCELIUM_HOME) then
    if (-d "$XCELIUM_HOME/tools.lnx86/bin") set path = ("$XCELIUM_HOME/tools.lnx86/bin" $path)
endif

# ---------------------------------------------------------------------------
# 5. 工具链检测
# ---------------------------------------------------------------------------
if (! $?SIMULATOR) setenv SIMULATOR "vcs"
if (! $?LINT_TOOL) setenv LINT_TOOL "verilator"
if (! $?SPYGLASS_HOME) setenv SPYGLASS_HOME "/usr/Synopsys/spyglass/latest"
if (! $?SG_HOME) setenv SG_HOME "$SPYGLASS_HOME"
if (! $?SG_SHELL) setenv SG_SHELL "$SG_HOME/bin/sg_shell"

echo ""
echo "[CHECK] 检测工具链 ..."
set _missing = 0

foreach _tool (make verilator iverilog vvp yosys vcs verdi xrun)
    (which $_tool) >& /dev/null
    if ($status == 0) then
        echo "  ✓ $_tool"
    else
        echo "  - $_tool (当前环境不可用)"
        if ("$_tool" == "make") @_missing++
        if ("$_tool" == "verilator" && "$LINT_TOOL" == "verilator") @_missing++
        if ("$_tool" == "iverilog" && "$SIMULATOR" == "iverilog") @_missing++
        if ("$_tool" == "vvp" && "$SIMULATOR" == "iverilog") @_missing++
        if ("$_tool" == "vcs" && "$SIMULATOR" == "vcs") @_missing++
        if ("$_tool" == "xrun" && "$SIMULATOR" == "xcelium") @_missing++
    endif
end

if (-x "$SG_SHELL") then
    echo "  ✓ $SG_SHELL"
else
    echo "  - $SG_SHELL (当前环境不可用)"
    if ("$LINT_TOOL" == "spyglass") @_missing++
endif

if ($_missing > 0) then
    echo ""
    echo "[WARN] 检测到 $_missing 个工具缺失"
    echo "       请先安装缺失工具再运行 make lint/sim/syn"
endif

# ---------------------------------------------------------------------------
# 6. 设置默认仿真器
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 7. 输出
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
echo "  make comp   TOP_MODULE=<tb>   # HDL 编译 + elaboration"
echo "  make sim    TOP_MODULE=<tb>   # 运行仿真"
echo "  make syn    RTL_TOP=<模块>    # 逻辑综合"
echo "======================================"

unset _ok _script_dir _candidate _cwd _missing _tool
