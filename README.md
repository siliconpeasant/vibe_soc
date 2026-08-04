# vibe_soc

`vibe_soc` 是一个 silicon-crew 风格的 SoC 前端开发仓库，覆盖模块/IP 创建、RTL 集成、lint/编译/仿真/回归/覆盖率、综合、OpenROAD 物理设计 handoff、寄存器生成、CRG 需求设计和时钟/复位树图生成。

当前仓库采用分层 Loop：日常单模块修改走轻量 `dev` 内环，准备交付时走
`merge`，接口、时钟复位、约束、Top、跨模块和 PD 等高风险修改自动升级
为 `signoff`。最终门控依然是 `doc -> rtl -> {verif, syn}`。EDA 执行由
注册的 MCP 工具驱动，禁止 agent 直接调用仿真器、综合器或 OpenROAD。

## 仓库布局

```text
vibe_soc/
├── chip/                         # 芯片级模块
│   ├── core/                     # core 示例模块
│   ├── bus/                      # bus 示例模块
│   ├── periph/                   # 外设汇聚模块
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

## 当前模块索引

当前可通过 `make list-modules` 发现的模块分为四类：

| 类别 | 模块 |
|---|---|
| Chip shell | `chip/top`、`chip/core`、`chip/bus`、`chip/periph`、`chip/lib` |
| 原生/公共数字 IP | `ip/digital/uart`、`ip/digital/spi`、`ip/digital/soc_ip_common`、`ip/digital/lint_lab` |
| OpenTitan vendor-island IP | `ip/digital/<name>` 下的 AES、GPIO、I2C、KMAC、OTBN、ROM、RV、TL-UL、USB、XBAR 等 OpenTitan 源组织模块 |
| 第三方封装 | `ip/third_party/pcie` |

`uart_ot`、`spi_ot` 等带 `_ot` 后缀的模块保留 OpenTitan 侧源组织；`uart`、`spi` 等不带后缀的模块承载 vibe_soc 原生封装、验证和综合入口。

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
make comp MODULE=chip/top SIMULATOR=verilator
make sim  MODULE=ip/digital/uart SIMULATOR=vcs TEST=uart_all SEED=7
```

OpenTitan `chip/top` 仿真默认 `FSDB=0`，即不生成波形；需要 debug 波形时显式加 `FSDB=1`。

## CI/CD 与合并策略

当前 GitHub Actions 包含三类 workflow：

| Workflow | 触发方式 | 用途 |
|---|---|---|
| `auto-pr-automerge` | `codex/**`、`feature/**`、`fix/**` 分支 push、手动 | 自动创建/复用 PR，并尝试启用 GitHub 原生 auto-merge |
| `loop-policy` | PR、手动 | 校验 Loop 路由、状态工具、规则和 Agent 契约 |
| `top-smoke` | PR、手动、定时 | `chip/top` UART smoke CI 门禁 |
| `cd-release-branch` | `release/**` 分支 push、手动 | 发布分支候选包构建 |
| `cd-release` | `v*` tag、手动 | 正式 release 包和 GitHub Release |

推荐合并链路是：push 内部功能分支 -> GitHub App 自动创建/复用 PR -> PR CI 自动跑门禁 -> GitHub auto-merge 在 required checks 满足后合入默认分支。外部 Fork PR 不进入自动创建/自动合并路径，继续使用 GitHub 的人工批准门禁。

每个新任务必须从最新默认分支创建唯一 fresh branch。已经合并过 PR 的分支禁止复用，继续向旧分支 push 会被 `auto-pr-automerge` 主动拒绝：

```bash
# 当前 checkout 干净时
scripts/prepare_task_branch.sh <task-slug>

# 当前 checkout 有未完成工作时，直接创建隔离 worktree
scripts/prepare_task_worktree.sh <task-slug>
# 按输出的 Start with 路径进入新 worktree

# 完成修改和提交后
git push -u origin "$(git branch --show-current)"
```

两个准备脚本都生成 `codex/<task>-<UTC timestamp>` 分支；worktree 版本不会改动或要求清理当前 checkout。分支合入默认分支后，可用 `scripts/cleanup_task_worktree.sh <path>` 安全回收；它只删除干净、已有 ancestor 或 GitHub merged-PR 证据的本地任务分支（兼容 squash merge），不删除远端分支。

