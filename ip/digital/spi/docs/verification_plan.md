# spi Verification Plan

## 1. 验证范围

本验证计划覆盖 SPI Master 控制器 IP 的全部功能，包括：

- APB 从接口功能（寄存器读写、地址解码）
- SPI 主设备功能（4 种模式、波特率分频、MSB first 传输）
- FIFO 功能（8 深度 TX/RX FIFO、满/空标志、溢出处理）
- 中断功能（5 种中断源、使能/清除机制）
- 片选管理（自动/手动模式、4 从设备选择）
- 帧格式配置（4~16 位可变长度、CPOL/CPHA）
- 复位行为
- 边界条件（最小/最大分频值、FIFO 边界、背靠背传输）

## 2. 功能点列表

### 2.1 APB 接口功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| APB-01 | 寄存器读写 | P0 | 验证所有寄存器（CTRL/STATUS/BAUD/TXDATA/RXDATA/IE/IS/FRAME）可正确读写 |
| APB-02 | 地址解码 | P0 | 验证非法地址访问不导致错误，返回 0 |
| APB-03 | 保留位 | P1 | 验证保留位读为 0，写被忽略 |
| APB-04 | 只读寄存器 | P1 | 验证 STATUS/RXDATA 写操作被忽略 |
| APB-05 | 只写寄存器 | P1 | 验证 TXDATA 读操作返回 0 |

### 2.2 SPI 传输功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| SPI-01 | Mode 0 传输 | P0 | CPOL=0, CPHA=0，验证 sclk/mosi/miso 时序 |
| SPI-02 | Mode 1 传输 | P0 | CPOL=0, CPHA=1，验证 sclk/mosi/miso 时序 |
| SPI-03 | Mode 2 传输 | P0 | CPOL=1, CPHA=0，验证 sclk/mosi/miso 时序 |
| SPI-04 | Mode 3 传输 | P0 | CPOL=1, CPHA=1，验证 sclk/mosi/miso 时序 |
| SPI-05 | MSB first | P0 | 验证数据从最高位开始发送 |
| SPI-06 | 可变帧长度 | P0 | 验证 4/8/12/16 位帧长度正确 |
| SPI-07 | 波特率精度 | P0 | 验证各分频值下 sclk 周期正确 |
| SPI-08 | 片选自动管理 | P0 | 验证传输开始时 assert，结束后 deassert |
| SPI-09 | 片选手动模式 | P1 | 验证软件可手动控制 cs_n |
| SPI-10 | 多从设备选择 | P1 | 验证 slave_sel 切换对应 cs_n |
| SPI-11 | 全双工传输 | P0 | 验证同时发送和接收 |
| SPI-12 | 忙标志 | P1 | 验证传输期间 busy=1，空闲时 busy=0 |

### 2.3 FIFO 功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| FIFO-01 | TX FIFO 写入 | P0 | 验证写 TXDATA 推入 TX FIFO |
| FIFO-02 | TX FIFO 读出 | P0 | 验证 SPI 从 TX FIFO 读取数据 |
| FIFO-03 | TX FIFO 满 | P0 | 验证 8 次写入后 tx_fifo_full=1 |
| FIFO-04 | TX FIFO 空 | P0 | 验证所有数据发送后 tx_fifo_empty=1 |
| FIFO-05 | RX FIFO 写入 | P0 | 验证 SPI 接收数据推入 RX FIFO |
| FIFO-06 | RX FIFO 读出 | P0 | 验证读 RXDATA 从 RX FIFO 弹出 |
| FIFO-07 | RX FIFO 满 | P0 | 验证 8 次接收后 rx_fifo_full=1 |
| FIFO-08 | RX FIFO 空 | P0 | 验证所有数据读出后 rx_fifo_empty=1 |
| FIFO-09 | TX FIFO underrun | P1 | 验证 TX FIFO 满时再写触发 underrun |
| FIFO-10 | RX FIFO overrun | P1 | 验证 RX FIFO 满时再接收触发 overrun |
| FIFO-11 | FIFO 计数器 | P1 | 验证 tx_fifo_cnt/rx_fifo_cnt 正确 |

