# spi Interface Spec

## 1. 端口列表

### 1.1 系统接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `pclk` | Input | 1 | APB 时钟，典型 100MHz |
| `preset_n` | Input | 1 | 异步复位，低电平有效。异步 assert，同步 deassert |

### 1.2 APB 从接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `paddr` | Input | 12 | APB 地址总线，字节寻址（实际使用 [7:0]） |
| `pwdata` | Input | 32 | APB 写数据总线 |
| `prdata` | Output | 32 | APB 读数据总线 |
| `pwrite` | Input | 1 | APB 读写方向，1=写，0=读 |
| `psel` | Input | 1 | APB 片选，高电平有效 |
| `penable` | Input | 1 | APB 使能，高电平有效 |

### 1.3 SPI 接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `sclk` | Output | 1 | SPI 时钟输出 |
| `mosi` | Output | 1 | Master Out Slave In，数据输出 |
| `miso` | Input | 1 | Master In Slave Out，数据输入 |
| `cs_n` | Output | 4 | 片选输出，低电平有效，支持 4 个从设备 |

### 1.4 中断接口

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `irq` | Output | 1 | 中断请求，高电平有效，电平触发 |

## 2. 参数定义

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DATA_WIDTH` | 16 | 最大数据位宽，固定为 16 |
| `FIFO_DEPTH` | 8 | TX/RX FIFO 深度 |
| `FIFO_CNT_WIDTH` | 4 | FIFO 计数器位宽（log2(FIFO_DEPTH)+1） |
| `APB_ADDR_WIDTH` | 12 | APB 地址宽度 |
| `APB_DATA_WIDTH` | 32 | APB 数据宽度 |
| `NUM_SLAVES` | 4 | 支持的从设备数量 |
| `SPI_DIV_WIDTH` | 16 | SPI 波特率分频器位宽 |

## 3. 时钟与复位

### 3.1 时钟

- **时钟域**：单一时钟域 `pclk`
- **频率范围**：支持 1MHz ~ 200MHz+（受 SPI 波特率精度限制）
- **占空比**：50%（典型）
- `sclk` 由内部波特率生成器产生，最高为 `pclk` 的 2 分频

### 3.2 复位

- **类型**：异步 assert，同步 deassert（推荐）
- **极性**：低电平有效 (`preset_n`)
- **复位后状态**：
  - SPI 状态机：SPI_IDLE
  - `sclk` = CPOL（由 CTRL 寄存器决定，默认 0）
  - `mosi` = 0
  - `cs_n` = 4'b1111（所有片选无效）
  - `irq` = 0
  - TX/RX FIFO：清空
  - 所有寄存器回到默认值（见 regmap.md）
  - 所有内部计数器清零

## 4. 接口协议

### 4.1 APB 读写协议

APB 为零等待状态从设备：

```
Host (APB Master)          spi (APB Slave)
  |                              |
  |-- paddr[11:0] -------------->|
  |-- pwrite ------------------->|
  |-- pwdata[31:0] ------------->| (if write)
  |-- psel --------------------->|
  |                              |
  |-- penable ------------------>|
  |<-- prdata[31:0] -------------| (if read)
  |                              |
```

- Setup 阶段（T1）：PSEL=1, PENABLE=0, PADDR/PWRITE/PWDATA 有效
- Access 阶段（T2）：PSEL=1, PENABLE=1, PRDATA 返回读数据
- 写操作在 T2 上升沿锁存 PWDATA
- 读操作在 T2 上升沿驱动 PRDATA

### 4.2 SPI 传输协议

SPI 传输由软件通过寄存器控制启动：

```
Software                  spi_master
  |                           |
  |-- write TXDATA ---------->| (push to TX FIFO)
  |-- write CTRL[en]=1 ----->| (enable transfer)
  |                           |
  |                           |-- cs_n[sel] = 0
  |                           |-- sclk toggles
  |                           |-- mosi shifts out
  |                           |-- miso shifts in
  |                           |
  |                           |-- transfer done
  |                           |-- cs_n[sel] = 1
  |                           |-- irq = 1 (if enabled)
  |                           |
  |-- read RXDATA ---------->| (pop from RX FIFO)
  |-- read IS --------------->| (check interrupt status)
  |-- write IS -------------->| (clear interrupts)
```

### 4.3 中断协议

`irq` 为电平触发中断信号：

```
spi_master                Interrupt Controller
  |                           |
  |-- irq ------------------->| (level high)
  |                           |   |
  |                           |   v
  |                           | (ISR entry)
  |                           |   |
  |                           |-- read IS
  |<-- read IS ---------------|
  |-- write IS (clear) ------>| (irq goes low)
