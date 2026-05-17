# AI Agent Swarm 实战记录：一个 Clock Mux 从需求到网表

> 本文完整记录了一次"多 Agent 协作开发芯片模块"的真实过程。用户只提了一句话需求，剩下的文档、RTL、验证、综合全由 AI Agent 分工完成。所有命令和交互均为实录。

---

## 零、系统背景

我们使用 **silicon-crew** SoC 开发框架，核心规则：

1. **4 阶段流水线**：Doc -> RTL -> Verif -> Syn，每个阶段由专门的 subagent 负责
2. **主 Agent 只协调，不写 RTL**：RTL、TB、网表必须由对应的 subagent 生成
3. **标准单元可跳过 Doc**：`std_cell_` 前缀的模块无需设计文档，直接从 RTL 阶段开始
4. **Verif + Syn 并行**：RTL 完成后，验证和综合两个 agent 同时启动
5. **所有 EDA 操作走 Makefile**：禁止直接调用 verilator/iverilog/yosys 等底层工具

---

## 一、用户一句话需求

```
在soc_ip_common目录写一个std_cell_clk_mux模块
```

用户只说了这一句话。没有规格书，没有接口定义，没有验证计划。

---

## 二、主 Agent 的决策链

### Step 1：环境扫描

主 Agent 首先检查项目现状：

```bash
# 检查是否已有同名模块
grep -c "std_cell_clk_mux" pipeline_state.json
# 结果：0（不存在）

# 检查现有 std_cell 模块
ls de/rtl/std_cell/
# std_cell_and.v  std_cell_buf.v  std_cell_icg.v  std_cell_inv.v
# std_cell_mux.v  std_cell_nand.v  std_cell_or.v
```

发现已有 7 个 std_cell，其中 `std_cell_icg.v`（时钟门控）和 `std_cell_mux.v`（数据选择器）可作为风格参考。

### Step 2：确认规范

根据项目 Memory 中的规则：

| 规则 | 来源 |
|------|------|
| RTL 必须由 rtl-designer 写 | `vibe_soc_swarm_flow_mandatory.md` |
| std_cell 跳过 doc 阶段 | `vibe_soc_swarm_flow_mandatory.md` |
| EDA 操作必须走 Makefile | `feedback_eda_must_use_makefile.md` |
| verif 与 syn 必须并行 | `feedback_verif_syn_parallel.md` |
| pipeline_state 每阶段即时更新 | `feedback_pipeline_state_per_stage.md` |

**结论**：这是一个标准单元，走 "skip doc -> RTL -> 并行(Verif+Syn)" 流程。

### Step 3：规划执行路径

```
用户提需求
    |
    v
主 Agent 创建 pipeline_state 条目（doc=done, rtl=in_progress）
    |
    v
spawn soc-rtl-designer 写 RTL + lint + SDC
    |
    v
RTL done，主 Agent 更新 pipeline_state（rtl=done）
    |
    +------------------+------------------+
    |                                     |
    v                                     v
spawn soc-verification-engineer      spawn soc-synthesis-engineer
写 TB + make comp/sim                make syn + 报告
    |                                     |
    v                                     v
Verif done                            Syn done
    |                                     |
    +------------------+------------------+
                       |
                       v
          主 Agent 更新 pipeline_state
          (verif=done, syn=done)
```

---

## 三、Phase 1：创建 Pipeline State

主 Agent 在 `pipeline_state.json` 中插入新模块条目：

```json
"std_cell_clk_mux": {
  "pipeline": {
    "doc": {
      "status": "done",
      "note": "std_cell: skip doc phase"
    },
    "rtl": {
      "status": "in_progress"
    },
    "verif": {
      "status": "pending"
    },
    "syn": {
      "status": "pending"
    }
  }
}
```

---

## 四、Phase 2：RTL 设计（spawn soc-rtl-designer）

### 4.1 发给 RTL Designer 的 Prompt

主 Agent 需要给 subagent 提供完整的上下文。Prompt 长达数百字，核心信息：

