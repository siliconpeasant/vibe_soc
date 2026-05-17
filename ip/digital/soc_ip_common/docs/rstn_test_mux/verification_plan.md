# rstn_test_mux Verification Plan

## 1. 验证范围

本验证计划针对 `rstn_test_mux` 模块,覆盖以下功能维度:

- test_mode = 0 时选择 `rst_n`
- test_mode = 1 时选择 `test_rst_n`
- test_mode 动态切换行为
- 全部 8 种输入组合真值表覆盖
- 纯组合无时序 / 无 latch 推断

不在本模块范围:
- `std_cell_mux` 内部实现验证(已在 `std_cell_mux` 单独验证中覆盖)
- DFT scan / ATPG 流程(由 DFT 流程单独覆盖)
- SDC 物理时序(由 STA 流程覆盖)
- 与 `rst_synchronizer` 级联后的整体验证(由集成验证覆盖)

## 2. TB 架构

```
            +---------------------------------------------+
            |                  testbench                  |
            |                                             |
            |   stim_gen ----------> rst_n                |
            |   stim_gen ----------> test_rst_n           |
            |   stim_gen ----------> test_mode            |
            |                                             |
            |                       rst_n_out  ---> chk   |
            |                                             |
            |   DUT: rstn_test_mux                        |
            |                                             |
            |   reference model: truth_table (8-entry)    |
            |   checker        : compare DUT vs ref       |
            |   coverage       : functional cov groups    |
            +---------------------------------------------+
```

- `stim_gen`:激励生成模块,产生 `rst_n`、`test_rst_n`、`test_mode` 的全部组合及切换序列
- `chk`:断言模块,实时比对 DUT 输出与参考真值表,标记 PASS/FAIL
- 仿真器:Icarus Verilog / VCS / Verilator(可综合子集)

## 3. 功能点列表

| 编号 | 功能点 | 优先级 |
|---|---|---|
| F-001 | test_mode = 0 时,rst_n_out = rst_n | P0 |
| F-002 | test_mode = 1 时,rst_n_out = test_rst_n | P0 |
| F-003 | test_mode 从 0->1 切换后,输出在组合延时后跟随 test_rst_n | P0 |
| F-004 | test_mode 从 1->0 切换后,输出在组合延时后跟随 rst_n | P0 |
| F-005 | 全部 8 种输入组合真值表覆盖 | P0 |
| F-006 | 纯组合:输出无时钟依赖 | P1 |
| F-007 | 无 latch 推断 | P1 |

## 4. 测试用例

### TC-001 Functional mode 选择 (test_mode = 0)

- **触发条件**:固定 `test_mode = 1'b0`,让 `rst_n` 在 0/1 之间变化(包括 assert、release、多次翻转),`test_rst_n` 随机变化。
- **期望结果**:无论 `test_rst_n` 如何变化,`rst_n_out` 始终等于 `rst_n`。
- **检查方法**:每 1 ns 采样断言 `assert(rst_n_out == rst_n)`;在 `rst_n` 变化后 `#1` 内检查 `rst_n_out` 已更新。
- **覆盖功能点**:F-001, F-005

### TC-002 Test mode 选择 (test_mode = 1)

- **触发条件**:固定 `test_mode = 1'b1`,让 `test_rst_n` 在 0/1 之间变化,`rst_n` 随机变化。
- **期望结果**:无论 `rst_n` 如何变化,`rst_n_out` 始终等于 `test_rst_n`。
- **检查方法**:每 1 ns 采样断言 `assert(rst_n_out == test_rst_n)`;在 `test_rst_n` 变化后 `#1` 内检查 `rst_n_out` 已更新。
- **覆盖功能点**:F-002, F-005

### TC-003 test_mode 动态切换 0->1

- **触发条件**:初始 `test_mode = 0`,`rst_n = 1`,`test_rst_n = 0`。在仿真时间 `#100` 将 `test_mode` 切换为 1。
- **期望结果**:切换前 `rst_n_out = rst_n = 1`;切换后 `rst_n_out = test_rst_n = 0`,变化发生在组合延时内(远小于 1 ns)。
- **检查方法**:切换前断言 `rst_n_out == 1`;切换后 `#1` 断言 `rst_n_out == 0`。
- **覆盖功能点**:F-003

### TC-004 test_mode 动态切换 1->0

- **触发条件**:初始 `test_mode = 1`,`rst_n = 0`,`test_rst_n = 1`。在仿真时间 `#100` 将 `test_mode` 切换为 0。
- **期望结果**:切换前 `rst_n_out = test_rst_n = 1`;切换后 `rst_n_out = rst_n = 0`,变化发生在组合延时内。
- **检查方法**:切换前断言 `rst_n_out == 1`;切换后 `#1` 断言 `rst_n_out == 0`。
- **覆盖功能点**:F-004

### TC-005 真值表全组合覆盖

- **触发条件**:遍历 `rst_n`、`test_rst_n`、`test_mode` 的全部 8 种组合(000 ~ 111),每种保持 10 ns。
- **期望结果**:对每种组合,`rst_n_out` 严格等于真值表预期:

| rst_n | test_rst_n | test_mode | rst_n_out (expected) |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 0 |
| 0 | 1 | 0 | 0 |
| 0 | 1 | 1 | 1 |
| 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 |

- **检查方法**:对每种组合断言 `rst_n_out == expected`,并记录功能覆盖率。
- **覆盖功能点**:F-005

### TC-006 纯组合无时钟依赖

- **触发条件**:固定所有输入,运行仿真 100 ns,期间不施加任何时钟。
- **期望结果**:输出保持稳定,无变化,无 x / z 态。
- **检查方法**:每 10 ns 断言 `rst_n_out` 为确定值(0 或 1),无 `x`/`z`。
- **覆盖功能点**:F-006

### TC-007 随机激励回归

- **触发条件**:使用 `$random` 生成 1000 组随机输入向量,每组保持 1~5 ns 随机时长。
- **期望结果**:每一时刻 `rst_n_out` 都满足真值表。
- **检查方法**:连续监测断言 `rst_n_out == (test_mode ? test_rst_n : rst_n)`。
- **覆盖功能点**:F-001 ~ F-005

## 5. 覆盖率目标

| 类型 | 目标 |
|---|---|
| 行覆盖率 (line) | 100% |
| 翻转覆盖率 (toggle) | 100%(每个输入端口 0->1 和 1->0 均至少一次) |
| 功能覆盖率 (functional) | 7/7 功能点全部命中,8 种输入组合全部覆盖 |
| 断言覆盖率 | TC-001 ~ TC-007 中所有 assert 均至少触发一次 |

## 6. 通过判据

模块验证通过需同时满足:

1. 全部 TC(TC-001 ~ TC-007)均 PASS,0 条 assertion failure。
2. 行 / 翻转 / 功能覆盖率均达到第 5 节目标。
3. 仿真无 `$warning` / `$error` / `$fatal`。
4. 仿真无 latch 推断告警(`UNOPT`、`LATCH` 等)。
5. lint(基础 lint 工具,如 Verilator `--lint-only` / Icarus warning)无 error,允许 0 个 warning。