`prepare_task_worktree.sh` 会把来源 checkout 中以下 Git 忽略的本机配置复制到新 worktree，不复制日志、缓存、波形或其他未跟踪文件：

- `scripts/local.mk`、`scripts/local.sh`、`scripts/local.csh`
- `pd/openroad/local/`
- `pd/openroad/**/config.local.mk`

如需让多个 worktree 实时共享同一份配置，可建立一个仓库外的持久化目录，保持上述相对路径，并配置一次：

```bash
git config --local vibeSoc.localConfigRoot /persistent/path/vibe_soc-local-config
```

之后新 worktree 会软链接该目录中的白名单配置。也可仅对单次命令设置 `VIBE_SOC_LOCAL_CONFIG_ROOT`。目标 worktree 已存在的配置不会被覆盖；需要重新同步时，先明确处理对应的本地文件，再运行 `scripts/sync_local_configs.sh <target-worktree> [source-worktree]`。

push 后 workflow 会自动创建 PR，并以 squash 方式启用 GitHub auto-merge。`auto-pr-automerge` 只接受同仓库的 `codex/**`、`feature/**`、`fix/**` 分支；手动触发也不能把 Fork 或其他前缀送入自动合并路径。

要让内部 PR 无需逐次批准即可触发 `pull_request` CI，需要创建一个仓库专用 GitHub App：

1. 注册 GitHub App，例如 `vibe-soc-pr-bot`；Webhook 可以关闭。
2. Repository permissions 设置为 `Contents: Read and write`、`Pull requests: Read and write`，并且只安装到 `vibe_soc`。
3. 把 App Client ID 保存为 Actions variable `PR_AUTOMATION_APP_CLIENT_ID`。
4. 生成 App private key，把完整 PEM 保存为 Actions secret `PR_AUTOMATION_APP_PRIVATE_KEY`。
5. 在仓库 `Settings -> General -> Pull Requests` 打开 `Allow auto-merge`。
6. 给默认分支设置 branch protection，并把关键 CI check 设为 required status check。
7. 在 `Settings -> Actions -> General` 的 Fork pull request workflow 设置中，要求所有外部贡献者运行 workflow 前经过批准，并保持 Fork workflow 的 write token 和 secrets 关闭。

安装 App 并生成 private key 后，可以用 `gh` 写入仓库配置；不要把 PEM 文件提交到仓库：

```bash
gh variable set PR_AUTOMATION_APP_CLIENT_ID --body "<app-client-id>"
gh secret set PR_AUTOMATION_APP_PRIVATE_KEY < /secure/path/to/app-private-key.pem
```

配置完成后，workflow 使用一小时内有效、仅限当前仓库的 GitHub App installation token 创建 PR，因此内部 PR 可以正常触发后续 workflow。App private key 只出现在受信分支的 `push` workflow 中，不会传给 `pull_request` job 或 Fork PR。仓库默认 `GITHUB_TOKEN` 保持只读且不能批准 PR，`auto-pr-automerge` 进一步使用 `permissions: {}` 禁用内置 Token 的全部显式权限。

如果任一 App 配置项缺失，workflow 会 fail closed 并指出缺少的配置，不会回退到内置 `GITHUB_TOKEN`。如果仓库没有打开 `Allow auto-merge`，workflow 仍会创建 PR，但启用 auto-merge 的步骤会以 warning 形式跳过。

发布分支建议使用 `release/<version>` 命名。发布分支允许做小修，但修复应同步回主线，避免 release 分支长期漂移。

本地也可以手动生成设计 release 包，输出 tarball、manifest 和 SHA256SUMS：

```bash
python3 scripts/package_design_release.py \
  --out-dir /tmp/vibe_soc_release \
  --channel snapshot \
  --release-id local-smoke \
  --module chip/top \
  --test chip_sw_uart_smoketest \
  --seed 1
```

`--include-syn` 会额外收集已存在的 `chip/top/de/syn` 综合证据；脚本不会主动运行综合或仿真。

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
| `verdi` | Verdi 入口 |
| `syn` | 综合入口，默认 Yosys，可用 `SYN_TOOL=dc` 切换 Design Compiler |
| `formal` | Formality 等价检查；普通 DC 与带 UPF 的 DC 快照均可使用 |
| `formal-upf` | 强制要求 canonical/saved UPF 成对存在的 Formality 兼容入口 |
| `clp-upf` | Conformal Low Power 原生 IEEE 1801 RTL/UPF 一致性检查 |
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