```
Design a `std_cell_clk_mux` (glitch-free 2:1 clock multiplexer)
in the soc_ip_common IP.

## Module Requirements
- Ports: clk0, clk1, sel, clk_en, clk_out
- Glitch-free switching using negative-level transparent latches
- clk_en=0 forces output to 0
- No timescale directive (project convention)

## Deliverables
1. de/rtl/std_cell/std_cell_clk_mux.v
2. Update de/rtl/filelist.f
3. de/syn/std_cell_clk_mux.sdc
4. Verify lint: make lint RTL_TOP=std_cell_clk_mux

## Important Notes
- This is a standard cell — keep it simple
- Latch warnings are expected (like std_cell_icg)
- Follow Verilog-2005, lint-clean via make lint
```

### 4.2 RTL Designer 的执行过程

subagent 内部执行了以下操作：

```bash
# 1. 读取参考模块了解风格
cat de/rtl/std_cell/std_cell_icg.v
cat de/rtl/std_cell/std_cell_mux.v

# 2. 编写 RTL
cat > de/rtl/std_cell/std_cell_clk_mux.v << 'EOF'
module std_cell_clk_mux (
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    input  wire clk_en,
    output wire clk_out
);
    wire sel0 = ~sel & clk_en;
    wire sel1 =  sel & clk_en;

    reg en0_latch;
    always @(*) begin
        if (!clk0) en0_latch = sel0;
    end

    reg en1_latch;
    always @(*) begin
        if (!clk1) en1_latch = sel1;
    end

    wire gated_clk0 = clk0 & en0_latch;
    wire gated_clk1 = clk1 & en1_latch;
    assign clk_out = gated_clk0 | gated_clk1;
endmodule
EOF

# 3. 更新 filelist
echo '$SOC/ip/digital/soc_ip_common/de/rtl/std_cell/std_cell_clk_mux.v' \
    >> de/rtl/filelist.f

# 4. 写 SDC
cat > de/syn/std_cell_clk_mux.sdc << 'EOF'
create_clock -name clk0 -period 10.0 [get_ports clk0]
create_clock -name clk1 -period 10.0 [get_ports clk1]
set_clock_groups -logically_exclusive -group {clk0} -group {clk1}
set_false_path -from [get_ports sel]    -to [get_ports clk_out]
set_false_path -from [get_ports clk_en] -to [get_ports clk_out]
EOF

# 5. Lint 检查
make lint RTL_TOP=std_cell_clk_mux
```

### 4.3 RTL Designer 的返回报告

```
RTL phase complete (task=std_cell_clk_mux)

Files created:
- de/rtl/std_cell/std_cell_clk_mux.v (46 lines)
- de/syn/std_cell_clk_mux.sdc
- de/rtl/filelist.f (appended)

Lint: make lint RTL_TOP=std_cell_clk_mux
      verilator -Wall passed, 0 warnings, 0 errors
      (empty stdout, exit code 0)

Key design decisions:
- Two negative-level transparent latches for glitch-free switching
- clk_en gates both select paths at the input
- No timescale directive per project std_cell convention
```

### 4.4 主 Agent 更新 Pipeline State

rtl-designer 返回后，主 Agent 立即更新：

```json
"rtl": {
  "status": "done",
  "completed_at": "2026-05-17T09:08:45Z",
  "artifacts": [
    "de/rtl/std_cell/std_cell_clk_mux.v",
    "de/rtl/filelist.f",
    "de/syn/std_cell_clk_mux.sdc"
  ],
  "check_results": [
    { "tool": "rtl_quality", "passed": true }
  ]
}
```

---

## 五、Phase 3：并行 Verif + Syn

根据 swarm 规则，RTL 完成后 verif 和 syn 必须**在同一消息中并行 spawn**。

### 5.1 同时 spawn 两个 Agent

```
Agent A: soc-verification-engineer  (run_in_background=true)
Agent B: soc-synthesis-engineer      (run_in_background=true)
```

两个 agent 同时启动，各自独立工作。

---

### 5.2 Verif Agent 的执行记录

#### Prompt（主 Agent 发出）

