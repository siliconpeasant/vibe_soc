# clk_glitch_free_mux Verification Plan

## 1. 验证范围

本验证计划覆盖 `clk_glitch_free_mux` 模块（v3.3）的全部功能验证，包括：
- 基本 2 选 1 时钟选择功能
- 复位功能（rst_n 控制）
- 测试模式功能（test_mode / DFT）
- 无毛刺切换机制验证
- 异步时钟源支持验证
- 异步 sel 输入安全切换验证
- 边界条件和异常场景

## 2. 功能点列表

| ID | 功能点 | 优先级 | 验证方法 |
|----|--------|--------|----------|
| F01 | 选择 clk0 输出（sel=0, rst_n=1） | P0 | 定向测试 |
| F02 | 选择 clk1 输出（sel=1, rst_n=1） | P0 | 定向测试 |
| F03 | 复位功能（rst_n=0） | P0 | 定向测试 |
| F04 | 复位释放后正常恢复 | P0 | 定向测试 |
| F05 | clk0 -> clk1 无毛刺切换 | P0 | 定向测试 + glitch 检测器 |
| F06 | clk1 -> clk0 无毛刺切换 | P0 | 定向测试 + glitch 检测器 |
| F07 | 快速 sel 翻转稳定性 | P1 | 定向测试 + glitch 检测器 |
| F08 | 异步 sel 切换（clk0 高电平期翻转） | P0 | 定向测试 + glitch 检测器 |
| F09 | 异步 sel 切换（clk1 高电平期翻转） | P0 | 定向测试 + glitch 检测器 |
| F10 | 异步时钟独立性验证 | P1 | 定向测试 |
| F11 | 多次来回切换可靠性 | P1 | 定向测试 + glitch 检测器 |
| F12 | test_mode=1 时 ICG 强制透传（sel=0） | P1 | 定向测试 |
| F13 | test_mode=1 时 ICG 强制透传（sel=1） | P1 | 定向测试 |
| F14 | test_mode 切换时无毛刺 | P1 | 定向测试 + glitch 检测器 |
| F15 | 复位期间 sel 变化不影响输出 | P2 | 定向测试 |
| F16 | 快速异步 sel 翻转稳定性 | P1 | 定向测试 + glitch 检测器 |
| F17 | 双向切换可靠性（clk0->clk1->clk0） | P1 | 定向测试 + glitch 检测器 |

## 3. 测试用例

### 3.1 测试用例清单

| TC ID | 名称 | 对应功能点 | 描述 |
|-------|------|------------|------|
| TC01 | Basic mux select clk0 | F01 | sel=0, rst_n=1，验证 clk_out 跟随 clk0 |
| TC02 | Basic mux select clk1 | F02 | sel=1, rst_n=1，验证 clk_out 跟随 clk1 |
| TC03 | Reset active | F03 | rst_n=0，验证 clk_out 恒为低，不受 sel/clk 影响 |
| TC04 | Reset release recovery | F04 | rst_n 释放后，验证经 2-stage sync 后正常恢复 |
| TC05 | Switch clk0->clk1 glitch-free | F05 | 从 clk0 切换到 clk1，检测无毛刺 |
| TC06 | Switch clk1->clk0 glitch-free | F06 | 从 clk1 切换到 clk0，检测无毛刺 |
| TC07 | Rapid sel toggles | F07 | 快速翻转 sel 10 次，检测无毛刺 |
| TC08 | Async sel switch clk0 high phase | F08 | sel 在 clk0 高电平期异步翻转，验证无毛刺 |
| TC09 | Async sel switch clk1 high phase | F09 | sel 在 clk1 高电平期异步翻转，验证 break-before-make |
| TC10 | Async clocks independence | F10 | 验证异步时钟（10ns/16ns）可独立运行和切换 |
| TC11 | Multiple back-and-forth switches | F11 | 5 次来回切换，检测无毛刺 |
| TC12 | Test mode clk0 selected | F12 | test_mode=1, sel=0，验证 gated_clk0 强制透传 |
| TC13 | Test mode clk1 selected | F13 | test_mode=1, sel=1，验证 gated_clk1 强制透传 |
| TC14 | Test mode toggle glitch-free | F14 | test_mode 开关切换，检测 clk_out 无毛刺 |
| TC15 | sel change during reset | F15 | rst_n=0 时改变 sel，验证输出不受影响 |
| TC16 | Rapid async sel toggles | F16 | sel 以不同时钟域频率快速翻转 20 次，验证稳定性 |
| TC17 | Bidirectional async switches | F17 | 异步 sel 来回切换 10 次，验证双向互锁可靠 |

### 3.2 测试环境配置

```
时钟配置：
- clk0: 10ns 周期（100MHz），50% 占空比
- clk1: 16ns 周期（62.5MHz），50% 占空比
- clk0 与 clk1 异步（无固定相位关系）

复位配置：
- rst_n: 初始为 0，保持 50ns 后释放
- 验证复位期间输出恒低
- 验证复位释放后经 2-stage sync 恢复

Glitch 检测器：
- 监测 clk_out 的上升沿和下降沿
- 检测高电平脉冲宽度 < 2ns 的短脉冲
- 检测两个 gated 时钟同时为高的异常情况（互锁失效）
- 记录 glitch 次数并在测试报告中输出

异步 sel 激励生成：
- sel 翻转使用与 clk0/clk1 均异步的独立时钟域（如 7ns 周期）
- 在仿真中随机化 sel 翻转与 clk0/clk1 的相位关系
- 覆盖 sel 翻转发生在 clk0/clk1 高电平期、低电平期、上升/下降沿的所有场景
```