### 公共综合、Formal 与 CLP Tcl

公共入口分别位于 `scripts/syn/`、`scripts/formal/` 和
`scripts/clp/`，模块 Makefile 只配置 top、库、约束、UPF 和可选 hook。
DC、Formality、CLP 共享注册综合快照中的同一份 `de/syn/rtl.f`，不会再
派生 `logic_rtl.f`。默认综合视图定义 `SYNTHESIS`，可通过
`RTL_SYNTHESIS_DEFINE` 覆盖。

`soc_formal` 接受普通 DC 快照，也接受同时包含 canonical/saved UPF 的
快照；只有后一种情况才加载 UPF。所有 EDA 目标仍必须由注册 MCP 工具
执行，Make 目标不是 agent 绕过证据门禁的直接入口。

### Filelist 约定

每个模块的 RTL 入口是 `de/rtl/filelist.f`，组合逻辑放在 `de/rtl/filelist.mk`。`make flist` 会生成模块运行用 filelist，`make validate-flist` 会展开嵌套 `-f`、检查 include 目录和源文件是否存在、去重并检测循环引用。

filelist 中优先使用模块相对路径，避免写入本机绝对目录。生成的 `de/run/rtl.f`、`de/run/rtl.raw.f` 和仿真/综合临时 filelist 都属于本地产物，不入库。

### Lint 工具说明

`lint` 默认使用 Verilator，也支持 SpyGlass：

```bash
make lint MODULE=ip/digital/uart
make lint MODULE=ip/digital/uart LINT_TOOL=verilator RTL_TOP=uart
make lint MODULE=ip/digital/uart LINT_TOOL=spyglass RTL_TOP=uart
```

SpyGlass lint 通过 `scripts/lint/sg_lint.tcl` 运行，默认 goal 为 `lint/lint_rtl`，报告写入模块 `de/run/lint_spyglass/`。VC Static lint 入口已移除；如果后续需要恢复，必须重新补齐合法 license、脚本和 MCP 参数约束。

`ip/digital/lint_lab` 是故意构造的坏 RTL 语料库，用于 SpyGlass lint 修复和规则验证基准。相关脚本位于 `scripts/lint/lint_*`。它不是功能 IP，不应接入 chip/top。

## 工具链

仿真/调试/静态检查/综合支持：

- VCS（本地已授权环境）
- Verilator
- Xcelium
- Verdi、DVE、SimVision、GTKWave（按本地授权和安装情况启用）
- SpyGlass lint/CDC（本地已授权环境）
- Yosys 结构综合
- Design Compiler 逻辑综合（本地已授权环境）

Verilator 是默认仿真后端。普通 SystemVerilog testbench 会在注册编译阶段
探测并启用 `--timing`；安装版本不支持 timing 时会明确失败，此时应升级
Verilator，或为该模块提供 `*_verilator.cpp` 自检 harness。公共 generic
harness 默认最多运行 `VERILATOR_MAX_CYCLES=100000` 个 timestep，未执行
`$finish` 会返回非零，不能把超时当 PASS。

项目脚本不会直接 source 用户 home 下的 shell 启动文件。EDA 工具能否找到取决于当前进程继承的环境变量，以及项目本地配置文件：

- `scripts/local.mk`：Make/MCP 使用，适合放 license endpoint、工具路径、DC `.db` 路径和默认参数。
- `scripts/local.sh`：bash/sh 用户 source `scripts/setup.sh` 时加载。
- `scripts/local.csh`：csh/tcsh 用户 source `scripts/setup.csh` 时加载。

这些 `scripts/local.*` 文件已被 Git 忽略，不要强制加入仓库。推荐先复制示例再填写本机值：

```bash
cp scripts/local.mk.example scripts/local.mk
```

需要 DesignWare 仿真模型时，在 `scripts/local.mk` 配置：

```make
VCS_DW_SIM_PATH := /path/to/dw/sim_ver
```

需要 Design Compiler 使用 Sky130HD 时，优先配置 Library Compiler 生成的 Synopsys `.db`：

```make
SKY130HD_DC_DB := /path/to/sky130_fd_sc_hd__tt_025C_1v80.db
```

## 门控开发流程

RTL 创建或实质修改先自动选择 Loop 模式：

