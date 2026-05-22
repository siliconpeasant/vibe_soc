# spi Design Spec

## 1. 概述

本文档描述 vibe_soc 项目中 SPI Master 控制器 IP 的设计规格。该模块提供 APB 总线接口的 SPI 主设备功能，支持标准 4 线 SPI 协议（sclk、mosi、miso、cs_n），可配置时钟极性/相位（CPOL/CPHA）、可编程波特率分频器、可变数据帧长度（4~16 位），并内置 8 深度 TX/RX FIFO 以及中断机制，适用于连接外部 SPI 从设备（如 Flash、传感器、ADC 等）。

## 2. 功能描述

### 2.1 顶层功能

- **APB 从接口**：标准 APB3/4 接口，用于寄存器读写访问
- **SPI 主设备**：生成 sclk 时钟，通过 mosi 发送数据，通过 miso 接收数据
- **片选管理**：支持最多 4 个从设备，通过 cs_n[3:0] 自动管理片选信号
- **可配置时钟**：可编程波特率分频器，支持多种 SPI 时钟速率
- **可配置帧格式**：CPOL（时钟极性）和 CPHA（时钟相位）可独立配置
- **可变数据宽度**：支持 4~16 位帧长度
- **FIFO 缓冲**：8 深度 TX FIFO 和 8 深度 RX FIFO，提高吞吐率
- **中断支持**：TX_EMPTY、RX_FULL、TX_UNDERRUN、RX_OVERRUN、TRANSFER_DONE

### 2.2 SPI 协议支持

#### 2.2.1 时钟极性 CPOL

- **CPOL = 0**：空闲时 sclk 为低电平
- **CPOL = 1**：空闲时 sclk 为高电平

#### 2.2.2 时钟相位 CPHA

- **CPHA = 0**：数据在 sclk 第一个边沿采样，第二个边沿改变
- **CPHA = 1**：数据在 sclk 第一个边沿改变，第二个边沿采样

#### 2.2.3 四种模式时序

```
Mode 0 (CPOL=0, CPHA=0):
            ____      ____      ____      ____      ____
sclk    ___/    \____/    \____/    \____/    \____/    \___
        idle   sample    sample    sample    sample   idle
mosi    ======|D15|=====|D14|=====|...|=====|D0|============
                 ↑         ↑                   ↑
               setup     setup               setup

Mode 1 (CPOL=0, CPHA=1):
            ____      ____      ____      ____      ____
sclk    ___/    \____/    \____/    \____/    \____/    \___
        idle   change    change    change    change   idle
mosi    ======|D15|=====|D14|=====|...|=====|D0|============
                    ↑         ↑                   ↑
                  sample    sample              sample

Mode 2 (CPOL=1, CPHA=0):
        ____      ____      ____      ____      ____      ____
sclk       \____/    \____/    \____/    \____/    \____/
        idle  sample    sample    sample    sample   idle
mosi    ======|D15|=====|D14|=====|...|=====|D0|============
                 ↑         ↑                   ↑
               setup     setup               setup

Mode 3 (CPOL=1, CPHA=1):
        ____      ____      ____      ____      ____      ____
sclk       \____/    \____/    \____/    \____/    \____/
        idle  change    change    change    change   idle
mosi    ======|D15|=====|D14|=====|...|=====|D0|============
                    ↑         ↑                   ↑
                  sample    sample              sample
```

**数据发送顺序**：MSB first（高位先发），与 UART 的 LSB first 不同。

### 2.3 波特率支持

系统时钟 100MHz 时，常用 SPI 时钟速率对应的分频值：

| SPI 时钟 | 分频值 (100MHz / sclk_freq / 2) | 实际 sclk | 误差 |
|----------|--------------------------------|-----------|------|
| 100 kHz  | 499 (0x1F3)                    | 100 kHz   | 0% |
| 1 MHz    | 49 (0x31)                      | 1 MHz     | 0% |
| 5 MHz    | 9 (0x09)                       | 5 MHz     | 0% |
| 10 MHz   | 4 (0x04)                       | 10 MHz    | 0% |
| 25 MHz   | 1 (0x01)                       | 25 MHz    | 0% |
| 50 MHz   | 0 (0x00)                       | 50 MHz    | 0% |

