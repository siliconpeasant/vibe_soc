# spi Register Map

## 概述

本 SPI Master 控制器通过 APB 总线提供完整的寄存器映射，支持配置、数据收发、状态查询和中断管理。所有寄存器为 32-bit 宽度，按字（4 字节）对齐寻址。

**基地址**：`0x000`（相对 APB 从设备基址）
**地址范围**：`0x000 ~ 0x01C`

## 寄存器列表

| Offset | Name | Type | Width | Description |
|--------|------|------|-------|-------------|
| 0x00 | CTRL | RW | 32 | 控制寄存器 |
| 0x04 | STATUS | RO | 32 | 状态寄存器 |
| 0x08 | BAUD | RW | 32 | 波特率分频寄存器 |
| 0x0C | TXDATA | WO | 32 | 发送数据寄存器（写操作推入 TX FIFO） |
| 0x10 | RXDATA | RO | 32 | 接收数据寄存器（读操作弹出 RX FIFO） |
| 0x14 | IE | RW | 32 | 中断使能寄存器 |
| 0x18 | IS | RW1C | 32 | 中断状态寄存器（写 1 清除） |
| 0x1C | FRAME | RW | 32 | 帧格式配置寄存器 |

---

## 寄存器详细定义

### CTRL — 控制寄存器 (Offset: 0x00)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 0 | en | RW | 0 | SPI 使能。1=使能 SPI 传输，0=禁用。写 0 会立即停止当前传输并复位 SPI 状态机 |
| 1 | cpol | RW | 0 | 时钟极性。0=空闲时 sclk 低电平，1=空闲时 sclk 高电平 |
| 2 | cpha | RW | 0 | 时钟相位。0=第一个边沿采样，1=第二个边沿采样 |
| 3 | cs_manual | RW | 0 | 片选手动模式。0=自动管理片选，1=软件手动控制 cs_n（通过 cs_val） |
| 4 | cs_val | RW | 1 | 手动模式下片选值。0=assert（低电平），1=deassert（高电平）。仅 cs_manual=1 时有效 |
| 7:5 | slave_sel | RW | 0 | 从设备选择。0~3 对应 cs_n[0]~cs_n[3]，4~7 保留 |
| 31:8 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- 修改 `cpol`、`cpha`、`slave_sel` 应在 SPI 空闲时进行
- `en` 从 1 变为 0 会软复位 SPI 控制器（不清除 FIFO）
- `cs_manual` 用于需要软件精确控制片选时序的场景（如某些 Flash 命令）

---

### STATUS — 状态寄存器 (Offset: 0x04)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 0 | tx_fifo_empty | RO | 1 | TX FIFO 空标志。1=空，0=非空 |
| 1 | tx_fifo_full | RO | 0 | TX FIFO 满标志。1=满，0=未满 |
| 2 | rx_fifo_empty | RO | 1 | RX FIFO 空标志。1=空，0=非空 |
| 3 | rx_fifo_full | RO | 0 | RX FIFO 满标志。1=满，0=未满 |
| 4 | busy | RO | 0 | SPI 传输忙标志。1=传输中，0=空闲 |
| 8:5 | tx_fifo_cnt | RO | 0 | TX FIFO 当前数据条数（0~8） |
| 12:9 | rx_fifo_cnt | RO | 0 | RX FIFO 当前数据条数（0~8） |
| 31:13 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- 所有状态位实时反映硬件状态
- `busy` 在 SPI 状态机非 IDLE 时为 1
- `tx_fifo_cnt` 和 `rx_fifo_cnt` 可直接用于流控

---

### BAUD — 波特率分频寄存器 (Offset: 0x08)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 15:0 | spi_div | RW | 0 | SPI 时钟分频系数。sclk 频率 = pclk / (2 * (spi_div + 1)) |
| 31:16 | reserved | RO | 0 | 保留，读为 0 |

**常用配置值**（@100MHz pclk）：

| spi_div | sclk 频率 | 说明 |
|---------|-----------|------|
| 0 | 50 MHz | 最高速 |
| 1 | 25 MHz | - |
| 4 | 10 MHz | - |
| 9 | 5 MHz | - |
| 49 | 1 MHz | - |
| 499 | 100 kHz | 最低速 |

**注意**：
- 修改 `spi_div` 应在 SPI 空闲时进行
- `spi_div` = 0 时 sclk 为 pclk 2 分频

---

### TXDATA — 发送数据寄存器 (Offset: 0x0C)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 15:0 | tx_data | WO | 0 | 待发送数据。写操作将数据推入 TX FIFO |
| 31:16 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- 写 TXDATA 会将数据推入 TX FIFO
- 若 TX FIFO 已满，写操作被忽略，并触发 TX_UNDERRUN 中断
- 实际发送位宽由 FRAME[frame_len] 决定，不足 16 位时高位被忽略

---

### RXDATA — 接收数据寄存器 (Offset: 0x10)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 15:0 | rx_data | RO | 0 | 接收到的数据。读操作从 RX FIFO 弹出数据 |
| 31:16 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- 读 RXDATA 会从 RX FIFO 弹出数据
- 若 RX FIFO 为空，读操作返回 0，不触发错误
- 实际接收位宽由 FRAME[frame_len] 决定，不足 16 位时高位补 0

