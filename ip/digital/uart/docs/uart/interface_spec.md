# uart Interface Spec

## 1. 端口列表

### 1.1 系统接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `clk` | Input | 1 | 系统时钟，典型 100MHz |
| `rst_n` | Input | 1 | 异步复位，低电平有效。异步 assert，同步 deassert |

### 1.2 TX 接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `tx_data` | Input | 8 | 待发送的并行数据 |
| `tx_valid` | Input | 1 | 发送请求，高电平有效。在 `tx_ready` 为 1 时置位可启动发送 |
| `tx_ready` | Output | 1 | 发送就绪，高电平表示可接收新数据 |
| `tx_busy` | Output | 1 | 发送忙标志，高电平表示正在发送 |
| `tx_done` | Output | 1 | 发送完成脉冲，高电平持续一个 `clk` 周期 |
| `tx_out` | Output | 1 | 串行 TX 输出，空闲时为高电平 |

### 1.3 RX 接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `rx_in` | Input | 1 | 串行 RX 输入，需外部连接 |
| `rx_data` | Output | 8 | 接收到的并行数据，在 `rx_valid` 为高时有效 |
| `rx_valid` | Output | 1 | 接收完成脉冲，高电平持续一个 `clk` 周期 |
| `rx_busy` | Output | 1 | 接收忙标志，高电平表示正在接收 |
| `rx_frame_err` | Output | 1 | 帧错误标志，stop bit 不为高时置位，与 `rx_valid` 同时有效 |

### 1.4 配置接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `baud_div` | Input | 16 | 波特率分频系数。`baud_tick_period = (baud_div + 1) * 16` 个系统时钟周期。典型值：9600bps@100MHz = 651 (0x28B) |

## 2. 参数定义

本模块采用硬编码参数（Verilog `parameter`），暂无可运行时配置参数。

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DATA_WIDTH` | 8 | 数据位宽，固定为 8 |
| `BAUD_DIV_WIDTH` | 16 | 波特率分频器位宽 |
| `OVERSAMPLE` | 16 | RX 过采样倍数，固定为 16 |

## 3. 时钟与复位

### 3.1 时钟

- **时钟域**：单一时钟域 `clk`
- **频率范围**：支持 1MHz ~ 200MHz+（受波特率精度限制）
- **占空比**：50%（典型）
- **时钟/复位:无**：本模块为时序逻辑模块，依赖 `clk` 和 `rst_n`

### 3.2 复位

- **类型**：异步 assert，同步 deassert（推荐）
- **极性**：低电平有效 (`rst_n`)
- **复位后状态**：
  - TX 状态机：TX_IDLE
  - RX 状态机：RX_IDLE
  - `tx_out` = 1（空闲高电平）
  - `tx_ready` = 1
  - `tx_busy` = 0
  - `rx_data` = 8'h00
  - `rx_valid` = 0
  - `rx_busy` = 0
  - `rx_frame_err` = 0
  - 所有内部计数器清零

## 4. 接口协议

### 4.1 TX 握手协议

TX 采用 ready/valid 握手：

```
Host                uart_tx
  |                     |
  |-- tx_data --------->|
  |-- tx_valid -------->|
  |<-- tx_ready --------| (ready = !busy)
  |                     |
  |<-- tx_done ---------| (1 cycle pulse when done)
```

- 当 `tx_ready == 1` 时，Host 可在同一时钟上升沿置 `tx_valid = 1` 并提供 `tx_data`
- `tx_busy` 在发送期间保持为高，发送完成后变低
- `tx_done` 在发送完成时产生一个时钟周期的高电平脉冲
- 若 `tx_valid` 在 `tx_ready == 0` 时置位，数据被忽略

### 4.2 RX 数据输出协议

RX 数据输出采用 valid 脉冲方式：

```
uart_rx               Host
  |                     |
  |<-- rx_in -----------|
  |                     |
  |-- rx_data --------->| (valid when rx_valid == 1)
  |-- rx_valid -------->| (1 cycle pulse)
  |-- rx_frame_err ---->| (valid when rx_valid == 1, if error)
```

- `rx_valid` 为单周期脉冲，表示 `rx_data` 有效
- `rx_frame_err` 与 `rx_valid` 同时有效，表示帧错误
- Host 应在 `rx_valid` 为高时采样 `rx_data` 和 `rx_frame_err`

### 4.3 波特率配置

- `baud_div` 为静态配置，建议在系统初始化时设置
- 更改 `baud_div` 应在 TX/RX 空闲时进行，避免传输中修改导致错误
- `baud_div` 最小有效值为 0（分频系数 = 1），最大值为 65535

## 5. 时序约束

### 5.1 Setup/Hold

| 信号 | Setup (ns) | Hold (ns) | 说明 |
|------|------------|-----------|------|
| `tx_data` | 2.0 | 0.5 | 相对 `clk` 上升沿 |
| `tx_valid` | 2.0 | 0.5 | 相对 `clk` 上升沿 |
| `baud_div` | 3.0 | 0.5 | 静态或变化缓慢 |
| `rx_in` | 2.0 | 0.5 | 经两级同步后内部使用 |

### 5.2 输出延迟

| 信号 | Max Delay (ns) | 说明 |
|------|----------------|------|
| `tx_out` | 2.0 | 相对 `clk` 上升沿 |
| `tx_ready` | 2.0 | 相对 `clk` 上升沿 |
| `tx_busy` | 2.0 | 相对 `clk` 上升沿 |
| `tx_done` | 2.0 | 相对 `clk` 上升沿 |
| `rx_data[7:0]` | 2.0 | 相对 `clk` 上升沿 |
| `rx_valid` | 2.0 | 相对 `clk` 上升沿 |
| `rx_busy` | 2.0 | 相对 `clk` 上升沿 |
| `rx_frame_err` | 2.0 | 相对 `clk` 上升沿 |

### 5.3 异步约束

- `rst_n`：异步输入，需约束为异步复位信号
- `rx_in`：外部异步输入，内部经过两级同步器处理

## 6. IO 电气特性

| 信号 | 类型 | 驱动能力 | 备注 |
|------|------|----------|------|
| `tx_out` | Output | 4mA | 推挽输出，连接外部 UART TX pad |
| `rx_in` | Input | - | 需外部上拉，内部同步处理 |

## 7. 信号真值表

### 7.1 TX 控制

| `rst_n` | `tx_valid` | `tx_ready` | `tx_busy` | 动作 |
|---------|------------|------------|-----------|------|
| 0 | X | 0 | 0 | 复位，所有输出归零/初始值 |
| 1 | 0 | 1 | 0 | 空闲，等待发送请求 |
| 1 | 1 | 1 | 1 | 开始发送，`tx_data` 锁存 |
| 1 | 1 | 0 | 1 | 发送中，忽略新请求 |
| 1 | 0 | 0 | 1 | 发送中 |

### 7.2 RX 状态

| `rst_n` | `rx_in` | `rx_busy` | `rx_valid` | 动作 |
|---------|---------|-----------|------------|------|
| 0 | X | 0 | 0 | 复位 |
| 1 | 1 | 0 | 0 | 空闲，等待 start bit |
| 1 | 0 | 1 | 0 | 检测到 start bit，开始接收 |
| 1 | X | 1 | 0 | 接收中 |
| 1 | X | 0 | 1 | 接收完成，输出数据 |
