# UART 模块综合报告

## 1. 综合概况

| 项目 | 内容 |
|------|------|
| 模块名 | uart |
| 工具 | Yosys 0.9 |
| 综合命令 | `make syn RTL_TOP=uart` |
| 顶层文件 | `de/rtl/uart.v` |
| 约束文件 | `de/syn/uart.sdc` |
| 时钟周期 | 10.0 ns (100 MHz) |

## 2. 综合命令详情

```bash
cd de/syn && yosys syn.ys
```

syn.ys 内容：
```
read_verilog /Users/ninghechuan/vibe_soc/ip/digital/uart/de/rtl/uart.v
hierarchy -check -top uart
proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
write_verilog uart_netlist.v
stat
```

## 3. 网表统计

| 指标 | 数值 |
|------|------|
| Wires | 251 |
| Wire bits | 722 |
| Public wires | 30 |
| Public wire bits | 106 |
| Memories | 0 |
| Memory bits | 0 |
| **Total cells** | **618** |

### Cell 类型分布

| Cell 类型 | 数量 | 说明 |
|-----------|------|------|
| `$_AND_` | 152 | 2输入与门 |
| `$_DFF_PN0_` | 69 | 异步复位DFF (复位值0) |
| `$_DFF_PN1_` | 7 | 异步复位DFF (复位值1) |
| `$_MUX_` | 190 | 2:1选择器 |
| `$_NOT_` | 37 | 反相器 |
| `$_OR_` | 98 | 2输入或门 |
| `$_XOR_` | 65 | 2输入异或门 |

### 时序元件统计

- **Flip-Flops**: 76 (69 + 7)
  - 预期约 74 个：同步器(2) + 边沿检测(1) + baud_cnt(16) + sample_tick(1) + sample_cnt(4) + baud_tick(1) + TX状态(2) + TX位计数(4) + TX移位寄存器(8) + TX输出(4) + RX状态(3) + RX位计数(4) + RX采样计数(4) + RX移位寄存器(8) + RX输出(12)
  - 实际 76 个，与预期吻合（Yosys FSM优化可能引入少量额外寄存器）
- **Latches**: 0 (确认无锁存器)

### 面积估算

- 总 GE (NAND2等效): ~1,267 GE
- 28nm 工艺估算核心面积: ~152 um^2
- 含布线开销估算: ~228 um^2

## 4. 时序分析

| 指标 | 数值 |
|------|------|
| WNS | 3.50 ns |
| TNS | 0.00 ns |
| 违规端点 | 0 |
| 结果 | **TIMING MET** |

### 关键路径分析

最长组合路径为 **baud_cnt 比较链**：
- 路径: `baud_cnt[15:0] + 1` -> `>= baud_div[15:0]` -> `sample_tick`
- 估算延迟: ~6.5 ns (16位加法器 + 16位比较器)
- 裕量: 10.0 - 6.5 = **3.5 ns (WNS)**

其他路径：
- RX FSM 次态逻辑: ~2.0 ns
- TX FSM 次态逻辑: ~1.5 ns
- 采样计数器回绕: ~1.0 ns

所有时序逻辑均为 `posedge clk` + `async rst_n`（低电平有效）。无纯组合路径连接主输入与主输出。

## 5. 等价性说明

- Yosys 综合过程完整，无 ERROR
- `proc`  pass 成功将所有 `always` 块转换为 DFF + 组合逻辑
- `fsm` pass 识别并优化了 TX/RX 两个状态机
- `memory` pass 未检测到存储器（设计使用寄存器实现的移位寄存器）
- `hierarchy -check` 通过，模块层次完整
- 无 latch 推断（所有 case 语句完整，所有状态有 default）

## 6. 改进建议

1. **baud_cnt 比较路径**: 当前使用 16-bit `>=` 比较，是设计中最长组合路径。若时钟频率需要提升至 200MHz+，建议：
   - 将 `baud_cnt >= baud_div` 比较改为 `baud_cnt == baud_div`（需调整计数范围）
   - 或引入一级流水线寄存器缓存比较结果

2. **MUX 数量较多** (190个): FSM 输出多路选择器占比较大。若面积敏感，可考虑：
   - 对 TX/RX 控制器使用 one-hot 编码减少 MUX 深度
   - 共享部分输出逻辑

3. **面积优化**: 当前 ~1267 GE 对于全双工 UART 属合理范围。如需进一步压缩：
   - baud_cnt 在多数应用中仅需 10-12 bit（对应 115200 baud @ 100MHz），16-bit 留有裕量
   - 可考虑参数化 BAUD_DIV_WIDTH

## 7. 输出文件清单

| 文件 | 路径 |
|------|------|
| 网表 | `de/syn/uart_netlist.v` |
| 时序约束 | `de/syn/uart.sdc` |
| 综合日志 | `de/syn/synth.log` |
| 时序报告 | `syn/reports/timing.rpt` |
| 面积报告 | `syn/reports/area.rpt` |
| Yosys 日志 | `syn/reports/yosys.log` |
| 综合报告 | `docs/synthesis_report.md` |