```text
dev:     单模块 RTL owner -> targeted lint/compile/sim -> 保持 rtl in_progress
merge:   doc delta -> rtl -> {verif, syn} -> reviewer normal
signoff: architecture 可选 -> doc -> rtl -> {verif, syn} -> risk checks -> reviewer strict
```

`LOOP_MODE` 是最低模式而不是绕过开关。filelist 和验证 collateral 至少升级
到 `merge`；新模块、接口/寄存器、时钟复位、约束、生成 Top/wrapper、
chip-top RTL、跨模块、UPF 和 PD 自动升级到 `signoff`。

| 阶段 | 角色 | 典型产物 |
|---|---|---|
| architecture | `soc-architect` | `docs/architecture*.md` |
| doc | `soc-doc-engineer` | `docs/design_spec.md`、`interface_spec.md`、`regmap.md`、`verification_plan.md` |
| rtl | `soc-rtl-designer` 或特化角色 | `de/rtl/*.v`、`de/rtl/filelist.f`、`de/syn/*.sdc` |
| verif | `soc-verification-engineer` | `dv/tb/tb_<module>.*`、`dv/sim/sim.log` |
| syn | `soc-synthesis-engineer` | `de/syn/*_netlist.v`、`de/syn/synth.log` |
| pd handoff (post-syn) | `soc-pd-engineer` | `pd/openroad/<platform>/<design>/config.mk`、`constraint.sdc`、真实 ORFS reports/results |

PD handoff 使用 `soc-pd-engineer` 协调 OpenROAD，但它不是 `pipeline_state.json` 的正式 `doc/rtl/verif/syn` stage；只有真实 ORFS 报告和结果可作为完成依据。

每个独立模块/IP 可用 `pipeline_state.json` 跟踪阶段状态。常用状态脚本：

```bash
python3 .agents/scripts/init_state.py <workspace> <module>
python3 .agents/scripts/loop_context.py <workspace> --format text
python3 .agents/scripts/query_state.py <workspace> --compact
python3 .agents/scripts/update_state.py <workspace> rtl in_progress
```

准备 PR 前先生成最终阶段计划：

```bash
python3 .agents/scripts/loop_context.py <workspace> \
  --mode merge --format text
# 完成 packet 指定的 stale stages 和 reviewer 后：
python3 .agents/scripts/loop_context.py <workspace> \
  --mode merge --review-result pass --check-ready --format text
```

router 只输出需要读取的规则、需要执行的检查和 fingerprint 缓存命中。
详细状态仍保留在 `pipeline_state.json`，日常 Agent 不再把完整 artifact hash
和 check note 放进上下文。加 `--write` 可把紧凑 packet 写到被忽略的
`de/run/loop_evidence/loop_context.json`。

状态规则要点：

- `done` 必须有真实、非空 artifact 和至少一个 passing check。
- `dev` 只保留一个 stage owner，RTL 可跨多次迭代保持 `in_progress`；综合和独立 reviewer 延后到交付，不会被当作 PASS。
- `verif` 和 `syn` 在 RTL 完成后可以并行，但结果只对当时消费的 RTL snapshot 有效。
- 验证阶段可在 `verif in_progress` 内多次修 RTL，只在阶段完成/失败时结算一次；若 RTL 变更，`syn` 必须退回 `pending` 并重跑。
- 综合阶段同理；若综合修 RTL，`verif` 必须退回 `pending` 并重跑。
- 同一个 RTL epoch 只允许一个下游阶段承担 RTL 修复。若另一侧也需要改 RTL，重新打开 `rtl in_progress`，旧 `verif/syn` 结果会自动失效。

## MCP/Agent 功能

仓库内置自动化配置，用于 silicon-crew 风格的项目生成、构建、集成和验证。主要能力如下：