```

- `irq` 在任一使能的中断源触发时变为高电平
- 软件通过读取 IS（Interrupt Status）寄存器了解中断源
- 通过向 IS 寄存器对应位写 1 清除中断（W1C 方式）
- 清除所有中断源后 `irq` 变为低电平

## 5. 时序约束

### 5.1 Setup/Hold

| 信号 | Setup (ns) | Hold (ns) | 说明 |
|------|------------|-----------|------|
| `paddr[11:0]` | 2.0 | 0.5 | 相对 `pclk` 上升沿 |
| `pwdata[31:0]` | 2.0 | 0.5 | 相对 `pclk` 上升沿 |
| `pwrite` | 2.0 | 0.5 | 相对 `pclk` 上升沿 |
| `psel` | 2.0 | 0.5 | 相对 `pclk` 上升沿 |
| `penable` | 2.0 | 0.5 | 相对 `pclk` 上升沿 |
| `miso` | 5.0 | 0.5 | 相对 `sclk` 采样沿，需考虑外部从设备延迟 |

### 5.2 输出延迟

| 信号 | Max Delay (ns) | 说明 |
|------|----------------|------|
| `prdata[31:0]` | 2.0 | 相对 `pclk` 上升沿 |
| `sclk` | 2.0 | 相对 `pclk` 上升沿（内部生成） |
| `mosi` | 2.0 | 相对 `sclk` 改变沿 |
| `cs_n[3:0]` | 2.0 | 相对 `pclk` 上升沿 |
| `irq` | 2.0 | 相对 `pclk` 上升沿 |

### 5.3 SPI 时序参数

| 参数 | 符号 | 最小 | 典型 | 最大 | 单位 |
|------|------|------|------|------|------|
| SCLK 周期 | t_sclk | 20 | - | - | ns (@ spi_div=0, 100MHz pclk) |
| SCLK 高电平 | t_high | 10 | - | - | ns |
| SCLK 低电平 | t_low | 10 | - | - | ns |
| CS 建立时间 | t_css | 1*sclk | - | - | period |
| CS 保持时间 | t_csh | 1*sclk | - | - | period |
| MOSI 建立时间 | t_setup | 5 | - | - | ns（相对采样沿） |
| MISO 保持时间 | t_hold | 0 | - | - | ns |

### 5.4 异步约束

- `preset_n`：异步输入，需约束为异步复位信号
- `miso`：外部异步输入，内部经过同步器处理（若需要）

## 6. IO 电气特性

| 信号 | 类型 | 驱动能力 | 备注 |
|------|------|----------|------|
| `sclk` | Output | 4mA | 推挽输出，连接外部 SPI SCLK |
| `mosi` | Output | 4mA | 推挽输出，连接外部 SPI MOSI |
| `miso` | Input | - | 需外部驱动，内部同步处理 |
| `cs_n[3:0]` | Output | 4mA | 推挽输出，连接外部 SPI CS |

## 7. 信号真值表

### 7.1 APB 写操作

| `preset_n` | `psel` | `penable` | `pwrite` | 动作 |
|------------|--------|-----------|----------|------|
| 0 | X | X | X | 复位，所有输出归零/初始值 |
| 1 | 0 | X | X | 未选中，无操作 |
| 1 | 1 | 0 | 1 | Setup 阶段，准备写 |
| 1 | 1 | 1 | 1 | Access 阶段，锁存 PWDATA 到寄存器 |
| 1 | 1 | 0 | 0 | Setup 阶段，准备读 |
| 1 | 1 | 1 | 0 | Access 阶段，驱动 PRDATA |

### 7.2 SPI 传输控制

| `preset_n` | `ctrl_en` | `tx_fifo_empty` | `spi_state` | 动作 |
|------------|-----------|-----------------|-------------|------|
| 0 | X | X | SPI_IDLE | 复位 |
| 1 | 0 | X | SPI_IDLE | 空闲，不启动传输 |
| 1 | 1 | 1 | SPI_IDLE | 使能但 TX FIFO 空，等待数据 |
| 1 | 1 | 0 | SPI_IDLE -> SPI_CS_SETUP | 启动传输 |
| 1 | X | X | SPI_TRANSFER | 传输中 |
| 1 | X | X | SPI_DONE | 传输完成，可触发下一帧 |
