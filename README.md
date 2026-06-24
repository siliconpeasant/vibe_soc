# vibe_soc

`vibe_soc` 是一个 silicon-crew 风格的 SoC 前端开发仓库，覆盖模块/IP 创建、RTL 集成、lint/编译/仿真/回归/覆盖率、综合、OpenROAD 物理设计 handoff、寄存器生成、CRG 需求设计和时钟/复位树图生成。

当前仓库采用统一模块布局和门控流程：`doc -> rtl -> {verif, syn}`。EDA 执行由注册的 MCP 工具驱动，避免在 agent 阶段绕过项目 Make/MCP 约束直接调用仿真器、综合器或 OpenROAD。

## 仓库布局

```text
vibe_soc/
├── chip/                         # 芯片级模块
│   ├── core/                     # core 示例模块
│   ├── bus/                      # bus 示例模块
│   ├── periph/                   # 外设汇聚模块
│   ├── interconnect/             # 互联模块
│   ├── lib/                      # 通用库模块
│   └── top/                      # SoC 顶层，含集成配置和 pipeline_state.json
├── ip/
│   ├── digital/                  # 自研数字 IP，例如 uart/spi/soc_ip_common
│   └── third_party/              # 第三方 IP 封装，例如 pcie
├── pd/openroad/                  # 设计自有 OpenROAD handoff 配置
│   └── nangate45/<design>/       # config.mk、constraint.sdc、README 等
├── scripts/                      # 项目 Make 公共规则、工具链配置和检查脚本
├── .agents/                      # silicon-crew agents、rules、MCP skills 和状态脚本
├── .codex/                       # Codex agent/MCP 配置
├── Makefile                      # 顶层统一构建入口
└── README.md
```

每个 chip module 或 IP 使用统一结构：

```text
<module>/
├── docs/                         # 设计文档、接口说明、regmap、验证计划
├── de/rtl/                       # RTL、filelist.f、filelist.mk
├── de/run/                       # lint/build 临时 filelist 和日志，Git 忽略
├── de/syn/                       # SDC、综合脚本、网表、综合/STA 报告
├── dv/tb/                        # testbench
├── dv/tests/                     # 回归测试列表
├── dv/sim/                       # 编译/仿真日志、波形和缓存，Git 忽略
├── dv/cov/                       # 覆盖率数据库和报告，Git 忽略
├── pipeline_state.json           # 门控流程状态，可选
└── Makefile
```

不要新建旧式根目录 `rtl/`、`tb/`、`sim/`、`syn/`、`constraints/` 作为兼容层。

## 快速开始

```bash
# 检查工具链环境
source scripts/setup.sh
make check-env

# 查看可构建模块
make list-modules

# 查看当前配置
make print-config MODULE=ip/digital/uart SIMULATOR=vcs

# 提交前检查本机路径、license endpoint 等泄漏风险
make check-repo
```

所有顶层 Make 目标都可以通过 `MODULE=<path>` 指定模块，默认模块是 `chip/top`。

```bash
make lint MODULE=ip/digital/uart
make comp MODULE=chip/top SIMULATOR=iverilog
make sim  MODULE=ip/digital/uart SIMULATOR=vcs TEST=uart_all SEED=7
```

## Make 目标

| 目标 | 作用 |
|---|---|
| `list-modules` | 列出带模块 Makefile 的 chip/IP 模块 |
| `check-env` | 检查本机 EDA/Python 环境 |
| `check-repo` | 检查不应入库的本机路径和 license 信息 |
| `flist` | 生成/刷新模块 filelist |
| `validate-flist` | 展平并检查嵌套 filelist、循环和失效路径 |
| `lint` | RTL lint，默认 Verilator，可切换工具 |
| `comp` | 编译/elaboration |
| `sim` / `run` / `test` | 单次仿真，支持 TEST/SEED |
| `regress` | 多测试、多 seed 回归 |
| `report` | 汇总回归结果 |
| `coverage` | 单次覆盖率采集 |
| `coverage-regress` | 回归覆盖率采集 |
| `coverage-report` | 覆盖率报告生成 |
| `wave` | 打开波形 |
| `verdi` / `debug-gui` | Verdi/调试 GUI 入口 |
| `syn` | Yosys 综合入口 |
| `clean` | 清理运行日志/波形，保留编译缓存 |
| `debugclean` | 进一步清理调试和报告文件 |
| `deepclean` | 清理瞬态编译/仿真产物，保留综合交付物 |

