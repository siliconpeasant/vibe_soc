# rst_cnt Verification Plan

## 1. 验证范围

本验证计划针对 `rst_cnt` 模块,覆盖以下功能维度:

- 上电默认 `rst_n_out = 0`(reset asserted)
- 基本 stretch:`rst_n_in` 释放后延迟 `STRETCH_CYCLES` 个 `posedge clk` 才释放 `rst_n_out`
- 异步 assert:`rst_n_in` 下降沿立即拉低 `rst_n_out`,不依赖 clk
- 短脉冲被拉长:`rst_n_in` 低脉冲宽度 < 1 个 clk 周期时仍可靠拉长输出复位窗口
- `rst_n_in` 长保持:在保持期间 `rst_n_out` 保持 0
- 计数中途再次 assert:计数器重置,从最后一次 release 开始重新计满 `STRETCH_CYCLES`
- 参数化覆盖:`CNT_WIDTH = 4 / 8 / 16`,`STRETCH_CYCLES = 1 / 3 / 16 / 255` 边界与典型值
- 参数非法检查:`STRETCH_CYCLES > 2**CNT_WIDTH - 1` 时触发 `$error`
- reset glitch / 极窄毛刺鲁棒性
- 同步 deassert 沿与 `posedge clk` 严格对齐

不在本模块范围:
- 与 `rst_synchronizer` 级联后的整体亚稳态分析(由集成验证 / STA 覆盖)
- 后端 buffer tree / fanout 物理实现(由综合 + STA 覆盖)
- DFT scan 流程(本模块通常不进 scan chain)

## 2. TB 架构

```
            +----------------------------------------------------------+
            |                       testbench                          |
            |                                                          |
            |   clk_gen   ---> clk                                     |
            |   stim_gen  ---> rst_n_in                                |
            |                                                          |
            |                   rst_n_out -----> checker / scoreboard  |
            |                                                          |
            |   DUT: rst_cnt #(.CNT_WIDTH(N), .STRETCH_CYCLES(M))      |
            |                                                          |
            |   reference model:                                       |
            |     - golden cycle counter (rising on clk while          |
            |       rst_n_in is high)                                  |
            |     - expected rst_n_out =                               |
            |       (golden_cnt >= STRETCH_CYCLES) when rst_n_in==1    |
            |       else 0                                             |
            |                                                          |
            |   checker      : per-cycle compare DUT vs golden         |
            |   coverage     : functional cov groups + cycle counts    |
            |   assertions   : SVA / 简化 always @ posedge clk assert  |
            +----------------------------------------------------------+
```

- `clk_gen`:固定周期方波(默认 10ns / 100MHz)
- `stim_gen`:产生 `rst_n_in` 各类波形(长复位、短脉冲、毛刺、中途 re-assert)
- `checker`:与 golden model 周期级比对,记录释放延迟(clk 数)与异步 assert 延迟(组合延时)
- 仿真器:Icarus Verilog / VCS / Verilator(可综合子集)

## 3. 功能点列表

| 编号 | 功能点 | 优先级 |
|---|---|---|
| F-001 | 上电默认 `rst_n_out = 0` | P0 |
| F-002 | `rst_n_in` 异步 assert 立即拉低 `rst_n_out`,不依赖 clk | P0 |
| F-003 | `rst_n_in` 释放后,`rst_n_out` 在第 `STRETCH_CYCLES` 个 `posedge clk` 上变 1 | P0 |
| F-004 | `rst_n_out` 上升沿严格对齐 `posedge clk`(同步 deassert) | P0 |
| F-005 | `rst_n_in` 短脉冲(< 1 clk)能可靠触发并拉长输出复位窗口 | P0 |
| F-006 | `rst_n_in` 长保持期间 `rst_n_out` 持续为 0 | P0 |
| F-007 | 计数中途再次 assert 后,从最后一次 release 开始重新计满 `STRETCH_CYCLES` | P0 |
| F-008 | 参数化:`CNT_WIDTH = 4`、`STRETCH_CYCLES = 3` 边界值正确 | P1 |
| F-009 | 参数化:`CNT_WIDTH = 4`、`STRETCH_CYCLES = 15`(=2^N-1)边界值正确 | P1 |
| F-010 | 参数化:`STRETCH_CYCLES = 1` 最小合法值,释放后 1 个 clk 即出复位 | P1 |
| F-011 | 参数化:`CNT_WIDTH = 16`、`STRETCH_CYCLES = 1024` 大值正确 | P1 |
| F-012 | 非法参数 `STRETCH_CYCLES > 2**CNT_WIDTH - 1` 触发 `$error`(elaboration) | P1 |
| F-013 | `rst_n_in` 多次窄毛刺连续触发,每次都正确重置并拉长输出 | P2 |
| F-014 | 上电后 `rst_n_in` 一直为 1(从未 assert)时,`rst_n_out` 在第 STRETCH_CYCLES 个 clk 后释放 | P1 |