---

### IE — 中断使能寄存器 (Offset: 0x14)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 0 | tx_empty_ie | RW | 0 | TX FIFO 空中断使能。1=使能，0=禁用 |
| 1 | rx_full_ie | RW | 0 | RX FIFO 满中断使能。1=使能，0=禁用 |
| 2 | tx_underrun_ie | RW | 0 | TX FIFO underrun 中断使能。1=使能，0=禁用 |
| 3 | rx_overrun_ie | RW | 0 | RX FIFO overrun 中断使能。1=使能，0=禁用 |
| 4 | transfer_done_ie | RW | 0 | 传输完成中断使能。1=使能，0=禁用 |
| 31:5 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- 中断使能位独立控制各中断源
- `irq` 输出 = OR(IE & IS)，即任一使能的中断源触发时 `irq` 变高

---

### IS — 中断状态寄存器 (Offset: 0x18)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 0 | tx_empty | RW1C | 0 | TX FIFO 空中断状态。写 1 清除 |
| 1 | rx_full | RW1C | 0 | RX FIFO 满中断状态。写 1 清除 |
| 2 | tx_underrun | RW1C | 0 | TX FIFO underrun 中断状态。写 1 清除 |
| 3 | rx_overrun | RW1C | 0 | RX FIFO overrun 中断状态。写 1 清除 |
| 4 | transfer_done | RW1C | 0 | 传输完成中断状态。写 1 清除 |
| 31:5 | reserved | RO | 0 | 保留，读为 0 |

**中断触发条件**：

| 中断位 | 触发条件 | 清除方式 |
|--------|----------|----------|
| tx_empty | TX FIFO 从非空变为空 | 写 1 清除 |
| rx_full | RX FIFO 从非满变为满 | 写 1 清除 |
| tx_underrun | TX FIFO 满时仍写 TXDATA | 写 1 清除 |
| rx_overrun | RX FIFO 满时仍接收数据 | 写 1 清除 |
| transfer_done | 一帧数据传输完成 | 写 1 清除 |

**注意**：
- 所有中断状态位为 RW1C（写 1 清除，写 0 无影响，读返回当前状态）
- 清除所有中断源后 `irq` 输出变为低电平

---

### FRAME — 帧格式配置寄存器 (Offset: 0x1C)

| Bit | Name | Type | Default | Description |
|-----|------|------|---------|-------------|
| 4:0 | frame_len | RW | 8 | 帧长度，范围 4~16。实际位宽 = frame_len |
| 7:5 | reserved | RO | 0 | 保留，读为 0 |
| 15:8 | cs_setup | RW | 1 | 片选建立时间，单位 sclk 周期数（默认 1） |
| 23:16 | cs_hold | RW | 1 | 片选保持时间，单位 sclk 周期数（默认 1） |
| 31:24 | reserved | RO | 0 | 保留，读为 0 |

**注意**：
- `frame_len` 最小值为 4，最大值为 16。写入值小于 4 按 4 处理，大于 16 按 16 处理
- 修改 `frame_len` 应在 SPI 空闲时进行
- `cs_setup` 和 `cs_hold` 控制片选时序，最小值为 1

---

## 寄存器地址汇总

```
Address Map (byte address):

0x000 +----------------+
      |     CTRL       |  RW
0x004 +----------------+
      |     STATUS     |  RO
0x008 +----------------+
      |     BAUD       |  RW
0x00C +----------------+
      |     TXDATA     |  WO
0x010 +----------------+
      |     RXDATA     |  RO
0x014 +----------------+
      |     IE         |  RW
0x018 +----------------+
      |     IS         |  RW1C
0x01C +----------------+
      |     FRAME      |  RW
0x020 +----------------+
      |   (reserved)   |
      +----------------+
```

## 配置示例

### 初始化 SPI（Mode 0, 1MHz, 8-bit 帧）

```c
// 1. 配置波特率：1MHz @ 100MHz pclk -> spi_div = 49
SPI_BAUD = 0x00000031;

// 2. 配置帧格式：8-bit，cs_setup=1, cs_hold=1
SPI_FRAME = 0x00010108;

// 3. 配置控制：Mode 0 (cpol=0, cpha=0)，选择从设备 0
SPI_CTRL = 0x00000001;  // en=1, cpol=0, cpha=0, slave_sel=0

// 4. 使能中断（可选）
SPI_IE = 0x00000011;  // tx_empty_ie=1, transfer_done_ie=1
```

### 发送数据

```c
// 等待 TX FIFO 非满
while (SPI_STATUS & 0x2);  // wait tx_fifo_full == 0

// 写入数据
SPI_TXDATA = 0x000000A5;

// 等待传输完成（轮询方式）
while (!(SPI_IS & 0x10));  // wait transfer_done
SPI_IS = 0x10;  // clear interrupt

// 读取接收数据（如果是全双工传输）
uint16_t rx = SPI_RXDATA & 0xFFFF;
```
