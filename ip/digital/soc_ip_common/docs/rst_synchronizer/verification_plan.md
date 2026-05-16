# rst_synchronizer Verification Plan

## 1. 验证范围

本验证计划针对 `rst_synchronizer` 模块,覆盖以下功能维度:

- 上电复位行为
- 异步置位行为(独立于 `clk`)
- 同步释放延迟的精确周期数
- 短脉冲(亚周期)毛刺的捕获能力
- 参数 `STAGES` 的可配置性

不在本模块范围:
- 时钟域跨越的整体验证(由上层 reset 树验证)
- DFT scan / shift(由 DFT 流程单独覆盖)
- SDC 物理时序(由 STA 流程覆盖)

## 2. TB 架构

```
            +---------------------------------------------+
            |                  testbench                  |
            |                                             |
            |   clk_gen ----------> clk                   |
            |                                             |
            |   stim    ----------> rst_async_n           |
            |                                             |
            |                       rst_sync_n  ---> chk  |
            |                                             |
            |   DUT: rst_synchronizer #(STAGES)           |
            |                                             |
            |   reference model: behavioral N-stage chain |
            |   checker        : compare DUT vs ref       |
            |   coverage       : functional cov groups    |
            +---------------------------------------------+
```

- `clk_gen`:固定周期 10 ns(100 MHz)时钟源
- `stim`:复位激励生成,支持参数化脉冲宽度、随机毛刺
- `chk`:断言模块,周期级比对 DUT 与 reference,标记 PASS/FAIL
- 仿真器:Icarus Verilog / VCS / Verilator(可综合子集)

## 3. 功能点列表

| 编号 | 功能点 | 优先级 |
|---|---|---|
| F-001 | 上电默认 `rst_sync_n = 0` | P0 |
| F-002 | 异步置位(无 clk 边沿即生效) | P0 |
| F-003 | 同步释放延迟 = STAGES 个 posedge clk | P0 |
| F-004 | 短脉冲(< 0.5 clk)能被捕获 | P0 |
| F-005 | 参数 STAGES = 2 / 3 / 4 行为正确 | P0 |
| F-006 | 复位期间 rst_sync_n 持续保持 0 | P1 |
| F-007 | 多次连续置位/释放无残留状态 | P1 |

## 4. 测试用例

### TC-001 上电复位

- **触发条件**:仿真起点 `rst_async_n = 0`,保持至少 5 个 `clk` 周期。
- **期望结果**:整个保持期间 `rst_sync_n` 恒为 0。
- **检查方法**:每个 `posedge clk` 上断言 `assert(rst_sync_n == 1'b0)`;并在 t=0 时刻(`#0`)同样断言。
- **覆盖功能点**:F-001, F-006

### TC-002 异步置位(无时钟边沿)

- **触发条件**:先让 `rst_async_n = 1`、`rst_sync_n` 稳定为 1。然后在两个 `posedge clk` **正中间**(例如 `#(period/2)` 后)将 `rst_async_n` 拉低。
- **期望结果**:在 `rst_async_n` 下降沿后的零延时(组合传播)内,`rst_sync_n` 立即变为 0,**不等待**下一个 `posedge clk`。
- **检查方法**:在 `rst_async_n` negedge 上设置 `@(negedge rst_async_n) #1 assert(rst_sync_n == 1'b0);`;并记录从 negedge 到 `rst_sync_n` 变 0 的时间应远小于一个 `clk` 周期。
- **覆盖功能点**:F-002

### TC-003 同步释放延迟精确测量

- **触发条件**:`rst_async_n = 0` 持续若干周期后,在 `posedge clk` 之后一个小延时(例如 `#1`)将 `rst_async_n` 拉高(避免与 clk 沿重合)。
- **期望结果**:
  - 从该释放沿起,经过 **正好 `STAGES` 个 `posedge clk`** 后,`rst_sync_n` 变 1。
  - 在释放沿到第 `STAGES-1` 个 `posedge clk` 期间,`rst_sync_n` 仍为 0(不能更早)。
  - 在第 `STAGES` 个 `posedge clk` 之后,`rst_sync_n` 持续为 1(不能更晚)。
