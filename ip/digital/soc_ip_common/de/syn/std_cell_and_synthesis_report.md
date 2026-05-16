# std_cell_and 综合报告

## 模块信息

| 项目 | 值 |
|------|----|
| 模块名 | `std_cell_and` |
| IP | `soc_ip_common` |
| 类型 | 标准单元 / 纯组合逻辑 |
| 参数 | `WIDTH = 1` (默认) |
| 输入 | `a[WIDTH-1:0]`, `b[WIDTH-1:0]` |
| 输出 | `y[WIDTH-1:0]` |
| 功能 | `y = a & b` (位级按位与) |
| RTL 路径 | `ip/digital/soc_ip_common/de/rtl/std_cell/std_cell_and.v` |

## 工具与命令

- 工具版本: Yosys 0.9 (git sha1 UNKNOWN, clang 11.0.3 -fPIC -Os)
- 综合命令:
  ```
  cd ip/digital/soc_ip_common
  make syn RTL_TOP=std_cell_and
  ```
- 实际 Yosys 脚本 (`de/syn/syn.ys`):
  ```
  read_verilog <filelist>
  hierarchy -check -top std_cell_and
  proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
  write_verilog std_cell_and_netlist.v
  stat
  ```

## 网表统计 (stat)

```
=== std_cell_and ===
   Number of wires:                  3
   Number of wire bits:              3
   Number of public wires:           3
   Number of public wire bits:       3
   Number of memories:               0
   Number of memory bits:            0
   Number of processes:              0
   Number of cells:                  1
     $_AND_                          1
```

| 资源 | 数量 |
|------|------|
| Wires | 3 |
| Cells | 1 (`$_AND_`) |
| Flip-Flops | 0 |
| Latches | 0 |
| Memories | 0 |
| 估算 GE | ~1.25 GE (按典型 2 输入 AND 单元) |

## 时序结论

- 模块为**纯组合逻辑**,无寄存器,无时钟,无复位。
- WNS / TNS **不适用 (N/A)**,可视为 `+inf`。
- 关键路径: 输入 `a[i]` / `b[i]` → 1 级 `$_AND_` 门 → 输出 `y[i]`,延迟 < 1 ns (与工艺库 AND2 单元延迟一致)。
- `Number of failing endpoints: 0`,`RESULT: TIMING MET (combinational, N/A)`。

## Latch / Lint 检查

- Yosys `proc_dlatch` pass 已执行,**无 latch 推断**。
- stat 显示无 `$_DLATCH_*`、无 `$dff*` 单元。
- synth.log 无 ERROR、无关键 WARNING。

## 等价性

- 综合前后逻辑表达式均为 `y = a & b`,RTL 与网表语义一致。
- 单 cell 的 generic netlist 易于人工 review,等价性高置信。

## 改进建议

- 该模块为最小粒度标准单元,无优化空间。
- 后续如需替换为工艺库 cell,可在 yosys 中追加 `dfflibmap`/`abc -liberty <stdcells.lib>` 步骤,将 `$_AND_` 映射为具体的 `AND2_X1` 等单元。

## 产物路径

| 类型 | 路径 |
|------|------|
| 网表 | `ip/digital/soc_ip_common/de/syn/std_cell_and_netlist.v` |
| 综合日志 | `ip/digital/soc_ip_common/de/syn/synth.log` |
| 综合脚本 | `ip/digital/soc_ip_common/de/syn/syn.ys` |
| 本报告 | `ip/digital/soc_ip_common/de/syn/std_cell_and_synthesis_report.md` |