## 4. 测试用例

### TC-001 上电默认状态

- **触发条件**:仿真启动时 `rst_n_in = 0`,`clk` 跑 10 个周期。
- **期望结果**:`rst_n_out` 持续为 0,内部计数器为 0。
- **检查方法**:每个 `posedge clk` 断言 `rst_n_out == 1'b0`。
- **覆盖功能点**:F-001, F-006

### TC-002 基本 stretch(默认 STRETCH_CYCLES=16)

- **触发条件**:`rst_n_in = 0` 保持 100ns 后释放为 1。
- **期望结果**:`rst_n_out` 在 `rst_n_in` 释放后的第 16 个 `posedge clk` 上变 1;前 15 个 clk 上保持 0。
- **检查方法**:
  - 记录 `rst_n_in` 上升沿后第几个 `posedge clk` `rst_n_out` 由 0 变 1
  - 断言该计数 == STRETCH_CYCLES
  - 断言上升沿与 `posedge clk` 严格对齐(在 `posedge clk` 的 `#0` 采样为新值)
- **覆盖功能点**:F-002, F-003, F-004

### TC-003 异步 assert 不依赖 clk

- **触发条件**:`rst_n_in` 初始为 1,`rst_n_out` 已稳定释放为 1。在两个 `posedge clk` 之间(`clk` 高电平或低电平中段)将 `rst_n_in` 拉低。
- **期望结果**:`rst_n_out` 在 ns 级延时内变 0,不需要等到下一个 `posedge clk`。
- **检查方法**:`rst_n_in` 下降沿后 `#1ns` 断言 `rst_n_out == 1'b0`。
- **覆盖功能点**:F-002

### TC-004 短脉冲被拉长

- **触发条件**:`rst_n_in` 拉低 0.3 个 clk 周期(即 3ns @ 100MHz)后释放。
- **期望结果**:`rst_n_out` 立即变 0,并在 `rst_n_in` 上升沿后第 STRETCH_CYCLES 个 `posedge clk` 才释放。即:0.3 clk 的输入脉冲被拉长为 ~`STRETCH_CYCLES` clk 的输出复位窗口。
- **检查方法**:
  - 测量 `rst_n_out` 低电平持续时间,断言 ≥ `STRETCH_CYCLES` 个 clk 周期(扣除异步 assert 延时)
  - 断言释放沿对齐 `posedge clk`
- **覆盖功能点**:F-002, F-005

### TC-005 长保持

- **触发条件**:`rst_n_in = 0` 保持 1000 个 clk 周期。
- **期望结果**:期间 `rst_n_out` 始终为 0,内部计数器停在 0。
- **检查方法**:每个 `posedge clk` 断言 `rst_n_out == 1'b0`。
- **覆盖功能点**:F-006

### TC-006 计数中途再次 assert

- **触发条件**:`rst_n_in` 拉低 → 释放 → 等 `STRETCH_CYCLES / 2` 个 clk(约 8 cycles)后再次拉低 1 个 clk → 再次释放。
- **期望结果**:
  - 第二次 assert 时 `rst_n_out` 立即变 0
  - 第二次释放后,内部计数器从 0 开始重新计数
  - 第二次释放后第 `STRETCH_CYCLES` 个 `posedge clk` 才释放 `rst_n_out`
- **检查方法**:
  - 记录两次释放沿到 `rst_n_out` 上升沿的 clk 数,均 == STRETCH_CYCLES
  - 断言中途 `rst_n_out` 已被拉低
- **覆盖功能点**:F-002, F-007

### TC-007 参数化小边界(CNT_WIDTH=4, STRETCH_CYCLES=3)

- **触发条件**:DUT 例化 `CNT_WIDTH=4`,`STRETCH_CYCLES=3`。`rst_n_in` 拉低再释放。
- **期望结果**:释放后第 3 个 `posedge clk` 上 `rst_n_out` 变 1。
- **检查方法**:同 TC-002,但目标值为 3。
- **覆盖功能点**:F-008

### TC-008 参数化 N-1 边界(CNT_WIDTH=4, STRETCH_CYCLES=15)

