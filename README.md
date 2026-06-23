# vibe_soc SoC 前端开发项目

## 目录结构

```
vibe_soc/
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
│           ├── rtl/
│           ├── tb/
│           └── Makefile
├── scripts/              # 项目级公共脚本
│   ├── setup.sh          # 环境初始化
│   ├── paths.mk          # 集中路径定义
│   ├── config.mk         # 工具链与项目默认配置
│   ├── common.mk         # 公共仿真编译规则
│   ├── toolchains/       # 每种 EDA 工具的独立配置
│   ├── validate_filelist.py
│   ├── build_fingerprint.py
│   └── run_regression.py
├── doc/                  # 文档
│   ├── arch/             # 架构设计文档
│   └── spec/             # 接口规范与需求
└── Makefile              # 顶层构建入口
```

## 快速开始

### 1. 环境初始化
```bash
source scripts/setup.sh
# 或只检查工具，不修改当前 shell
make check-env

# 提交前检查个人绝对路径和 license endpoint
make check-repo
```

### 2. IP 独立仿真
```bash
cd ip/digital/template_ip
make comp    # 编译 IP 级 testbench
make lint    # lint 检查

# 也可始终从项目根目录执行
make lint MODULE=ip/digital/uart
make comp MODULE=chip/top SIMULATOR=iverilog
```

### 3. Chip 级仿真
```bash
cd chip/core && make comp && make lint
cd chip/top  && make comp && make lint
```

## 工具链支持

- **仿真**: VCS、Verilator、Iverilog、Xcelium
- **波形/调试**: Verdi、DVE、SimVision、GTKWave

商业 EDA 使用方式：

```bash
# VCS 编译（包含 elaboration）、运行和 Verdi KDB 调试
make comp MODULE=ip/digital/uart SIMULATOR=vcs
make sim  MODULE=ip/digital/uart SIMULATOR=vcs SEED=100
make debug-gui MODULE=ip/digital/uart SIMULATOR=vcs

# 启用 FSDB（testbench 需包含相应 $fsdbDump* 调用）
make comp MODULE=ip/digital/uart SIMULATOR=vcs FSDB=1
make wave MODULE=ip/digital/uart SIMULATOR=vcs FSDB=1

# Xcelium 编译（包含 elaboration）和运行
make comp MODULE=ip/digital/uart SIMULATOR=xcelium
make sim  MODULE=ip/digital/uart SIMULATOR=xcelium GUI=1

# 不依赖编译结果，直接用 Verdi 浏览源码
make verdi MODULE=ip/digital/uart SIMULATOR=vcs
```

## 增量构建与 Filelist

```bash
# 展平嵌套 -f、检查循环/失效路径，并对重复源文件去重
make validate-flist MODULE=chip/top

# RTL、filelist 和编译参数均未变化时直接复用已编译映像
make comp MODULE=ip/digital/uart SIMULATOR=vcs

# 强制重新编译
make comp MODULE=ip/digital/uart SIMULATOR=vcs FORCE=1
```

每个模块使用独立的 VCS worklib 和 `synopsys_sim.setup`，构建指纹保存在模块的 `dv/sim/.build.fingerprint`。

## 测试与回归

测试清单放在模块的 `dv/tests/tests.list`，格式为 `test_name [optional plusargs]`。

```bash
# 单测试/单 seed
make test MODULE=ip/digital/uart TEST=uart_all SEED=7

# 多测试、多 seed 并行回归
make regress MODULE=ip/digital/uart \
  REGRESS_SEEDS=1-10 REGRESS_JOBS=4

make report MODULE=ip/digital/uart
```

结果写入 `dv/sim/regress/summary.txt` 和 `summary.json`，任一用例失败时 Make 返回非零。

## 覆盖率

```bash
# 单次 VCS 覆盖率及 URG HTML 报告
make coverage MODULE=ip/digital/uart TEST=uart_all SEED=7

# 回归覆盖率
make coverage-regress MODULE=ip/digital/uart \
  REGRESS_SEEDS=1-10 REGRESS_JOBS=4
```

默认指标为 `line+branch+cond+tgl+fsm+assert`，HTML 报告位于模块的 `dv/cov/report/`。

## 清理级别

```bash
make clean MODULE=ip/digital/uart       # 仅运行日志/波形，保留编译缓存
make debugclean MODULE=ip/digital/uart  # 再清理调试和报告文件
make deepclean MODULE=ip/digital/uart   # 清理全部瞬态编译/仿真产物，保留综合交付物
```

工具安装路径和 license server 可写在 `scripts/local.sh`/`local.csh`；Make 参数覆盖写在 `scripts/local.mk`。这些本地文件已被 Git 忽略，不会提交到仓库。首次配置可执行：

```bash
cp scripts/local.mk.example scripts/local.mk
# 仅在 local.mk 中填写本机 license endpoint
git check-ignore scripts/local.mk
```

禁止使用 `git add -f scripts/local.mk`。仓库只提交不含真实地址的 `local.mk.example`。
默认模拟器与参考项目一致采用 VCS；当前机器需要可访问的 Synopsys license server 才能完成首次 elaboration。

如需 DesignWare 仿真模型，在 `scripts/local.mk` 中显式配置：

```make
VCS_DW_SIM_PATH := /path/to/dw/sim_ver
```

## 开发规范

- 所有 RTL 文件使用 `*.v` / `*.sv` 扩展名
- 模块名与文件名保持一致
- 每个 IP 独立目录，包含 RTL + 可独立编译的 testbench
- 顶层模块统一放在 `chip/top/`
- 所有子目录 Makefile 均引用 `scripts/common.mk`，确保编译环境一致
- 项目配置按 `paths.mk -> config.mk -> filelist.mk -> common rules` 顺序加载
- 本地工具路径或参数可写入不强制存在的 `scripts/local.mk`，也可在命令行覆盖
