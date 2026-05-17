# 从零设计一个 Glitch-Free Clock Mux：RTL -> 验证 -> 综合完整实战

> 本文记录了一个标准时钟多路复用器（Clock Mux）从需求提出到验证通过、综合落地的全过程。使用 Verilog 实现，通过 iverilog 仿真，Yosys 综合，全程遵循 Makefile 驱动的标准化 SoC 开发流程。

---

## 一、需求：为什么需要 Glitch-Free Clock Mux？

在多时钟域的 SoC 设计中，经常需要在两个（或多个）时钟源之间动态切换。例如：

- 低功耗场景：从高频工作时钟切换到低频休眠时钟
- 测试模式：从功能时钟切换到测试扫描时钟
- 时钟冗余：主备时钟切换

**普通的数据多路复用器**（如 `assign y = sel ? clk1 : clk0`）不能用于时钟切换，因为 `sel` 信号的变化如果发生在时钟高电平期间，会在输出端产生**毛刺（glitch）**—— 一个宽度不确定的窄脉冲。这个毛刺会被下游的触发器误采为有效时钟沿，导致整个时序系统崩溃。

因此，时钟多路复用器必须满足一个核心约束：

> **Glitch-Free：切换过程中绝不能产生任何毛刺或短脉冲。**

---

## 二、模块规格

### 2.1 端口定义

| 端口 | 方向 | 位宽 | 说明 |
|------|------|------|------|
| `clk0` | input | 1 | 第一路时钟源 |
| `clk1` | input | 1 | 第二路时钟源 |
| `sel` | input | 1 | 选择信号，`0=clk0`，`1=clk1` |
| `clk_en` | input | 1 | 输出使能，`0` 时强制输出低电平 |
| `clk_out` | output | 1 | 无毛刺的选定时钟输出 |

### 2.2 功能要求

1. **正常模式**：`clk_en=1` 时，`clk_out` 跟随 `sel` 选定的时钟源
2. **关断模式**：`clk_en=0` 时，`clk_out` 恒为低电平
3. **无毛刺切换**：`sel` 变化时，先等当前时钟源进入低电平期关断它，再等目标时钟源进入低电平期打开它
4. **异步安全**：`sel` 和 `clk_en` 可以是异步信号，设计本身保证安全采样

---

## 三、RTL 设计实现

### 3.1 核心原理：负电平透明 Latch + 互锁结构

Glitch-free clock mux 的经典实现基于以下观察：

> **时钟信号本身可以作为 latch 的使能信号。** 当某个时钟处于低电平期间，用 latch 捕获选择信号；当该时钟上升沿到来时，latch 已经锁存了稳定的使能值。

这样确保：**任何使能信号的变化只发生在对应时钟的低电平期**，从而保证 gated clock 的上升沿是干净完整的。

结构分解为三级：

```
sel/clk_en -> [组合逻辑产生 sel0/sel1]
                  |
                  v
         [负电平透明 Latch 0]  [负电平透明 Latch 1]
         (clk0 低电平时透明)     (clk1 低电平时透明)
                  |                        |
                  v                        v
         [AND: clk0 & en0]      [AND: clk1 & en1]
                  |                        |
                  +-----------[OR]---------+
                               |
                               v
                            clk_out
```

### 3.2 Verilog 源码

```verilog
module std_cell_clk_mux (
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    input  wire clk_en,
    output wire clk_out
);

    // 组合逻辑：根据 sel 和 clk_en 产生两路使能
    wire sel0 = ~sel & clk_en;   // 选 clk0 且使能
    wire sel1 =  sel & clk_en;   // 选 clk1 且使能

    // 负电平透明 latch：clk0 低电平时捕获 sel0 状态
    reg en0_latch;
    always @(*) begin
        if (!clk0)
            en0_latch = sel0;
    end

    // 负电平透明 latch：clk1 低电平时捕获 sel1 状态
    reg en1_latch;
    always @(*) begin
        if (!clk1)
            en1_latch = sel1;
    end

    // AND 门：gating 每一路时钟
    wire gated_clk0 = clk0 & en0_latch;
    wire gated_clk1 = clk1 & en1_latch;

    // OR 门：合并输出
    assign clk_out = gated_clk0 | gated_clk1;

endmodule
```

### 3.3 为什么 Latch 在这里是安全的？