### 2.4 中断功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| IRQ-01 | TX_EMPTY 中断 | P0 | 验证 TX FIFO 变空时触发 |
| IRQ-02 | RX_FULL 中断 | P0 | 验证 RX FIFO 变满时触发 |
| IRQ-03 | TX_UNDERRUN 中断 | P1 | 验证 TX FIFO 满时写触发 |
| IRQ-04 | RX_OVERRUN 中断 | P1 | 验证 RX FIFO 满时接收触发 |
| IRQ-05 | TRANSFER_DONE 中断 | P0 | 验证每帧传输完成触发 |
| IRQ-06 | 中断使能 | P0 | 验证 IE 寄存器控制各中断使能 |
| IRQ-07 | 中断清除 | P0 | 验证写 1 清除 IS 寄存器对应位 |
| IRQ-08 | irq 输出 | P0 | 验证 irq = OR(IE & IS) |

### 2.5 波特率生成功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| BR-01 | 分频精度 | P0 | 验证 spi_div 配置后 sclk 周期正确 |
| BR-02 | 常用波特率 | P0 | 验证 100k/1M/5M/10M/25M/50MHz |
| BR-03 | 边界分频值 | P1 | 验证 spi_div = 0 和 spi_div = 65535 |
| BR-04 | 动态修改 | P1 | 验证 SPI 空闲时修改 spi_div 生效 |

### 2.6 集成/系统功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| SYS-01 | SPI 回环 | P0 | mosi 直连 miso，验证数据完整性 |
| SYS-02 | 复位验证 | P0 | 验证复位后所有寄存器和信号处于正确初始状态 |
| SYS-03 | 随机数据 | P1 | 发送随机数据，验证收发一致 |
| SYS-04 | 长时间运行 | P2 | 连续发送 1000 帧，验证无丢包 |
| SYS-05 | 背靠背传输 | P1 | TX FIFO 有多个数据时自动连续传输 |
| SYS-06 | 寄存器配置组合 | P1 | 随机组合 CPOL/CPHA/帧长/分频，验证功能正确 |

## 3. 覆盖率目标

### 3.1 代码覆盖率

| 类型 | 目标 |
|------|------|
| Line Coverage | 100% |
| Branch Coverage | 100% |
| FSM State Coverage | 100%（SPI 5 状态） |
| FSM Transition Coverage | 100% |
| Toggle Coverage | 100%（所有端口和内部信号） |

### 3.2 功能覆盖率

| 覆盖点 | 目标 |
|--------|------|
| CPOL/CPHA 组合 | 覆盖全部 4 种模式 |
| frame_len | 覆盖 4/8/12/16 位 |
| spi_div 值 | 至少覆盖 6 种常用速率 + 2 种边界值 |
| slave_sel | 覆盖 0~3 所有从设备 |
| TX FIFO 状态 | 覆盖 empty / not_empty / full |
| RX FIFO 状态 | 覆盖 empty / not_empty / full |
| 中断源 | 覆盖全部 5 种中断 |
| 片选模式 | 覆盖自动和手动模式 |
| 背靠背传输 | 覆盖连续发送/接收场景 |
| APB 地址 | 覆盖所有有效地址和非法地址 |

## 4. Testbench 架构

```
+-------------------------------------------------------------------+
|                        tb_spi (Top)                               |
|                                                                   |
|  +------------------+        +--------------------------------+   |
|  |   spi_dut        |        |   Test Sequence                |   |
|  |   (DUT)          |<------>|   (task-based tests)           |   |
|  |                  |        |                                |   |
|  |  sclk ---------->|>------>|  SPI slave BFM                 |   |
|  |  mosi ---------->|>------>|  (miso response)               |   |
|  |  miso <---------|<-------|                                |   |
|  |  cs_n ---------->|>------>|                                |   |
|  |                  |        |                                |   |
|  |  apb_* <------->|<----->|  APB master BFM                |   |
|  |                  |        |                                |   |
|  |  irq ----------->|>------>|                                |   |
|  |                  |        |                                |   |
|  +------------------+        +--------------------------------+   |
|           ^                            ^                          |
|           |                            |                          |
|  +------------------+        +--------------------------------+   |
|  |   Clock/Reset    |        |   Scoreboard/Checker           |   |
|  |   Generator      |        |   (auto check)                 |   |
|  +------------------+        +--------------------------------+   |
|                                                                   |
+-------------------------------------------------------------------+
```