| 能力 | MCP/Skill | 说明 |
|---|---|---|
| 项目/IP/模块脚手架 | `soc-build` | `soc_init`、`soc_add_chip`、`soc_add_ip` |
| 构建与验证 | `soc-build` | filelist、lint、compile、sim、regress、coverage、syn |
| 顶层集成 | `soc-integrate` | 端口提取、实例化、wrapper、top 生成、快照、diff、刷新 |
| OpenROAD handoff | `soc-pd-engineer` + `soc-openroad` | 物理设计 handoff agent 负责约束审查和流程调度；MCP 生成 ORFS config/SDC、运行 synth/floorplan/place/cts/route/finish/all 并汇总结果 |
| Liberty/DB 辅助生成 | `lib-db-gen` | 使用 Library Compiler 将 `.lib` 转 `.db`，或从 Verilog top 端口生成早期 black-box stub `.lib/.db` |
| 寄存器 YAML 生成 | `yml2reg` | 从 YAML 生成 APB/AHB regfile RTL，以及 Spirit XML / Excel 表 / C header / sysmap |
| Excel memmap → 芯片 sysmap | `gen-asic-memmap` | 从 Excel memmap 生成 `*_ASIC.yml` 与 C/SV `*_sysmap` header |
| Excel mem → wrap + lib/lef | `gen-memwrap` | sky130 OpenRAM / nangate45 FakeRAM：统一 wrap RTL + 复制 `.lib`/`.lef` |
| Excel 寄存器生成 | `excel-yml-gen` | 从 Excel 生成 YAML、regfile RTL、wrapper 等 |
| CRG 需求转设计表 | `crg-req-to-design` | 从 CRG 需求表生成 clock/reset 设计表和 PLL 建议 |
| 时钟/复位树图 | `cr-tree-diag-gen` | 从设计表生成 Draw.io 和 Excalidraw 图 |
| 流程编排 | `vibe-soc-loop` → `soc-pipeline` | 自动选择 `dev/merge/signoff`，只协调失效阶段和所需 PD handoff |
| 独立设计审查 | `soc-reviewer` + `soc-ai-kb` | 对设计交付物做只读第一轮 Review，输出结构化风险、Issue、waiver 和交付清单，不执行 EDA 或宣称 signoff |

EDA 阶段应走注册工具入口：验证调用 `soc-build.soc_sim`，综合调用 `soc-build.soc_syn`，OpenROAD 调用 `soc-openroad.soc_openroad_*`。自动化流程不使用直接 `make`、`iverilog`、`vvp`、`yosys`、`openroad` 等 shell fallback。

## SoC Reviewer 与知识库

`soc-reviewer` 在 `merge` 中执行一次 normal review，在 `signoff` 中执行
strict review，也可用于显式独立审查；普通 `dev` 迭代不派发。它是只读
审查角色，不修改 RTL、testbench、约束、waiver 或 `pipeline_state.json`，
也不运行仿真、综合、STA 和 OpenROAD。Review 结果只作为人工二轮评审
输入，不代表设计 signoff。

审查范围按实际输入选择，可覆盖 RTL coding/lint、clock/reset、CDC/RDC、总线协议、寄存器和地址映射、顶层集成、UPF/low power、DFT、SDC/STA、综合 QoR、LEC/Formality、Formal、验证/regression/coverage、X-prop/GLS、安全、waiver、交付复现性和文档完整性。固定输出包括：

- `Review Summary`
- `Key Risks`
- `Issue List`
- `Waiver Review`
- `Delivery Checklist`
- `Next Actions`

知识库通过 Codex 全局 MCP `soc-ai-kb` 提供。当前 reviewer 使用 `kb_search`/`kb_context` 查询规则；仓库不保存个人服务地址或认证信息。可用性检查：

```bash
codex mcp list
```

### 知识库来源硬门禁

- 只有 source path 以 `soc/review/rule_library/` 开头的结果具有 `Project Rule` 权威。
- 其他知识库结果只能标记为 `Reference Evidence`，不得单独判定项目违规、设置 `Blocker/Critical` 或支持 waiver。
- 项目规则若只有标题或缺少实质 requirement，视为 placeholder，结论必须标记 `Need Human Confirmation`。
- 直接代码缺陷、失败检查、缺失 artifact 和仓库流程违规仍可使用 `Local Evidence` 报告。
- Reviewer 不得伪造规则 ID、来源、版本或项目要求。

典型调用：

```text
使用 soc-reviewer strict 审查 chip/top；知识库优先限定 soc/review/rule_library/，列出 reviewed/unreviewed domains，并输出结构化 Issue List。
```


## OpenTitan Vendor Island

`chip/top` 当前以 OpenTitan Earlgrey chip top 为主要顶层，保留 vendor island 结构以便先复用已验证的 FuseSoC 生成顺序和 DV collateral，再逐步拆成 vibe_soc 原生模块。顶层 filelist 通过 `chip/top/de/rtl/filelist.mk` 汇总各 `ip/digital/*` 子模块的 `filelist.mk`、`pkg.f` 和 `filelist.f`。