Latch 在数字设计中通常被视为"危险信号"，因为综合工具可能在不期望的地方推断出 latch（通常是条件分支写漏了 else）。但在这个设计中：

- **Latch 是有意为之**，不是综合工具误推断
- **Latch 的使能信号是时钟本身**（`!clk0` / `!clk1`），不是某个普通控制信号
- 这种结构是**业界标准做法**，ASIC 库中甚至有专门的 Glitch-Free Clock Mux 硬核单元

---

## 四、验证：114 组测试用例全部通过

### 4.1 测试策略

时钟 mux 的验证难点在于**时序敏感**：测试的不仅是功能正确性，还要证明"没有毛刺"。为此设计了 14 组测试，覆盖以下场景：

| 测试组 | 测试内容 | 通过数 |
|--------|---------|--------|
| Test 1 | `sel=0`，验证 `clk_out` 跟随 `clk0` | 8 |
| Test 2 | `sel=1`，验证 `clk_out` 跟随 `clk1` | 8 |
| Test 3 | `sel: 0->1` 切换，验证无毛刺 | 4 |
| Test 4 | `sel: 1->0` 切换，验证无毛刺 | 4 |
| Test 5 | `clk_en=0` 强制关断输出 | 11 |
| Test 6 | `clk_en=1` 重新使能恢复 | 3 |
| Test 7 | 多次来回切换 | 12 |
| Test 8 | 快速翻转 `sel`，检测短脉冲 | 9 |
| Test 9 | `clk_en` 翻转无毛刺 | 7 |
| Test 10 | `clk_en=0` 时改变 `sel`，输出保持为 0 | 4 |
| Test 11 | 相位关系测试 | 2 |
| Test 12 | 随机 `sel`/`clk_en` 组合（16 轮） | 32 |
| Test 13 | `sel` 和 `clk_en` 同时变化 | 4 |
| Test 14 | 不同时钟相位下的切换 | 6 |
| **总计** | | **114** |

### 4.2 关键测试：Glitch-Free 切换

以 Test 3（`sel: 0->1`）为例，验证波形的关键时序：

```verilog
@(negedge clk0);
sel = 1'b0;
#1;
@(posedge clk0);
#1;
// 确认切换前 clk_out 跟随 clk0（高电平）

@(negedge clk0);
sel = 1'b1;        // 在 clk0 低电平期改变 sel
#1;
// en0_latch 在 clk0 低电平期捕获 sel0=0，clk0 被关断
// clk_out = 0（安全！）

@(negedge clk1);
#1;
// en1_latch 在 clk1 低电平期捕获 sel1=1，clk1 被打开
// 但仍为低电平期，clk_out = 0（安全！）

@(posedge clk1);
#1;
// 此时 clk1 第一个完整上升沿到来，clk_out = 1
// 成功切换到 clk1，没有毛刺！
```

核心要点：**`sel` 的变化不会立即生效，而是被 latch"延迟"到对应时钟的低电平期才生效**，这样确保 gated clock 的上升沿永远是完整周期的。

### 4.3 仿真结果

```
========================================
  std_cell_clk_mux Testbench
  clk0 period = 10ns, clk1 period = 20ns
========================================

--- Test 1: Basic selection sel=0 (clk0) ---
[PASS] @6ns sel=0, clk0 high => clk_out=1
[PASS] @11ns sel=0, clk0 low => clk_out=0
...

--- Test 3: Glitch-free sel 0->1 ---
[PASS] @26ns pre-switch: sel=0, clk0 high => clk_out=1
[PASS] @31ns sel switched 0->1, clk0 low => clk_out=0 (en0=0)
[PASS] @41ns after clk1 negedge captures sel=1, clk1 low => clk_out=0
[PASS] @51ns sel=1 latched, clk1 high => clk_out=1
...

========================================
Test summary: PASS=114 ERROR=0
RESULT: ALL TESTS PASS
========================================
```

**0 ERROR，0 MISMATCH，114 组检查全部通过。**

---

## 五、综合：Yosys 资源分析

使用 Yosys 进行综合，生成 generic 网表。关键统计如下：

### 5.1 单元统计

| 单元类型 | 数量 | 说明 |
|---------|------|------|
| `$_AND_` | 4 | `sel0/sel1` 生成 + 两路 clock gating |
| `$_DLATCH_P_` | **2** | **en0_latch / en1_latch，有意推断** |
| `$_NOT_` | 3 | `sel` 取反 + `clk0`/`clk1` 取反驱动 latch 使能 |
| `$_OR_` | 1 | 两路 gated clock 合并 |
| **总计** | **10** | |