### 4.1 Testbench 组件

| 组件 | 描述 |
|------|------|
| `tb_spi.v` | Top-level testbench |
| `spi_dut` | 被测 SPI Master 模块实例 |
| `clk_gen` | 100MHz 时钟生成（`#5` 翻转） |
| `rst_gen` | 复位生成（低电平有效，持续 100ns） |
| `apb_bfm` | APB 总线功能模型：读写寄存器的 task |
| `spi_slave_bfm` | SPI 从设备功能模型：响应 sclk/mosi，驱动 miso |
| `scoreboard` | 自动比对：发送数据 vs 接收数据，检查 SPI 时序 |

### 4.2 APB BFM 接口

```verilog
task apb_write(input [11:0] addr, input [31:0] data);
  // 执行 APB 写操作
endtask

task apb_read(input [11:0] addr, output [31:0] data);
  // 执行 APB 读操作
endtask
```

### 4.3 SPI Slave BFM 接口

```verilog
task spi_slave_response(input [15:0] data, input [4:0] frame_len);
  // 根据 sclk/cpol/cpha 在 miso 上输出数据
  // 同时采样 mosi 数据
endtask
```

## 5. 测试用例

### 5.1 基础测试 (Smoke Tests)

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_apb_basic_rw` | APB 读写所有寄存器 | 读写值一致，保留位读为 0 |
| `test_spi_mode0_single` | Mode 0 单帧 8-bit 传输 | mosi/sclk 时序正确，miso 数据接收正确 |
| `test_spi_loopback` | mosi 直连 miso，发送 0xA5 | rx_data = 0xA5 |
| `test_fifo_basic` | 写入/读出 FIFO | tx_fifo_cnt/rx_fifo_cnt 正确 |

### 5.2 SPI 模式测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_spi_mode0` | CPOL=0, CPHA=0，发送多帧 | 每帧收发一致，sclk 空闲为低 |
| `test_spi_mode1` | CPOL=0, CPHA=1，发送多帧 | 每帧收发一致，采样边沿正确 |
| `test_spi_mode2` | CPOL=1, CPHA=0，发送多帧 | 每帧收发一致，sclk 空闲为高 |
| `test_spi_mode3` | CPOL=1, CPHA=1，发送多帧 | 每帧收发一致，采样边沿正确 |
| `test_spi_all_modes` | 随机切换 4 种模式 | 每种模式下收发正确 |

### 5.3 FIFO 和中断测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_tx_fifo_full` | 连续写 9 次 TXDATA | 第 9 次被忽略，tx_underrun=1 |
| `test_rx_fifo_full` | 连续接收 9 帧 | 第 9 帧丢失，rx_overrun=1 |
| `test_tx_empty_irq` | 使能 tx_empty_ie，发送完 FIFO 中数据 | irq 触发，is[tx_empty]=1 |
| `test_rx_full_irq` | 使能 rx_full_ie，接收 8 帧 | irq 触发，is[rx_full]=1 |
| `test_transfer_done_irq` | 使能 transfer_done_ie，发送 1 帧 | 每帧完成 irq 触发 |
| `test_irq_clear` | 触发中断后写 IS 清除 | irq 变低，is 对应位清零 |