- **检查方法**:计数 `posedge clk`,在第 `n < STAGES` 个时刻断言 `rst_sync_n == 0`,在第 `STAGES` 个时刻断言 `rst_sync_n == 1`。
- **覆盖功能点**:F-003

### TC-004 亚周期短脉冲毛刺捕获

- **触发条件**:先稳定 `rst_async_n = 1`、`rst_sync_n = 1`。然后在两个 `posedge clk` 之间生成一个低脉冲:脉冲宽度 = `clk` 周期的 1/4(明显小于半周期)。
- **期望结果**:
  - 在低脉冲期间(无 clk 边沿),`rst_sync_n` 被异步拉低。
  - 脉冲结束(`rst_async_n` 回 1)后,经过 `STAGES` 个 `posedge clk`,`rst_sync_n` 才回到 1。
- **检查方法**:监测 `rst_sync_n` 必须出现一次 1->0 的下降;并在脉冲尾沿后计数 `posedge clk`,在第 `STAGES` 个上断言 `rst_sync_n == 1`。
- **覆盖功能点**:F-004

### TC-005 STAGES = 2 / 3 / 4 参数化扫描

- **触发条件**:分别用 `STAGES=2`、`STAGES=3`、`STAGES=4` 例化三份 DUT(或参数化重编三次仿真)。每个配置都跑 TC-001 ~ TC-004 全部用例。
- **期望结果**:TC-003 的释放延迟应分别等于 2、3、4 个 `posedge clk`,其余行为不变。
- **检查方法**:复用 TC-001 ~ TC-004 的断言,把 `STAGES` 作为期望延迟的参数。
- **覆盖功能点**:F-005

### TC-006 复位期间持续保持

- **触发条件**:`rst_async_n = 0` 保持 100 个 `clk` 周期。
- **期望结果**:`rst_sync_n` 在这 100 个周期内恒为 0,无任何尖峰。
- **检查方法**:每 `posedge clk` 与每 `negedge clk` 都断言 `rst_sync_n == 0`。
- **覆盖功能点**:F-006

### TC-007 连续多次置位/释放

- **触发条件**:循环 16 次,每次将 `rst_async_n` 在随机相位拉低 1~5 个 `clk` 周期,再释放并保持 `STAGES + N` 个周期(`N` 随机 0~10)。
- **期望结果**:每次释放都需要经过精确 `STAGES` 个 `posedge clk` 才输出 1;不存在“上次残留导致提前释放”等问题。
- **检查方法**:对每一次释放沿都重复 TC-003 的计数检查。
- **覆盖功能点**:F-007

## 5. 覆盖率目标

| 类型 | 目标 |
|---|---|
| 行覆盖率 (line) | 100% |
| 翻转覆盖率 (toggle, on stage 寄存器) | 100%(每个 stage DFF 至少有 0->1 和 1->0) |
| 功能覆盖率 (functional) | 7/7 功能点全部命中,STAGES = 2/3/4 各跑一遍 |
| 断言覆盖率 | TC-001 ~ TC-007 中所有 assert 均至少触发一次 |

## 6. 通过判据

模块验证通过需同时满足:

1. 全部 TC(TC-001 ~ TC-007)在 `STAGES = 2/3/4` 三种参数下均 PASS,0 条 assertion failure。
2. 行 / 翻转 / 功能覆盖率均达到第 5 节目标。
3. 仿真无 `$warning` / `$error` / `$fatal`。
4. 仿真无 latch 推断告警(`UNOPT`、`LATCH` 等)。
5. lint(基础 lint 工具,如 Verilator `--lint-only` / Icarus warning)无 error,允许 0 个 warning。

