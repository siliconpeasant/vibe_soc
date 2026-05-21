# clk_glitch_free_mux Interface Specification

## 1. 模块概述

| 属性 | 内容 |
|------|------|
| 模块名 | `clk_glitch_free_mux` |
| 功能 | 无毛刺 2 选 1 时钟多路复用器，基于标准单元（std_cell_sync + std_cell_icg + std_cell_clk_or） |
| 时钟域 | 多时钟域（`clk0`、`clk1` 可为异步时钟） |
| 复位 | `rst_n`，低电平有效，异步复位（接入 std_cell_sync） |

## 2. 端口定义

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `clk0` | Input | 1 | 时钟源 0，可为任意频率/相位的时钟 |
| `clk1` | Input | 1 | 时钟源 1，可为与 clk0 异步的时钟 |
| `sel` | Input | 1 | 时钟选择信号。`0` = 选择 clk0，`1` = 选择 clk1。**支持异步输入** |
| `rst_n` | Input | 1 | 异步复位，低电平有效。复位时同步器清零，输出恒低 |
| `test_mode` | Input | 1 | 测试模式使能，高电平有效。连接到 ICG 的 `test_en`，DFT 扫描时强制透传时钟 |
| `clk_out` | Output | 1 | 无毛刺输出时钟，跟随被选中的时钟源 |

## 3. 参数

本模块无参数化配置。

## 4. 时钟与复位

### 4.1 时钟

| 时钟信号 | 类型 | 说明 |
|----------|------|------|
| `clk0` | 输入时钟 | 第一路时钟源，频率不限 |
| `clk1` | 输入时钟 | 第二路时钟源，可与 clk0 异步，频率不限 |
| `clk_out` | 输出时钟 | 经选择、同步、门控后的输出时钟 |

**注意**：`clk0` 和 `clk1` 不需要有固定的频率关系，可以是完全异步的时钟源。

`sel` 信号同样支持异步输入。模块内部的反馈互锁（feedback interlock）机制确保即使 `sel` 在不同时钟域中异步翻转，也不会产生毛刺或两个时钟源同时输出的情况。

### 4.2 复位

| 复位信号 | 类型 | 说明 |
|----------|------|------|
| `rst_n` | 输入，低电平有效 | 异步复位，接入两个 std_cell_sync 的 `rst_n` 端口 |

**复位行为**：
- `rst_n = 0` 时，两个 `std_cell_sync` 的同步链被异步清零，`en0_sync = en1_sync = 0`
- ICG 关闭两路时钟，输出 `clk_out = 0`
- `rst_n` 释放后，需等待 2 个目标时钟周期的同步延时，使能信号才恢复正常

## 5. 协议与行为

### 5.1 选择信号协议

- `sel` 为电平敏感信号，不是脉冲触发
- `sel` 的变化不会立即生效，需等待对应时钟域的 2-stage 同步器完成同步
- 从 `sel` 变化到输出实际切换的延迟取决于目标时钟的周期，最坏情况下需等待约 2 个目标时钟周期（同步器延时）+ 互锁释放延时
- **异步安全**：即使 `sel` 在时钟高电平期间翻转，反馈互锁会阻止新时钟使能直到旧时钟完全关闭

### 5.2 测试模式协议

- `test_mode` 为 active-high 电平信号
- `test_mode = 1` 时，ICG 的 `test_en` 强制使能，gated 时钟透传（不受 `en_sync` 控制）
- 用于 DFT 扫描测试，确保 scan chain 的时钟不被门控截断
- `test_mode = 0` 时，ICG 正常工作，由 `en_sync` 控制门控

### 5.3 切换时序要求

| 参数 | 描述 | 典型值 |
|------|------|--------|
| `T_switch_max` | 从 sel 变化到输出稳定的最长时间 | ~2 个目标时钟周期（2-stage sync 延时）+ 互锁释放 |
| `T_rst_release` | 从 rst_n 释放到输出恢复的最长时间 | ~2 个目标时钟周期（同步器恢复延时） |
| `T_glitch_free` | 切换过程中保证无毛刺 | 固有特性（含异步 sel） |

**设计保证**：
- 切换过程中不会产生短脉冲（runt pulse）
- 输出时钟的高电平脉冲宽度始终完整（不会被截断）
- 两个时钟源不会同时在输出上产生高电平（互斥）
- 复位期间输出确定性地为低电平

## 6. 时序约束

### 6.1 SDC 约束要点

```sdc
# 定义输入时钟
create_clock -name clk0 -period 10.0 [get_ports clk0]
create_clock -name clk1 -period 16.0 [get_ports clk1]

# 输出时钟约束
set_clock_groups -logically_exclusive -group {clk0} -group {clk1}

# 组合路径最大延迟
set_max_delay 2.0 -from [get_ports {clk0 clk1}] -to [get_ports clk_out]

# 保护 ICG 中的 latch 不被优化
set_dont_touch [get_cells -filter "ref_name =~ *ICG* || ref_name =~ *icg*"]

# 时钟路径 OR 门保护
set_dont_touch [get_cells -filter "ref_name =~ *clk_or* || ref_name =~ *CLK_OR*"]
```

### 6.2 时序特性

| 参数 | 值 | 说明 |
|------|-----|------|
| 估算传播延时 | ~1.0 ns | clk0/clk1 -> clk_out（ICG + std_cell_clk_or） |
| 约束 max_delay | 2.0 ns | SDC 中设定 |
| sel -> en_sync 延时 | ~2 个目标时钟周期 | 2-stage std_cell_sync 延时 |

## 7. 使用建议

### 7.1 典型应用场景

1. **时钟源切换**：从低频参考时钟切换到高频工作时钟
2. **测试模式**：在功能时钟和测试时钟之间选择
3. **低功耗门控**：通过 `sel` 切换到低功耗时钟源，或关闭非活动时钟

### 7.2 集成注意事项

- `sel` 可直接来自异步时钟域（反馈互锁已保证安全），但为降低亚稳态风险，仍建议由外部同步器同步后再使用
- `rst_n` 应来自系统复位域，确保上电时输出确定性地为低
- `test_mode` 应连接到 SoC 级别的 DFT 控制信号
- `clk_out` 应作为时钟信号接入时钟树综合（CTS）
- 在 SoC 顶层 STA 中，需分别对 `clk0` 和 `clk1` 路径进行时序分析
- `std_cell_clk_or`（v3.3）为时钟路径专用 OR 门，具有更对称的上升/下降延时，适合高频时钟合并场景