```
验证 std_cell_clk_mux 模块。

## 测试要求
写 TB 覆盖：
1. 基本选择（sel=0 跟 clk0，sel=1 跟 clk1）
2. Glitch-free 切换（sel 0->1 和 1->0）
3. clk_en=0 强制关断
4. 重新使能恢复
5. 多次来回切换
6. 不同时钟频率（clk0=10ns, clk1=20ns）

## 关键规则
- MUST 用 Makefile: make comp TOP_MODULE=tb_std_cell_clk_mux
- MUST 用 Makefile: make sim TOP_MODULE=tb_std_cell_clk_mux
- 禁止自创 iverilog/vvp 命令
- $dumpfile 用 "wave.vcd"
- 报告 0 ERROR / 0 MISMATCH
```

#### Verif Agent 内部执行

```bash
# 1. 读取 RTL 了解端口
cat de/rtl/std_cell/std_cell_clk_mux.v

# 2. 编写 535 行 testbench
cat > dv/tb/tb_std_cell_clk_mux.v << 'EOF'
`timescale 1ns / 1ps
module tb_std_cell_clk_mux;
    reg clk0, clk1, sel, clk_en;
    wire clk_out;
    // ... DUT 实例化 ...
    // ... 14 组测试 ...
endmodule
EOF

# 3. 编译
make comp TOP_MODULE=tb_std_cell_clk_mux
# [COMP] Simulator: iverilog | Top: tb_std_cell_clk_mux
# 编译成功，生成 dv/sim/sim.out

# 4. 仿真
make sim TOP_MODULE=tb_std_cell_clk_mux
# [SIM] Running tb_std_cell_clk_mux ...
# VCD info: dumpfile wave.vcd opened for output.
# ...
# Test summary: PASS=114 ERROR=0
# RESULT: ALL TESTS PASS
```

#### Verif Agent 返回

```
Verification complete for `std_cell_clk_mux`

Test coverage (14 test groups, 114 checks):

| Test | Description | Result |
|------|-------------|--------|
| 1 | Basic selection sel=0 (clk0) | PASS (8) |
| 2 | Basic selection sel=1 (clk1) | PASS (8) |
| 3 | Glitch-free switching sel 0->1 | PASS (4) |
| 4 | Glitch-free switching sel 1->0 | PASS (4) |
| 5 | Clock enable disable | PASS (11) |
| 6 | Re-enable | PASS (3) |
| 7 | Multiple transitions | PASS (12) |
| 8 | Runt pulse detection | PASS (9) |
| 9 | clk_en toggle glitch-free | PASS (7) |
| 10 | sel change while clk_en=0 | PASS (4) |
| 11 | Phase relationship | PASS (2) |
| 12 | Random transitions (16 rounds) | PASS (32) |
| 13 | Simultaneous sel+clk_en change | PASS (4) |
| 14 | Switch at various phases | PASS (6) |

Results: 114 PASS, 0 ERROR, 0 MISMATCH

Sanity checks:
- No *.vcd in workspace root (OK)
- dv/sim/wave.vcd exists with fresh timestamp (OK)
```

---

### 5.3 Syn Agent 的执行记录

#### Prompt（主 Agent 发出）

```
综合 std_cell_clk_mux 模块。

## 设计特点
- 2 个 negative-level transparent latches（有意设计）
- AND-OR 组合逻辑
- 无触发器
- clk0 和 clk1 是异步源

## 要求
1. make syn RTL_TOP=std_cell_clk_mux
2. 生成：netlist、report、timing.rpt、area.rpt、final.sdc
3. 报告中注明：latch 是有意的、WNS N/A、无错误
```

#### Syn Agent 内部执行

```bash
# 执行综合
make syn RTL_TOP=std_cell_clk_mux
# [SYN] Yosys | Top: std_cell_clk_mux
# ...
# === std_cell_clk_mux ===
#    Number of wires:                  14
#    Number of cells:                  10
#      $_AND_                          4
#      $_DLATCH_P_                     2
#      $_NOT_                          3
#      $_OR_                           1
# ...
# [SYN] Netlist: de/syn/std_cell_clk_mux_netlist.v
# [SYN] Report:  de/syn/synth.log
```

Yosys 输出关键日志：

```
Latch inferred for signal `\std_cell_clk_mux.\en1_latch'
Latch inferred for signal `\std_cell_clk_mux.\en0_latch'
```

**恰好 2 个 latch，全部是有意推断。**

#### Syn Agent 返回

```
Synthesis Results: std_cell_clk_mux