示例：

```bash
make validate-flist MODULE=chip/top
make comp MODULE=ip/digital/uart SIMULATOR=vcs
make comp MODULE=ip/digital/uart SIMULATOR=vcs FORCE=1
make regress MODULE=ip/digital/uart REGRESS_SEEDS=1-10 REGRESS_JOBS=4
make coverage MODULE=ip/digital/uart TEST=uart_all SEED=7
```

## 工具链

仿真/调试支持：

- VCS
- Verilator
- Iverilog
- Xcelium
- Verdi、DVE、SimVision、GTKWave

本地工具路径、license endpoint 和默认参数写入本地文件：

```bash
cp scripts/local.mk.example scripts/local.mk
```

`scripts/local.mk`、`scripts/local.sh`、`scripts/local.csh` 已被 Git 忽略。不要强制加入这些文件。需要 DesignWare 仿真模型时，在 `scripts/local.mk` 配置：

```make
VCS_DW_SIM_PATH := /path/to/dw/sim_ver
```

## 门控开发流程

RTL 创建或实质修改遵循：

```text
architecture handoff，可选 -> doc -> rtl -> {verif, syn}
```

| 阶段 | 角色 | 典型产物 |
|---|---|---|
| architecture | `soc-architect` | `docs/architecture*.md` |
| doc | `soc-doc-engineer` | `docs/design_spec.md`、`interface_spec.md`、`regmap.md`、`verification_plan.md` |
| rtl | `soc-rtl-designer` 或特化角色 | `de/rtl/*.v`、`de/rtl/filelist.f`、`de/syn/*.sdc` |
| verif | `soc-verification-engineer` | `dv/tb/tb_<module>.*`、`dv/sim/sim.log` |
| syn | `soc-synthesis-engineer` | `de/syn/*_netlist.v`、`de/syn/synth.log` |

每个独立模块/IP 可用 `pipeline_state.json` 跟踪阶段状态。常用状态脚本：

```bash
python3 .agents/scripts/init_state.py <workspace> <module>
python3 .agents/scripts/query_state.py <workspace>
python3 .agents/scripts/update_state.py <workspace> rtl in_progress
```

状态规则要点：

- `done` 必须有真实、非空 artifact 和至少一个 passing check。
- `verif` 和 `syn` 在 RTL 完成后可以并行，但结果只对当时消费的 RTL snapshot 有效。
- 验证阶段可在 `verif in_progress` 内多次修 RTL，只在阶段完成/失败时结算一次；若 RTL 变更，`syn` 必须退回 `pending` 并重跑。
- 综合阶段同理；若综合修 RTL，`verif` 必须退回 `pending` 并重跑。
- 同一个 RTL epoch 只允许一个下游阶段承担 RTL 修复。若另一侧也需要改 RTL，重新打开 `rtl in_progress`，旧 `verif/syn` 结果会自动失效。

## MCP/Agent 功能

仓库内置 `.agents/` 和 `.codex/` 配置，用于 silicon-crew 自动化。主要能力如下：

| 能力 | MCP/Skill | 说明 |
|---|---|---|
| 项目/IP/模块脚手架 | `soc-build` | `soc_init`、`soc_add_chip`、`soc_add_ip` |
| 构建与验证 | `soc-build` | filelist、lint、compile、sim、regress、coverage、syn |
| 顶层集成 | `soc-integrate` | 端口提取、实例化、wrapper、top 生成、快照、diff、刷新 |
| OpenROAD handoff | `soc-openroad` | 生成 ORFS config/SDC，运行 synth/floorplan/place/cts/route/finish/all，汇总结果 |
| 寄存器 YAML 生成 RTL | `yml2reg` | 从 YAML 生成 APB/AHB regfile RTL |
| Excel 寄存器生成 | `excel-yml-gen` | 从 Excel 生成 YAML、regfile RTL、wrapper 等 |
| CRG 需求转设计表 | `crg-req-to-design` | 从 CRG 需求表生成 clock/reset 设计表和 PLL 建议 |
| 时钟/复位树图 | `cr-tree-diag-gen` | 从设计表生成 Draw.io 和 Excalidraw 图 |
| 流程编排 | `soc-pipeline` | 协调架构、doc、RTL、验证、综合、PD handoff |

