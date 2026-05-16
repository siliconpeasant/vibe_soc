# std_cell_icg 综合报告

## 模块信息

| 项目 | 值 |
|------|----|
| 模块名 | `std_cell_icg` |
| IP | `soc_ip_common` |
| 类型 | 标准单元 / 时钟门控 (含 latch) |
| 输入 | `clk`, `en`, `test_en` |
| 输出 | `gated_clk` |
| 功能 | Positive-edge ICG: active-low transparent latch 锁存 `en \| test_en`, AND 门产生 `gated_clk = clk & en_latch` |
| RTL 路径 | `ip/digital/soc_ip_common/de/rtl/std_cell/std_cell_icg.v` |

## 工具与命令

- 工具版本: Yosys 0.9 (git sha1 UNKNOWN, clang 11.0.3 -fPIC -Os)
- 综合命令:
  ```
  cd ip/digital/soc_ip_common
  make syn RTL_TOP=std_cell_icg
  ```
- 实际 Yosys 脚本 (`de/syn/syn.ys`):
  ```
  read_verilog <filelist>
  hierarchy -check -top std_cell_icg
  proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
  write_verilog std_cell_icg_netlist.v
  stat
  ```

## 网表统计 (stat)

```
=== std_cell_icg ===
   Number of wires:                  7
   Number of wire bits:              7
   Number of public wires:           5
   Number of public wire bits:       5
   Number of memories:               0
   Number of memory bits:            0
   Number of processes:              0
   Number of cells:                  4
     $_AND_                          1
     $_DLATCH_P_                     1
     $_NOT_                          1
     $_OR_                           1
```

| 资源 | 数量 |
|------|------|
| Wires | 7 |
| Cells | 4 |
| Flip-Flops | 0 |
| Latches | 1 (`$_DLATCH_P_`) |
| Memories | 0 |
| 估算 GE | ~3.5 GE (1x AND + 1x OR + 1x NOT + 1x latch) |

## 时序结论

- 模块为**时钟门控单元**,无时钟寄存器,无时序约束文件。
- WNS / TNS **不适用 (N/A)**。ICG 的时序特性由工艺库 latch 单元的 setup/hold 决定,不在综合阶段评估。
- 关键路径: `en`/`test_en` → `$_OR_` → `$_DLATCH_P_` → `$_AND_` → `gated_clk`。
- `Number of failing endpoints: 0`, `RESULT: TIMING MET (ICG, N/A)`。

## Latch / Lint 检查

- Yosys `proc_dlatch` pass 正确**推断 1 个 latch** (`$_DLATCH_P_`),这是 ICG 的标准结构。
- 综合日志无 ERROR、无关键 WARNING。
- RTL 的 `always @(*)` + `if (!clk)` 结构正确映射为 `$_DLATCH_P_`。

## 等价性

- 综合前后逻辑等价: `gated_clk = clk & latch(en | test_en)`。
- 网表结构清晰,RTL 与网表语义一致。

## 产物路径

| 类型 | 路径 |
|------|------|
| 网表 | `ip/digital/soc_ip_common/de/syn/std_cell_icg_netlist.v` |
| 综合日志 | `ip/digital/soc_ip_common/de/syn/synth.log` |
| 综合脚本 | `ip/digital/soc_ip_common/de/syn/syn.ys` |
| 本报告 | `ip/digital/soc_ip_common/de/syn/std_cell_icg_synthesis_report.md` |