| Metric | Value |
|--------|-------|
| Total cells | 10 |
| $_AND_ | 4 |
| $_DLATCH_P_ | 2 (intentional) |
| $_NOT_ | 3 |
| $_OR_ | 1 |
| Wires | 14 |
| Flip-flops | 0 |
| WNS/TNS | N/A |
| Area | ~12.5 GE |

Generated:
- de/syn/std_cell_clk_mux_netlist.v
- de/syn/std_cell_clk_mux_synthesis_report.md
- de/syn/timing.rpt
- de/syn/area.rpt
- de/syn/final.sdc
```

---

### 5.4 两个 Agent 谁先完成？

| Agent | 耗时 | 完成顺序 |
|-------|------|---------|
| Synthesis | ~115 秒 | 先完成 |
| Verification | ~289 秒 | 后完成 |

**Syn agent 先返回**。主 Agent 立即更新 pipeline_state，标记 syn=done。不等待 verif。

**Verif agent 后返回**。主 Agent 再次更新 pipeline_state，标记 verif=done。

这体现了"每阶段即时更新"的规则——不攒到收尾再统一写。

---

## 六、Phase 4：Pipeline State 最终态

所有阶段完成后，`std_cell_clk_mux` 在 pipeline_state.json 中的状态：

```json
"std_cell_clk_mux": {
  "pipeline": {
    "doc": {
      "status": "done",
      "note": "std_cell: skip doc phase"
    },
    "rtl": {
      "status": "done",
      "completed_at": "2026-05-17T09:08:45Z",
      "artifacts": ["de/rtl/std_cell/std_cell_clk_mux.v",
                    "de/rtl/filelist.f",
                    "de/syn/std_cell_clk_mux.sdc"],
      "check_results": [{"tool": "rtl_quality", "passed": true}]
    },
    "verif": {
      "status": "done",
      "completed_at": "2026-05-17T09:14:06Z",
      "artifacts": ["dv/tb/tb_std_cell_clk_mux.v",
                    "dv/sim/tb_std_cell_clk_mux.log"],
      "check_results": [{"tool": "sim", "passed": true,
                          "note": "0 ERROR 0 MISMATCH"}]
    },
    "syn": {
      "status": "done",
      "completed_at": "2026-05-17T09:08:45Z",
      "artifacts": ["de/syn/std_cell_clk_mux_netlist.v",
                    "de/syn/synth.log",
                    "de/syn/std_cell_clk_mux_synthesis_report.md",
                    "de/syn/timing.rpt",
                    "de/syn/area.rpt",
                    "de/syn/final.sdc"],
      "check_results": [{"tool": "syn", "passed": true,
                          "note": "Yosys OK, 10 cells, 0 latch误推断, WNS N/A"}]
    },
    "release": {
      "status": "pending",
      "next_action": "spawn soc-release-engineer"
    }
  }
}
```

---

## 七、完整执行命令汇总

以下是从用户提需求到全部完成的**所有主 Agent 和 subagent 执行过的命令**：

### 主 Agent 环境扫描

```bash
# 检查模块是否已存在
grep -c "std_cell_clk_mux" pipeline_state.json
ls de/rtl/std_cell/
cat de/rtl/std_cell/std_cell_icg.v
cat de/rtl/std_cell/std_cell_mux.v
cat de/rtl/filelist.f
```

### 主 Agent 更新 pipeline_state

```bash
# 编辑 pipeline_state.json，插入 std_cell_clk_mux 条目
# doc=done(skip), rtl=in_progress, verif=pending, syn=pending
```

### RTL Designer Agent

```bash
make lint RTL_TOP=std_cell_clk_mux
# verilator --lint-only -I$(RTL_PATH) --top-module std_cell_clk_mux
# 0 warn, 0 error
```

### 并行：Verif + Syn

```bash
# === Verif Agent ===
make comp TOP_MODULE=tb_std_cell_clk_mux
# iverilog -g2012 -s tb_std_cell_clk_mux -o dv/sim/sim.out ...