### 5.4 帧格式和波特率测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_frame_len_4` | 4-bit 帧传输 | 只发送/接收低 4 位 |
| `test_frame_len_16` | 16-bit 帧传输 | 完整 16 位收发 |
| `test_frame_len_var` | 随机 4~16 位帧长度 | 每种长度收发正确 |
| `test_baud_1mhz` | spi_div=49，1MHz | sclk 周期 = 1us |
| `test_baud_10mhz` | spi_div=4，10MHz | sclk 周期 = 100ns |
| `test_baud_max` | spi_div=0，50MHz | sclk 周期 = 20ns |
| `test_baud_min` | spi_div=65535 | 功能正常，sclk 周期正确 |

### 5.5 片选测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_cs_auto` | 自动片选模式 | 传输时 cs_n=0，结束后 cs_n=1 |
| `test_cs_manual` | 手动片选模式 | 软件写 cs_val 直接控制 cs_n |
| `test_cs_slave_sel` | 切换 slave_sel 0~3 | 对应 cs_n 信号有效 |
| `test_cs_setup_hold` | 配置 cs_setup/cs_hold | 片选时序符合配置 |

### 5.6 边界测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_back_to_back_tx` | TX FIFO 有 8 帧数据 | 自动连续传输 8 帧 |
| `test_back_to_back_rx` | 连续接收 8 帧 | RX FIFO 正确存储 8 帧 |
| `test_reset_during_transfer` | 传输中复位 | 立即停止，cs_n=1，状态机回到 IDLE |
| `test_all_data_values` | 发送 0x0000~0xFFFF 所有值 | 每个值收发一致 |
| `test_apb_illegal_addr` | 访问非法地址 | 不报错，prdata=0 |

### 5.7 压力测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_random_cfg` | 随机 CPOL/CPHA/帧长/分频/从设备 | 1000 次随机配置下收发正确 |
| `test_long_run` | 连续发送 1000 帧 | 无丢包，无溢出 |
| `test_random_fifo` | 随机 APB 读写和 SPI 传输交错 | FIFO 状态正确，无数据丢失 |

## 6. 通过判据

### 6.1 必过条件 (P0)

- [ ] 所有 P0 功能点测试通过
- [ ] Line Coverage >= 100%
- [ ] Branch Coverage >= 100%
- [ ] FSM State/Transition Coverage = 100%
- [ ] 无仿真错误（$error / $fatal）
- [ ] 无时序违例（setup/hold 检查）

### 6.2 加分条件 (P1/P2)

- [ ] 所有 P1 功能点测试通过
- [ ] Toggle Coverage >= 95%
- [ ] 长时间压力测试（1000+ 帧）通过
- [ ] 随机测试（1000+ 次随机配置）通过

### 6.3 失败标准

以下任一情况即判定验证失败：
- 收发数据不一致
- SPI 时序不符合 CPOL/CPHA 配置
- FIFO 满/空标志错误
- 中断漏触发或误触发
- 状态机进入非法状态
- 复位后信号未回到初始值
- 代码覆盖率未达标

## 7. 仿真环境

### 7.1 工具链

| 工具 | 用途 | 版本 |
|------|------|------|
| Icarus Verilog | 编译 + 仿真 | v12+ |
| VVP | 仿真执行 | v12+ |
| GTKWave | 波形查看 | v3.4+ |
| Verilator | Lint 检查 | v5+ |

### 7.2 编译/仿真命令

```bash
# Lint
make lint TOP=spi

# Compile
make comp TOP=tb_spi

# Simulate
make sim TOP=tb_spi

# View waveforms
make wave TOP=tb_spi
```

### 7.3 仿真参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 仿真时间 | 10ms | 覆盖所有测试用例 |
| 时钟周期 | 10ns | 100MHz pclk |
| 时间精度 | 1ps | 足够分辨 SPI 时序 |

## 8. 测试进度跟踪

| 阶段 | 计划完成 | 状态 |
|------|----------|------|
| TB 搭建 | Day 1 | 待开始 |
| Smoke Test | Day 2 | 待开始 |
| SPI 模式测试 | Day 3 | 待开始 |
| FIFO/中断测试 | Day 4 | 待开始 |
| 边界/压力测试 | Day 5 | 待开始 |
| 覆盖率收敛 | Day 6 | 待开始 |
| 报告输出 | Day 7 | 待开始 |