## 4. 覆盖率目标

### 4.1 功能覆盖率

| 覆盖项 | 目标 | 说明 |
|--------|------|------|
| sel 取值覆盖 | 100% | sel=0 和 sel=1 均需覆盖 |
| rst_n 取值覆盖 | 100% | rst_n=0 和 rst_n=1 均需覆盖 |
| test_mode 取值覆盖 | 100% | test_mode=0 和 test_mode=1 均需覆盖 |
| 切换方向覆盖 | 100% | 0->1 和 1->0 均需覆盖 |
| 时钟相位覆盖 | 高 | sel 变化发生在不同时钟相位 |
| 复位场景覆盖 | 100% | 复位期间/复位释放/复位中 sel 变化 |

### 4.2 代码覆盖率

| 类型 | 目标 |
|------|------|
| 行覆盖率（Line Coverage） | >= 95% |
| 分支覆盖率（Branch Coverage） | >= 95% |
| 表达式覆盖率（Expression Coverage） | >= 95% |
| 状态覆盖率（FSM Coverage） | N/A（无状态机） |

## 5. Testbench 架构

```
┌─────────────────────────────────────────────────────────┐
│                    tb_clk_glitch_free_mux                │
│                                                          │
│  ┌─────────────┐    ┌─────────────────┐                 │
│  │  Clock Gen  │───►│      DUT        │                 │
│  │  - clk0     │    │  clk_glitch_    │                 │
│  │  - clk1     │    │  free_mux       │                 │
│  └─────────────┘    │                 │                 │
│                     │  clk0 ──┐       │                 │
│  ┌─────────────┐    │  clk1 ──┤       │                 │
│  │  Stimulus   │───►│  sel  ──┼──► clk_out              │
│  │  - sel      │    │  rst_n──┤       │                 │
│  │  - rst_n    │    │test_mode┘       │                 │
│  │  - test_mode│    └─────────────────┘                 │
│  └─────────────┘                                         │
│                                                          │
│  ┌─────────────┐    ┌─────────────────┐                 │
│  │   Checker   │◄───│ Glitch Detector │                 │
│  │  - pass/fail│    │  (runt pulse    │                 │
│  │  - summary  │    │   detection)    │                 │
│  └─────────────┘    └─────────────────┘                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.1 组件说明

| 组件 | 功能 |
|------|------|
| Clock Gen | 生成两路异步时钟（clk0: 100MHz, clk1: 62.5MHz） |
| Stimulus | 产生 sel、rst_n、test_mode 的测试序列 |
| DUT | 被测模块 `clk_glitch_free_mux` |
| Glitch Detector | 实时监测 clk_out，检测 <2ns 的短脉冲 |
| Checker | 采样 clk_out 并与预期值比较，统计 pass/fail |

### 5.2 辅助 Task

| Task | 功能 |
|------|------|
| `run_test(name)` | 打印测试名称，递增测试编号 |
| `check(condition, msg)` | 条件判断，记录 pass/fail |
| `wait_stable()` | 等待两路时钟均经历至少 2 个周期，确保同步器已稳定 |

## 6. 通过判据

### 6.1 仿真通过标准

| 判据 | 要求 |
|------|------|
| 所有定向测试通过 | 17 个测试场景全部执行（v3.3 覆盖复位、test_mode、异步 sel） |
| 检查点通过数 | 50/50 PASS（0 FAIL） |
| Glitch 检测 | 0 个毛刺被检测到 |
| 互锁验证 | 0 次 gated_clk0 与 gated_clk1 同时为高 |
| 复位验证 | 复位期间输出恒低，释放后正常恢复 |
| test_mode 验证 | test_mode=1 时 ICG 强制透传，test_mode=0 时正常门控 |
| 超时保护 | 仿真在 10000ns 内正常结束 |

### 6.2 实际验证结果

| 项目 | 结果 |
|------|------|
| 测试场景数 | 17 |
| 检查点总数 | 50 |
| PASS | 50 |
| FAIL | 0 |
| Glitches | 0 |
| 互锁失效 | 0 |
| 结论 | **ALL TESTS PASS** |

## 7. 回归测试建议

1. **RTL 修改后**：全量运行 17 个测试场景
2. **综合网表验证**：使用综合后网表 + SDF 反标进行门级仿真
3. **v3.3 专项回归**：
   - `std_cell_clk_or` 替换后的时钟特性验证（上升/下降沿对称性）
   - 高频时钟（如 1GHz）下的时序验证
   - test_mode 切换时的 glitch 检测
4. **corner case 补充**：
   - 极低频时钟（如 1MHz）切换
   - 占空比非 50% 的时钟源
   - sel 与 rst_n 同时变化的场景
   - 复位释放后立即切换 sel 的场景
