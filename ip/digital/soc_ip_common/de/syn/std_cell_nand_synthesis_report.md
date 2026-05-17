# std_cell_nand 综合报告

## 1. 综合命令

```bash
cd /Users/ninghechuan/vibe_soc/ip/digital/soc_ip_common
make syn RTL_TOP=std_cell_nand
```

底层 Yosys 脚本(由 Makefile 自动生成 `de/syn/syn.ys`,内部展开如下):

```
read_verilog <full filelist (clk_divider, std_cell_*, rst_synchronizer)>
hierarchy -check -top std_cell_nand
proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
write_verilog std_cell_nand_netlist.v
stat
```

## 2. 工具版本

```
Yosys 0.9 (git sha1 UNKNOWN, clang 11.0.3 -fPIC -Os)
```

## 3. RTL 设计概要

- 文件:`de/rtl/std_cell/std_cell_nand.v`
- 功能:参数化位宽 NAND,`y = ~(a & b)`
- 默认参数:`WIDTH = 1`(本次综合按默认参数顶层化)
- 时序元素:无(纯组合)

## 4. stat 段落原文

```
=== std_cell_nand ===

   Number of wires:                  4
   Number of wire bits:              4
   Number of public wires:           3
   Number of public wire bits:       3
   Number of memories:               0
   Number of memory bits:            0
   Number of processes:              0
   Number of cells:                  2
     $_AND_                          1
     $_NOT_                          1
```

## 5. 单元清单

| 单元类型 | 数量 | 说明 |
|----------|------|------|
| `$_AND_` | 1    | generic AND2 |
| `$_NOT_` | 1    | generic INV   |
| 合计     | 2    | 与目标 `≤ 2` 一致 |

Yosys 0.9 在没有指定 `synth -top` 库的情况下,techmap 把 `~(a & b)` 拆成 `$_AND_` + `$_NOT_`,而不是直接合成 `$_NAND_`。在 ASIC techmap(`abc -liberty`)阶段会合并成单个 NAND2 标准单元,功能等价,不影响后端流程。

## 6. 时序

- 纯组合 NAND2,无寄存器路径
- 关键路径:`a / b -> $_AND_ -> $_NOT_ -> y`(2 级 generic 门)
- **WNS N/A**(纯组合无 endpoint,Yosys 0.9 也不做真实 STA;在 PnR 阶段以工艺库的 NAND2 cell delay 为准)

## 7. 检查结果

| 检查项         | 结果      |
|----------------|-----------|
| ERROR          | 0         |
| Latch          | 0         |
| Flip-Flop      | 0         |
| Process        | 0         |
| Memory         | 0         |
| 顶层 `hierarchy -check` | PASS |
| `write_verilog` | OK (`de/syn/std_cell_nand_netlist.v`) |

## 8. 结论

**综合 PASS**:0 latch、0 error,网表只含 1 `$_AND_` + 1 `$_NOT_`,与 RTL 功能等价,可进入后续 PnR/复用流程。

## 9. 产物

- 网表:`de/syn/std_cell_nand_netlist.v`
- 日志:`de/syn/synth.log`
- 报告:`de/syn/std_cell_nand_synthesis_report.md`