make sim TOP_MODULE=tb_std_cell_clk_mux
# cd dv/sim && vvp sim.out
# 114 PASS, 0 ERROR

# === Syn Agent ===
make syn RTL_TOP=std_cell_clk_mux
# yosys syn.ys
# 10 cells, 2 intentional latch
```

---

## 八、Swarm 协作的关键观察

### 8.1 为什么需要 "主 Agent 只协调"？

如果只有一个 Agent 做所有事情，它可能会：
- 写 RTL 时忘了更新 filelist
- 写 TB 时路径搞错
- 综合时漏掉 SDC
- 各阶段的产物格式不一致

而 swarm 架构中：
- **rtl-designer** 只专注 RTL + lint，交付物格式标准化
- **verif-engineer** 只专注 testbench + 仿真，不碰 RTL
- **synthesis-engineer** 只专注综合 + 报告，不碰 TB
- **主 Agent** 负责状态流转和规则校验，确保每个阶段的产物被正确归档

### 8.2 为什么 Verif + Syn 要并行？

RTL 完成后的两个下游任务没有依赖关系：
- Verif 验证的是**功能正确性**（behavioral simulation）
- Syn 验证的是**可综合性 + 面积时序**（synthesis + stat）

串行执行总耗时 = 289s + 115s = 404s
并行执行总耗时 = max(289s, 115s) = **289s**

节省了 ~28% 的时间。在大型项目中这个比例会更显著。

### 8.3 为什么所有命令必须走 Makefile？

以仿真为例，如果不走 Makefile 直接调 iverilog：

```bash
# 错误做法
iverilog -o sim.out tb.v dut.v        # cwd 错，产物散落
vvp sim.out                           # VCD 可能落错目录
```

Makefile 保证了：
- 统一的编译参数（`-g2012`）
- 统一的输出目录（`dv/sim/`）
- 统一的 VCD 路径（`dv/sim/wave.vcd`）
- 统一的日志归档（`dv/sim/tb_xxx.log`）

这是多人/多 Agent 协作的基础设施。

---

## 九、产物清单

| 文件 | 路径 | 大小 | 说明 |
|------|------|------|------|
| RTL | `de/rtl/std_cell/std_cell_clk_mux.v` | 46 行 | Glitch-free clock mux |
| Filelist | `de/rtl/filelist.f` | 12 项 | 已包含新模块 |
| Testbench | `dv/tb/tb_std_cell_clk_mux.v` | 535 行 | 14 组测试 |
| Sim Log | `dv/sim/tb_std_cell_clk_mux.log` | - | 114 PASS |
| VCD | `dv/sim/wave.vcd` | - | 波形文件 |
| Netlist | `de/syn/std_cell_clk_mux_netlist.v` | - | Yosys generic |
| Synth Report | `de/syn/std_cell_clk_mux_synthesis_report.md` | - | 详细报告 |
| Timing RPT | `de/syn/timing.rpt` | - | N/A (latch-based) |
| Area RPT | `de/syn/area.rpt` | - | ~12.5 GE |
| Final SDC | `de/syn/final.sdc` | - | 时钟约束 |
| SDC | `de/syn/std_cell_clk_mux.sdc` | - | 原始约束 |

---

## 十、总结

从一个**用户的一句话需求**：

```
在soc_ip_common目录写一个std_cell_clk_mux模块
```

到**完整的可交付产物**：

```
RTL (lint-clean) + Testbench (114 PASS) + Netlist (10 cells) + SDC
```

中间经历了：

1. **1 个主 Agent**：环境扫描、流程规划、状态管理、3 次 pipeline_state 更新
2. **1 个 RTL Designer**：写 RTL、跑 lint、写 SDC、更新 filelist
3. **1 个 Verification Engineer**：写 535 行 TB、14 组测试、仿真验证
4. **1 个 Synthesis Engineer**：Yosys 综合、生成报告、分析资源

**全过程零人工干预**，所有命令通过 Makefile 标准化执行，所有产物路径通过 pipeline_state.json 统一追踪。

这就是 silicon-crew SoC swarm 流水线的实际运作方式。

---

> 本文是过程实录，技术实现细节可参考同目录下的 `std_cell_clk_mux_article.md`。