EDA 阶段必须走注册 MCP 工具：验证调用 `soc-build.soc_sim`，综合调用 `soc-build.soc_syn`，OpenROAD 调用 `soc-openroad.soc_openroad_*`。阶段 agent 不使用直接 `make`、`iverilog`、`vvp`、`yosys`、`openroad` 等 shell fallback。

## 顶层集成

顶层位于 `chip/top`。自动集成产物包括：

```text
chip/top/de/rtl/vibe_soc_top.v
chip/top/de/rtl/vibe_soc_top.integrate.json
chip/top/de/rtl/vibe_soc_top.integrate.csv
```

集成应通过 `soc-integrate` 工具生成和刷新，复杂连接使用显式 port map。不要手工改自动生成的实例连接；子模块端口变化后用配置刷新并重新检查。

## 仿真、回归与覆盖率

模块 testbench 放在 `dv/tb/`，回归清单放在 `dv/tests/tests.list`，格式为：

```text
test_name [optional plusargs]
```

常用命令：

```bash
make test MODULE=ip/digital/uart TEST=uart_all SEED=7
make regress MODULE=ip/digital/uart REGRESS_SEEDS=1-10 REGRESS_JOBS=4
make report MODULE=ip/digital/uart
make coverage-regress MODULE=ip/digital/uart REGRESS_SEEDS=1-10 REGRESS_JOBS=4
```

回归摘要写入模块 `dv/sim/regress/summary.txt` 和 `summary.json`。覆盖率默认指标为 `line+branch+cond+tgl+fsm+assert`，报告位于 `dv/cov/report/`。

## 综合与 STA

综合通过项目 Make 或 `soc-build.soc_syn` 运行：

```bash
make syn MODULE=ip/digital/uart RTL_TOP=uart
```

综合产物位于 `de/syn/`，包括 `*_netlist.v`、`synth.log`、`rtl.f`、`syn.ys`、SDC 和可选 STA 报告。Yosys 结构综合结果不等于时序收敛；只有真实 STA 报告可以声明 WNS/TNS 或 timing closure。

## OpenROAD handoff

项目自有 OpenROAD 配置放在：

```text
pd/openroad/<platform>/<design>/config.mk
pd/openroad/<platform>/<design>/constraint.sdc
```

当前已有：

- `pd/openroad/nangate45/vibe_soc_top/`
- `pd/openroad/nangate45/uart/`

默认 MCP flow 使用 local ORFS，输出目录为 `pd/openroad/work_local/`。容器后端显式使用 `backend=auto|docker|podman`，输出目录通常为 `pd/openroad/work/`。

重要约束：

- OpenROAD-flow-scripts/OpenROAD 源码树不放进本仓库。
- `pd/openroad/local/`、`pd/openroad/work/`、`pd/openroad/work_local*/` 和 `config.local.mk` 属于本机环境或运行产物，Git 忽略。
- `soc_openroad_init` 需要模块 `de/run/rtl.f` 作为 PD RTL 输入来源；缺失时停止，不 fallback 到 `de/rtl/filelist.f`。

## 寄存器与 CRG 辅助生成

寄存器：

- 已批准 YAML 源：使用 `yml2reg` 生成 APB/AHB regfile RTL。
- 已批准 Excel 源：使用 `excel-yml-gen` 生成 YAML、regfile RTL、instance wrapper 和 TDR buffer list。
- 不手工修改生成 RTL；修改源 YAML/Excel 后重新生成。

CRG：

- 需求表到设计表：使用 `crg-req-to-design` 生成 `clock_design.xlsx`、`reset_design.xlsx`、`crg_report.txt`。
- 设计表到图：使用 `cr-tree-diag-gen` 生成 Draw.io/Excalidraw 拓扑图。
- 当前 `crg-gen` 未注册，不安排 CRG RTL 自动生成。

## 仓库卫生

`.gitignore` 已覆盖常见本地产物：

- `**/run/`、`**/sim/`、`**/cov/`
- `*.log`、`*.out`、`*.vcd`、`*.vpd`
- VCS/Verdi/仿真缓存目录
- `scripts/local.mk`、`scripts/local.sh`、`scripts/local.csh`
- `pd/openroad/work/`、`pd/openroad/work_local*/`、`pd/openroad/local/`、`pd/openroad/**/config.local.mk`

提交前建议执行：

```bash
make check-repo
git diff --check
git status --short
```

不要提交真实 license server、本机绝对工具路径、大型仿真/PD 运行产物或未审查的生成缓存。