- **触发条件**:DUT 例化 `CNT_WIDTH=4`,`STRETCH_CYCLES=15`(等于 `2^4 - 1`)。`rst_n_in` 拉低再释放。
- **期望结果**:释放后第 15 个 `posedge clk` 上 `rst_n_out` 变 1。
- **检查方法**:同 TC-002,目标值 15。验证计数器达到全 1 后正确比较与释放,无溢出问题。
- **覆盖功能点**:F-009

### TC-009 参数化最小值(STRETCH_CYCLES=1)

- **触发条件**:DUT 例化 `STRETCH_CYCLES=1`。`rst_n_in` 拉低再释放。
- **期望结果**:释放后第 1 个 `posedge clk` 上 `rst_n_out` 变 1。
- **覆盖功能点**:F-010

### TC-010 参数化大值(CNT_WIDTH=16, STRETCH_CYCLES=1024)

- **触发条件**:DUT 例化 `CNT_WIDTH=16`,`STRETCH_CYCLES=1024`。
- **期望结果**:释放后第 1024 个 `posedge clk` 上 `rst_n_out` 变 1。
- **覆盖功能点**:F-011

### TC-011 非法参数检查(STRETCH_CYCLES > 2^N - 1)

- **触发条件**:DUT 例化 `CNT_WIDTH=4`,`STRETCH_CYCLES=20`(非法)。
- **期望结果**:elaboration 阶段触发 `$error` 并 `$fatal`,仿真终止。
- **检查方法**:在 TB 中捕获 `$fatal` 或检测仿真 log 中 `$error` 字符串;独立 elaboration-only 用例。
- **覆盖功能点**:F-012

### TC-012 连续窄毛刺(reset glitch)

- **触发条件**:`rst_n_in` 在 100 个 clk 内随机触发 10 次窄脉冲(每次 ~0.2 clk),最后稳定释放。
- **期望结果**:每次毛刺均立即拉低 `rst_n_out`;最终稳定释放后第 STRETCH_CYCLES 个 `posedge clk` 才释放。
- **覆盖功能点**:F-002, F-007, F-013

### TC-013 上电后从未 assert

- **触发条件**:仿真启动时 `rst_n_in = 1`(立即释放,内部 DFF 仍为初始 reset asserted)。
- **期望结果**:`rst_n_out` 在第 `STRETCH_CYCLES` 个 `posedge clk` 释放。注意:这里依赖 Verilog `initial` 块或 stdcell `1'bx` 默认值,RTL 内部 DFF 的初值由 `rst_n_in` 决定;若 `rst_n_in` 启动即为 1,需保证 power-on 状态仍以 reset asserted 进入(可由 TB 显式给 1 个 clk 周期的 reset)。
- **检查方法**:启动 TB 时给 1 ns 的 rst_n_in=0 → 释放,然后计数 STRETCH_CYCLES。
- **覆盖功能点**:F-014

### TC-014 随机回归

- **触发条件**:使用 `$random` 生成 100 组 `rst_n_in` 波形,各种宽度(0.1 ~ 5 clk)与间隔(1 ~ 100 clk)。
- **期望结果**:每一时刻 DUT 输出与 golden model 完全一致。
- **检查方法**:周期级 scoreboard 对比,记录任意 mismatch。
- **覆盖功能点**:F-002 ~ F-007, F-013

## 5. 覆盖率目标

| 类型 | 目标 |
|---|---|
| 行覆盖率 (line) | 100% |
| 翻转覆盖率 (toggle) | 100%(`rst_n_in`、`clk`、`rst_n_out`、计数器各 bit 0->1 和 1->0 均至少一次) |
| 功能覆盖率 (functional) | F-001 ~ F-014 全部命中 |
| 参数化覆盖 | (CNT_WIDTH, STRETCH_CYCLES) ∈ { (4,1), (4,3), (4,15), (8,16), (16,1024) } 全部跑过 |
| 断言覆盖率 | TC-001 ~ TC-014 中所有 assert 均至少触发一次 |

## 6. 通过判据

模块验证通过需同时满足:

1. 全部 TC(TC-001 ~ TC-014)在 5 组参数化配置下均 PASS,0 条 assertion failure
2. 行 / 翻转 / 功能覆盖率均达到第 5 节目标
3. 仿真无 `$warning` / 非预期 `$error` / `$fatal`(TC-011 的 `$error` 为预期)
4. 仿真无 latch 推断告警(`UNOPT`、`LATCH` 等)
5. lint(Verilator `--lint-only` / Icarus warning)无 error,允许 0 个 warning
6. 释放沿与 `posedge clk` 对齐误差为 0(SVA `$rose(rst_n_out) |-> $rose(clk) within same cycle`)