分频公式：`spi_div = (clk_freq / sclk_freq / 2) - 1`

sclk 为系统时钟 2 分频时达到最高速率（50MHz @ 100MHz clk）。

### 2.4 片选管理

- 传输开始时自动 assert 对应片选（cs_n[slave_sel] = 0）
- 传输结束后自动 deassert（cs_n[slave_sel] = 1）
- 片选建立时间（setup）和保持时间（hold）各为 1 个 sclk 周期
- 支持软件手动控制片选（通过寄存器配置）

## 3. 模块结构

```
                    +------------------------------------------+
    pclk, preset_n  |                                          |
         +--------->|              APB Slave Interface         |
    apb_*           |              (register access)           |
         +--------->|                                          |
                    +------------------+-----------------------+
                                       |
                    +------------------v-----------------------+
                    |                                          |
                    |              Register Block              |
                    |  CTRL  STATUS  BAUD  TXFIFO  RXFIFO      |
                    |  IE    IS     SLAVE  FRAME               |
                    +------------------+-----------------------+
                                       |
                    +------------------v-----------------------+
                    |                                          |
                    |           SPI Master Controller          |
                    |                                          |
    +-------------> |  +----------------+   +--------------+  |
    |               |  |  Baud Rate Gen |   |   TX FIFO    |  |
    |               |  |  (clock div)   |   |   (8-depth)  |  |
    |               |  +--------+-------+   +------+-------+  |
    |               |           |                  |          |
    |               |  +--------v-------+   +------v-------+  |
    |               |  |  SPI Shift Reg |<--|  TX Shift    |  |
    |               |  |  (MSB first)   |   |  Controller  |  |
    |               |  +--------+-------+   +--------------+  |
    |               |           |                             |
    |               |  +--------v-------+   +--------------+  |
    |               |  |  RX Shift Reg  |-->|   RX FIFO    |  |
    |               |  |  (MSB first)   |   |   (8-depth)  |  |
    |               |  +--------+-------+   +--------------+  |
    |               |           |                             |
    |               |  +--------v-------+                     |
    |               |  |   CS Manager   |                     |
    |               |  |  (auto/manual) |                     |
    |               |  +--------+-------+                     |
    |               |                                          |
    |               +------------------------------------------+
    |                          |
    |               +----------+----------+
    |               |                     |
    |          sclk | cs_n[3:0]       mosi| miso
    |               |                     |
    +---------------+                     +------------------->
```

## 4. 子模块详细设计

### 4.1 APB Slave Interface

- 支持 APB3/4 协议（无 PREADY/PSLVERR 延迟，即零等待状态）
- 寄存器地址映射：见 `regmap.md`
- 写操作：PSEL & PENABLE & PWRITE 时，PWDATA 写入对应寄存器
- 读操作：PSEL & PENABLE & !PWRITE 时，PRDATA 返回对应寄存器值
- 所有寄存器为 32-bit 宽度，APB 数据宽度 32-bit

### 4.2 Baud Rate Generator

- 输入：`pclk`, `preset_n`, `spi_div[15:0]`（来自 BAUD 寄存器）
- 输出：`sclk_tick`（sclk 半周期 tick）
- 功能：对系统时钟进行分频，产生 sclk 的半周期 tick
- 实现：一个 16-bit 计数器，计数到 `spi_div` 时翻转 sclk 并回零

**时序**：
- `spi_div = 0`：sclk 为 pclk 的 2 分频（最高速）
- `spi_div = N`：sclk 周期 = 2 * (N + 1) * pclk 周期

### 4.3 TX FIFO

- 深度：8 条目
- 宽度：16-bit（支持最大帧长度）
- 接口：APB 侧写（TXDATA 寄存器），SPI 控制器侧读
- 状态信号：tx_fifo_empty、tx_fifo_full、tx_fifo_cnt[3:0]
- 写满后再写触发 TX_UNDERRUN 中断（实际为 overflow，但命名沿用）