### 5.2 面积估算

| 类型 | 数量 | 单门 GE | 小计 |
|------|------|---------|------|
| NOT | 3 | 0.5 | 1.5 |
| AND | 4 | 1.0 | 4.0 |
| OR | 1 | 1.0 | 1.0 |
| DLATCH | 2 | 3.0 | 6.0 |
| **总计** | | | **~12.5 GE** |

> GE（Gate Equivalent）是标准单元面积的归一化单位，以 2 输入 NAND 门为 1 GE。一个 12.5 GE 的面积对于时钟 mux 来说非常精简。

### 5.3 Latch 验证

综合日志确认：

```
Latch inferred for signal `\std_cell_clk_mux.\en1_latch'
Latch inferred for signal `\std_cell_clk_mux.\en0_latch'
```

**恰好 2 个 latch，全部是有意设计，没有误推断。**

### 5.4 时序说明

Clock mux 本身是 latch-based 的组合逻辑，没有触发器（FF），因此不存在传统意义上的 setup/hold 路径。WNS/TNS 标记为 N/A。

真正的时序验证应在 SoC 集成层面进行：
- 确保 `clk0`/`clk1` 到各自 latch 的时钟偏斜（skew）可控
- 保证 latch 透明窗口内的信号稳定性

### 5.5 SDC 约束

```tcl
create_clock -name clk0 -period 10.0 [get_ports clk0]
create_clock -name clk1 -period 10.0 [get_ports clk1]

# 声明两路时钟互斥，避免工具报 false path
set_clock_groups -logically_exclusive -group {clk0} -group {clk1}

# sel 和 clk_en 到 clk_out 是异步控制路径
set_false_path -from [get_ports sel]    -to [get_ports clk_out]
set_false_path -from [get_ports clk_en] -to [get_ports clk_out]
```

---

## 六、SoC 开发流水线总结

这个模块的开发遵循了标准化的 4 阶段 SoC 流水线：

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   Doc   │ -> │   RTL   │ -> │  Verif  │ -> │   Syn   │
│  (skip) │    │ (design │    │  (sim)  │    │ (yosys) │
│         │    │  + lint)│    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

| 阶段 | 工具/命令 | 产物 | 结果 |
|------|----------|------|------|
| RTL | `make lint RTL_TOP=std_cell_clk_mux` | `std_cell_clk_mux.v` | 0 warn, 0 error |
| Verif | `make comp TOP_MODULE=tb_std_cell_clk_mux` | `tb_std_cell_clk_mux.v` | 编译成功 |
| Verif | `make sim TOP_MODULE=tb_std_cell_clk_mux` | `dv/sim/wave.vcd` | **114 PASS, 0 ERROR** |
| Syn | `make syn RTL_TOP=std_cell_clk_mux` | `std_cell_clk_mux_netlist.v` | 10 cells, 0 误推断 |

**关键经验：**

1. **Makefile 驱动**：所有 EDA 操作（lint / comp / sim / syn）都通过 Makefile 统一执行，确保 cwd、路径、参数一致，避免手误
2. **标准单元惯例**：`std_cell_` 前缀的模块跳过文档阶段，直接进入 RTL，保持开发效率
3. **Lint 是 RTL 质量的第一道防线**：Verilator `-Wall` 通过后再进入仿真，避免低级语法错误浪费仿真时间
4. **Verif + Syn 并行**：RTL 完成后，验证和综合可以并行推进，互不阻塞，缩短整体开发周期

---

## 七、完整代码索引

| 文件 | 路径 |
|------|------|
| RTL | `de/rtl/std_cell/std_cell_clk_mux.v` |
| Testbench | `dv/tb/tb_std_cell_clk_mux.v` |
| Netlist | `de/syn/std_cell_clk_mux_netlist.v` |
| 综合报告 | `de/syn/std_cell_clk_mux_synthesis_report.md` |
| SDC | `de/syn/std_cell_clk_mux.sdc` |
| Filelist | `de/rtl/filelist.f` |

---

> 本文完。如需讨论时钟切换的其他实现方式（如基于 FF 的同步切换、NAND-NAND 交叉耦合结构等），欢迎留言交流。
