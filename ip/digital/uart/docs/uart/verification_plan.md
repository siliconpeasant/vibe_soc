# uart Verification Plan

## 1. 验证范围

本验证计划覆盖 UART IP 的全部功能，包括：

- TX 发送器功能（8N1 帧格式、波特率分频、握手信号）
- RX 接收器功能（8N1 帧解析、16x 过采样、start bit 检测）
- 波特率生成器（分频精度、多种波特率支持）
- 错误检测（framing error）
- 复位行为
- 边界条件（最小/最大分频值、背靠背传输）

## 2. 功能点列表

### 2.1 TX 功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| TX-01 | 基本发送 | P0 | 发送单字节数据，验证 tx_out 波形符合 8N1 格式 |
| TX-02 | LSB first | P0 | 验证数据位从 LSB 到 MSB 依次发送 |
| TX-03 | Start/Stop bit | P0 | 验证 start bit = 0，stop bit = 1 |
| TX-04 | 波特率精度 | P0 | 验证各波特率下位周期误差在 ±2% 以内 |
| TX-05 | tx_ready 握手 | P0 | 验证 ready/valid 握手正确，忙时拒绝新数据 |
| TX-06 | tx_busy 标志 | P1 | 验证发送期间 busy = 1，空闲时 busy = 0 |
| TX-07 | tx_done 脉冲 | P1 | 验证发送完成后产生单周期 done 脉冲 |
| TX-08 | 连续发送 | P1 | 验证背靠背发送多字节，无数据丢失 |
| TX-09 | 全 0 / 全 1 数据 | P1 | 验证 0x00 和 0xFF 发送正确 |
| TX-10 | 复位后发送 | P1 | 验证复位后立即发送功能正常 |

### 2.2 RX 功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| RX-01 | 基本接收 | P0 | 接收单字节 8N1 数据，验证 rx_data 正确 |
| RX-02 | LSB first | P0 | 验证数据位按 LSB first 解析 |
| RX-03 | 16x 过采样 | P0 | 验证在每位中心点采样 |
| RX-04 | Start bit 检测 | P0 | 验证下降沿触发 + 半位确认机制 |
| RX-05 | Start bit 毛刺过滤 | P1 | 验证窄脉冲（< 半位时间）不触发接收 |
| RX-06 | rx_valid 脉冲 | P1 | 验证接收完成后产生单周期 valid 脉冲 |
| RX-07 | rx_busy 标志 | P1 | 验证接收期间 busy = 1 |
| RX-08 | Framing error | P0 | 验证 stop bit = 0 时 frame_err = 1 |
| RX-09 | 连续接收 | P1 | 验证背靠背接收多字节 |
| RX-10 | 全 0 / 全 1 数据 | P1 | 验证 0x00 和 0xFF 接收正确 |
| RX-11 | 波特率容忍度 | P1 | 验证 ±2% 波特率偏差下仍可正确接收 |

### 2.3 波特率生成功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| BR-01 | 分频精度 | P0 | 验证 baud_div 配置后位周期正确 |
| BR-02 | 常用波特率 | P0 | 验证 9600/19200/38400/57600/115200 |
| BR-03 | 边界分频值 | P1 | 验证 baud_div = 0 和 baud_div = 65535 |

### 2.4 集成/系统功能点

| ID | 功能点 | 优先级 | 描述 |
|----|--------|--------|------|
| SYS-01 | TX-RX 回环 | P0 | TX 输出直连 RX 输入，验证数据完整性 |
| SYS-02 | 复位验证 | P0 | 验证复位后所有信号处于正确初始状态 |
| SYS-03 | 随机数据 | P1 | 发送随机数据，验证收发一致 |
| SYS-04 | 长时间运行 | P2 | 连续发送 1000 字节，验证无丢包 |

## 3. 覆盖率目标

### 3.1 代码覆盖率

| 类型 | 目标 |
|------|------|
| Line Coverage | 100% |
| Branch Coverage | 100% |
| FSM State Coverage | 100%（TX 4 状态 + RX 5 状态） |
| FSM Transition Coverage | 100% |
| Toggle Coverage | 100%（所有端口和内部信号） |

### 3.2 功能覆盖率

| 覆盖点 | 目标 |
|--------|------|
| tx_data 值 | 所有 256 种数据值 |
| baud_div 值 | 至少覆盖 5 种常用波特率 + 2 种边界值 |
| TX 状态机状态 | 覆盖 TX_IDLE/START/DATA/STOP |
| RX 状态机状态 | 覆盖 RX_IDLE/START/DATA/STOP/DONE |
| Framing error | 覆盖 error = 0 和 error = 1 |
| 背靠背传输 | 覆盖连续发送/接收场景 |