### 4.4 RX FIFO

- 深度：8 条目
- 宽度：16-bit
- 接口：SPI 控制器侧写，APB 侧读（RXDATA 寄存器）
- 状态信号：rx_fifo_empty、rx_fifo_full、rx_fifo_cnt[3:0]
- 读空后再读返回 0，不触发错误
- 满后再写触发 RX_OVERRUN 中断

### 4.5 SPI Shift Controller

**核心功能**：
- 从 TX FIFO 读取数据，按 MSB first 移出到 mosi
- 从 miso 采样数据，按 MSB first 移入到 RX shift reg
- 根据 CPOL/CPHA 配置控制 sclk 边沿和采样时机
- 管理传输状态（idle / active / done）

**移位逻辑**：
- `tx_shift_reg[15:0]`：从 TX FIFO 加载，MSB 移出到 mosi
- `rx_shift_reg[15:0]`：从 miso 采样，MSB 移入
- `bit_cnt[4:0]`：已传输 bit 计数（0 ~ frame_len-1）
- `frame_len[4:0]`：帧长度，来自 FRAME 寄存器（4~16）

**CPOL/CPHA 处理**：

| CPOL | CPHA | sclk 空闲 | 数据改变边沿 | 数据采样边沿 |
|------|------|-----------|-------------|-------------|
| 0    | 0    | 低        | 下降沿      | 上升沿      |
| 0    | 1    | 低        | 上升沿      | 下降沿      |
| 1    | 0    | 高        | 上升沿      | 下降沿      |
| 1    | 1    | 高        | 下降沿      | 上升沿      |

### 4.6 CS Manager

- **自动模式**（默认）：传输开始时 assert cs_n，传输结束后 deassert
- **手动模式**：软件通过寄存器直接控制 cs_n 值
- 建立时间：cs_n assert 后至少 1 个 sclk 周期才开始第一个 sclk 边沿
- 保持时间：最后一个 sclk 边沿后至少 1 个 sclk 周期才 deassert cs_n

## 5. 时序图

### 5.1 APB 写时序

```
pclk        ____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____

paddr       =====|ADDR|====================================|ADDR|===========
                 ↑setup                                    ↑setup
penable     ___________/‾‾‾‾\______________________________/‾‾‾‾\__________

psel        _______/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

pwrite      _______/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

pwdata      =====|DATA|====================================|DATA|===========

prdata      ====================|X|=================================|X|=====
                                 (don't care)                       (don't care)
```

### 5.2 SPI Mode 0 传输时序（CPOL=0, CPHA=0）

```
pclk        ____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____

sclk        _____________/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\_______________
              idle       ↑sample  ↑sample  ↑sample  ↑sample   idle
                         change   change   change   change

cs_n[0]     ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
            _______/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

mosi        ===========|D15|=====|D14|=====|D13|=====|...|=====|D0|========
                          ↑setup  ↑setup    ↑setup

miso        ===========|X15|=====|X14|=====|X13|=====|...|=====|X0|========
                          ↑sample ↑sample   ↑sample
```

### 5.3 中断时序

```
pclk        ____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____/‾‾‾‾\____

spi_active  ___________/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
            (transfer starts)                                    (transfer done)

tx_fifo_cnt ======|8|=======|7|=======|6|=======...=======|0|===============
                                                         (TX_EMPTY)

is[tx_empty]____________________________________________/‾‾‾‾\_____________

is[tx_done] __________________________________________________________/‾‾‾‾\_
```

## 6. 设计要点

### 6.1 关键假设

