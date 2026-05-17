# rstn_test_mux Release Notes

## 概述

`rstn_test_mux` 是 SoC 复位树中的测试模式多路选择器(reset test mode multiplexer)。在 DFT 流程中,功能复位(`rst_n`)与测试复位(`test_rst_n`)需要分离:正常工作时使用功能复位,scan / ATPG 测试模式下切换到测试复位,以保证测试向量对复位端的可控性。本模块通过 `test_mode` 信号在两路低有效复位之间进行选择,输出 `rst_n_out`。

本模块为纯组合逻辑,内部例化 `std_cell_mux #(WIDTH=1)` 实现选择功能,无时钟、无寄存器、无状态机。

## 变更日志

### v1.0.0 (2026-05-17)
- 初版发布
- 实现 rstn_test_mux 模块:2-to-1 复位多路选择器
- 完成设计文档(design_spec, interface_spec, regmap, verification_plan)
- 完成 RTL 设计与仿真验证(40/40 PASS)
- 完成逻辑综合,生成 netlist 与综合报告
- 通过 release 完整性检查

## 交付物

| 类别 | 文件路径 | 说明 |
|------|----------|------|
| RTL | `rtl/rstn_test_mux.v` | 模块 RTL 源码 |
| RTL | `rtl/rtl.f` | 文件列表 |
| TB | `tb/rstn_test_mux_tb.v` | 测试平台源码 |
| Doc | `docs/design_spec.md` | 设计规格书 |
| Doc | `docs/interface_spec.md` | 接口规格书 |
| Doc | `docs/regmap.md` | 寄存器映射(本模块无寄存器) |
| Doc | `docs/verification_plan.md` | 验证计划 |
| Doc | `docs/synthesis_report.md` | 综合报告 |
| Syn | `syn/netlist.v` | 综合后网表 |
| Syn | `syn/final.sdc` | 最终时序约束 |
| Syn | `syn/timing.rpt` | 时序分析报告 |
| Syn | `syn/area.rpt` | 面积分析报告 |
| Constraints | `constraints/base.sdc` | 基础约束文件 |
| Meta | `checksums.txt` | SHA256 校验和 |
| Meta | `manifest.yaml` | 文件清单 |
| Meta | `RELEASE_NOTES.md` | 本文件 |

## 验证状态

| 验证项 | 工具 | 结果 |
|--------|------|------|
| 功能仿真 | Icarus Verilog | 40/40 PASS |
| Lint | Verilator --lint-only | 无 error,无 warning |
| 逻辑综合 | Yosys 0.9 | PASS,无 latch,1 cell ($_MUX_) |
| 时序 | Yosys stat | TIMING MET (~0.15 ns < 2.0 ns) |

## 使用说明

### 模块例化

```verilog
rstn_test_mux u_rstn_test_mux (
    .rst_n       (sys_rst_n),
    .test_rst_n  (scan_rst_n),
    .test_mode   (dft_test_mode),
    .rst_n_out   (core_rst_n_selected)
);
```

### 级联 rst_synchronizer 的典型用法

```verilog
wire core_rst_n_muxed;

rstn_test_mux u_rstn_test_mux (
    .rst_n       (sys_rst_n),
    .test_rst_n  (scan_rst_n),
    .test_mode   (dft_test_mode),
    .rst_n_out   (core_rst_n_muxed)
);

rst_synchronizer #(
    .STAGES (2)
) u_rst_sync (
    .clk         (core_clk),
    .rst_async_n (core_rst_n_muxed),
    .rst_sync_n  (core_rst_n)
);
```

### 仿真运行

```bash
cd ip/digital/soc_ip_common
make sim RTL_TOP=rstn_test_mux
```

### 综合运行

```bash
cd ip/digital/soc_ip_common
make syn RTL_TOP=rstn_test_mux
```

## 已知问题

无。