OpenTitan 相关迁移文档位于 `chip/top/docs/`，包括 case manifest、baseline、UART bootstrap bring-up log、vendor migration 和 source manifest。当前 IP 拆分以顶层一起验证为主，子模块先承担源文件组织和 filelist 边界，后续再逐步拆独立验证环境。

## 顶层集成

顶层位于 `chip/top`。自动集成产物包括：

```text
chip/top/de/rtl/filelist.f
chip/top/de/rtl/vendor/opentitan/
chip/top/de/rtl/generated/opentitan_fusesoc/
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


## CDC

CDC 使用 SpyGlass CDC 入口，配置位于 `scripts/cdc/sg_cdc.tcl`。常用入口：

```bash
make cdc MODULE=ip/digital/uart RTL_TOP=uart CDC_TOOL=spyglass
```

CDC 运行产物写入模块 `de/run/cdc/`，属于本地运行输出，不入库。

## 综合与 STA

综合通过项目 Make 或 `soc-build.soc_syn` 运行，默认 `SYN_TOOL=yosys`：

```bash
make syn MODULE=ip/digital/uart RTL_TOP=uart
```

Design Compiler 综合使用 `SYN_TOOL=dc`：

```bash
make syn MODULE=ip/digital/uart RTL_TOP=uart SYN_TOOL=dc
```

MCP 调用时使用 `soc-build.soc_syn`，并传入 `syn_tool=dc` 或 `syn_tool=yosys`。DC 通用脚本位于 `scripts/syn/dc_synth.tcl`，Sky130HD 技术库 setup 位于 `scripts/syn/sky130hd_dc_setup.tcl`。模块可在 `de/syn/dc_setup.tcl` 中 source 通用 setup。

约束文件约定：

- 原始 SDC 放在模块 `de/syn/*.sdc`，可以入库，例如 `ip/digital/uart/de/syn/uart.sdc`。
- DC 生成的 SDC 位于 `de/syn/dc/outputs/*.sdc`，属于综合产物，不入库。

综合产物位于 `de/syn/` 或 `de/syn/dc/`，包括网表、DDC/SDF、日志和报告。Yosys 结构综合结果不等于时序收敛；只有真实 STA/DC 报告可以声明 WNS/TNS 或 timing closure。

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

- 已批准 YAML 源：使用 `yml2reg` 生成 APB/AHB regfile RTL；需要软件/DV 交付物时用 `yml2docs`（XML + Excel 表 + C header + sysmap），格式对齐 `xml_reg_converter`。
- 已批准 Excel 源：使用 `excel-yml-gen` 生成 YAML、regfile RTL、instance wrapper 和 TDR buffer list。
- 不手工修改生成 RTL；修改源 YAML/Excel 后重新生成。

CRG：

- 需求表到设计表：使用 `crg-req-to-design` 生成 `clock_design.xlsx`、`reset_design.xlsx`、`crg_report.txt`。
- 设计表到图：使用 `cr-tree-diag-gen` 生成 Draw.io/Excalidraw 拓扑图。
- Excel 配置到 CRG RTL/SDC：使用已注册的 `crg-gen.crg_gen`（输出建议落到模块 `de/run/crg_gen/` 再整理进 `de/rtl` / `de/syn`）。

## 仓库卫生

`.gitignore` 已覆盖常见本地产物：

- `**/run/`、`**/sim/`、`**/cov/`
- `*.log`、`*.out`、`*.vcd`、`*.vpd`
- VCS/Verdi/仿真缓存目录
- `scripts/local.mk`、`scripts/local.sh`、`scripts/local.csh`
- `pd/openroad/work/`、`pd/openroad/work_local*/`、`pd/openroad/local/`、`pd/openroad/**/config.local.mk`

贡献者和自动化操作约定见 `AGENTS.md`，Claude 侧约定见 `CLAUDE.md`。这两个文件只描述协作和执行规则，不替代 README 的项目功能说明。

提交前建议执行：

```bash
make check-repo
git diff --check
git status --short
```

`make check-repo` 会扫描已跟踪文件和待提交文件中的本机绝对路径、license endpoint。若第三方 vendor 元数据触发告警，发布前应确认其来源和许可状态，并确认本次 diff 没有新增泄漏。

不要提交真实 license server、本机绝对工具路径、大型仿真/PD 运行产物或未审查的生成缓存。