1. **系统时钟**：默认 100MHz，通过 `spi_div` 参数化支持其他频率
2. **复位策略**：`preset_n` 为异步 assert、同步 deassert
3. **APB 时钟域**：所有逻辑在 `pclk` 单一时钟域，无跨时钟域问题
4. **FIFO 实现**：使用标准 dual-port SRAM 或寄存器堆实现
5. **MSB first**：SPI 标准传输顺序为 MSB first，与 UART 的 LSB first 不同
6. **片选建立/保持**：固定 1 个 sclk 周期，不可配置
7. **最大帧长度**：16 位，最小 4 位
8. **从设备数量**：固定 4 个（cs_n[3:0]），通过 slave_sel 寄存器选择

### 6.2 面积与延时估计

- 预估门数：~3000 等效门（含 FIFO）
- APB 接口关键路径：PADDR 解码 -> 寄存器读写 -> PRDATA 输出，单周期完成
- SPI 关键路径：sclk_tick -> 状态机 -> mosi 输出，单周期完成
- 最高系统时钟：100MHz 在 28nm 以下无压力
- FIFO 面积：8x16 TX + 8x16 RX ≈ 256 bit SRAM

### 6.3 低功耗考虑

- 模块本身无时钟门控（ICG），由上层 SoC 控制 `pclk` 使能
- SPI 空闲时 sclk 保持恒定（由 CPOL 决定），无动态翻转
- 可通过 CTRL 寄存器禁用 SPI 功能（soft reset）

## 7. 验证要点

- 各 CPOL/CPHA 模式下的 SPI 传输正确性
- 各种波特率下的时钟精度
- FIFO 满/空边界条件
- 中断触发和清除
- 片选自动/手动管理
- 不同帧长度（4~16 位）
- 多从设备切换
- APB 寄存器读写
- 复位后状态正确性

## 8. 综合约束

- 目标频率：100MHz（`create_clock -period 10 [get_ports pclk]`）
- 输入延迟：`set_input_delay -clock pclk 2.0 [get_ports {apb_* miso}]`
- 输出延迟：`set_output_delay -clock pclk 2.0 [get_ports {sclk mosi cs_n[*]}]`
- 异步输入：`set_false_path -from [get_ports preset_n]`
- `sclk`、`mosi`、`miso`、`cs_n` 为外部 IO，需约束驱动强度/负载

## 9. 状态机

### 9.1 SPI Master 主状态机

```
         +-----------+
         |   IDLE    |<-------------------------------------+
         +-----------+                                      |
              | ctrl_en & !tx_fifo_empty                   |
              v                                            |
         +-----------+     cs_setup_done                   |
         |  CS_SETUP |----------------------------------->|
         +-----------+                                    |
              |                                           |
              v                                           |
    +------------------+                                  |
    |     TRANSFER     |<----------------------------+    |
    |  (shift in/out)  |     bit_cnt < frame_len    |    |
    +------------------+----------------------------+    |
         | bit_cnt == frame_len & sclk_edge             |
         v                                              |
    +------------------+                                |
    |    CS_HOLD       |                                |
    |  (cs hold time)  |--------------------------------+
    +------------------+     cs_hold_done               |
         |                                              |
         v                                              |
    +------------------+                                |
    |     DONE         |--------------------------------+
    | (set irq, load   |
    |  next if any)    |
    +------------------+
```

**状态定义**：

| 状态 | 编码 | 描述 |
|------|------|------|
| SPI_IDLE | 3'b000 | 空闲，等待传输启动 |
| SPI_CS_SETUP | 3'b001 | 片选建立，等待 setup 时间 |
| SPI_TRANSFER | 3'b010 | 数据传输中，移位寄存器工作 |
| SPI_CS_HOLD | 3'b011 | 片选保持，等待 hold 时间 |
| SPI_DONE | 3'b100 | 传输完成，触发中断，准备下一帧 |

### 9.2 FIFO 状态

TX FIFO 和 RX FIFO 各自维护独立的状态：

| 状态 | 条件 |
|------|------|
| EMPTY | fifo_cnt == 0 |
| NOT_EMPTY | 0 < fifo_cnt < 8 |
| FULL | fifo_cnt == 8 |

## 10. 寄存器映射

参见 `regmap.md`。本模块包含完整的寄存器映射表，通过 APB 接口访问。