## 4. Testbench 架构

```
+-----------------------------------------------------------+
|                      tb_uart (Top)                        |
|                                                           |
|  +------------------+        +------------------------+   |
|  |   uart_dut       |        |   Test Sequence        |   |
|  |   (DUT)          |<------>|   (task-based tests)   |   |
|  |                  |        |                        |   |
|  |  tx_out -------->|------->|  rx_in (loopback)      |   |
|  |  rx_in <---------|<-------|  tx_out (loopback)     |   |
|  |                  |        |                        |   |
|  +------------------+        +------------------------+   |
|           ^                            ^                  |
|           |                            |                  |
|  +------------------+        +------------------------+   |
|  |   Clock/Reset    |        |   Scoreboard/Checker   |   |
|  |   Generator      |        |   (auto check)         |   |
|  +------------------+        +------------------------+   |
|                                                           |
+-----------------------------------------------------------+
```

### 4.1 Testbench 组件

| 组件 | 描述 |
|------|------|
| `tb_uart.v` | Top-level testbench |
| `uart_dut` | 被测 UART 模块实例 |
| `clk_gen` | 100MHz 时钟生成（`#5` 翻转） |
| `rst_gen` | 复位生成（低电平有效，持续 100ns） |
| `uart_bfm` | UART 总线功能模型：发送/接收 8N1 帧的 task |
| `scoreboard` | 自动比对：发送数据 vs 接收数据 |

### 4.2 UART BFM 接口

```verilog
task uart_send_byte(input [7:0] data, input [15:0] div);
  // 按 8N1 格式在 rx_in 上产生串行波形
  // 位周期 = (div + 1) * 16 * clk_period
endtask

task uart_expect_byte(output [7:0] data, output frame_err);
  // 监控 tx_out，解析 8N1 帧，返回数据和错误标志
endtask
```

## 5. 测试用例

### 5.1 基础测试 (Smoke Tests)

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_tx_single_byte` | 发送单字节 0x55 | tx_out 波形正确，tx_done 产生 |
| `test_rx_single_byte` | 接收单字节 0xAA | rx_data = 0xAA，rx_valid 产生 |
| `test_loopback` | TX 输出直连 RX 输入，发送 0x55 | rx_data = 0x55，无 frame_err |

### 5.2 功能测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_all_data_values` | 发送 0x00 ~ 0xFF 所有值 | 每个值收发一致 |
| `test_all_baud_rates` | 在 5 种波特率下各发送 10 字节 | 收发一致，误差在范围内 |
| `test_back_to_back_tx` | 连续发送 10 字节 | 无数据丢失，tx_ready 正确 |
| `test_back_to_back_rx` | 连续接收 10 字节 | 无数据丢失，rx_valid 正确 |
| `test_frame_error` | 发送 stop bit = 0 的帧 | rx_frame_err = 1 |
| `test_glitch_rejection` | 在 rx_in 上发送窄脉冲 | 不触发接收 |

### 5.3 边界测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_min_div` | baud_div = 0 | 功能正常，位周期 = 16 clk |
| `test_max_div` | baud_div = 65535 | 功能正常 |
| `test_baud_tolerance` | ±2% 波特率偏差 | 接收正确 |

### 5.4 复位测试

| 用例名 | 描述 | 通过标准 |
|--------|------|----------|
| `test_reset_during_tx` | TX 发送中复位 | 立即回到 IDLE，tx_out = 1 |
| `test_reset_during_rx` | RX 接收中复位 | 立即回到 IDLE，rx_busy = 0 |
| `test_reset_after_done` | 完成后复位 | 所有信号回到初始值 |

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
- [ ] 长时间压力测试（1000+ 字节）通过

### 6.3 失败标准

以下任一情况即判定验证失败：
- 收发数据不一致
- framing error 漏检或误报
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
make lint TOP=uart

# Compile
make comp TOP=tb_uart

# Simulate
make sim TOP=tb_uart

# View waveforms
make verdi TOP_MODULE=tb_uart
```

### 7.3 仿真参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 仿真时间 | 10ms | 覆盖所有测试用例 |
| 时钟周期 | 10ns | 100MHz |
| 时间精度 | 1ps | 足够分辨波特率 tick |

## 8. 测试进度跟踪

| 阶段 | 计划完成 | 状态 |
|------|----------|------|
| TB 搭建 | Day 1 | 待开始 |
| Smoke Test | Day 2 | 待开始 |
| 功能测试 | Day 3-4 | 待开始 |
| 边界测试 | Day 5 | 待开始 |
| 覆盖率收敛 | Day 6 | 待开始 |
| 报告输出 | Day 7 | 待开始 |
