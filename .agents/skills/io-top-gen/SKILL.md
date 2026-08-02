---
name: io-top-gen
description: 从 Excel 配置生成 IO/Pad 相关 RTL（io_top、io_ring、pin_mux、SDC）。
---

# IO/Pad 生成

优先通过已注册 MCP 工具调用：

```text
io-top-gen.io_top_gen(excel_file=<path.xlsx>, output_dir=<out_dir>)
```

本地等价 CLI：

```bash
python3 .agents/skills/io-top-gen/scripts/io_top_gen.py <io_config.xlsx> <output_dir>/
```

从 Excel 生成 io_top、io_ring、pin_mux、SDC、寄存器文件等。

**增强功能**：
- 支持 `ds`/`st`/`sl`/`msc`/`ps`/`he`/`pe` 等 pad 控制字段
- 支持 DFT 模式、时钟域配置
- 生成 `IO_TOP.yml` 寄存器描述
- 自动生成 `IO_TOP_apb_regfile.v`（调用 `yml2reg.py`）
- 生成 SDC 约束、`io_check.csv`、TDR buffer 列表
- 自动生成 `io_top_top.v` / `io_top_top_model.v`（调用 `soc_build.py`）

Excel 模板：`references/io_top_demo.xlsx`

**约定**：
- 生成产物先落到模块 `de/run/io_top_gen/`，再整理进 `de/rtl/` / `de/syn/`。
- 不手写替代已批准 Excel 配置下的 pad/pin_mux 结构。

**pad_cfg sheet 关键字段**：
- `ds[msb:0]` / `st[msb:0]` / `sl[msb:0]` — 必须带位宽标记
- `pad_cell_type`：IOBUF、ANALOG、VREF、POC、INNO_GPIO 等

**pin_mux sheet 关键字段**：
- `drv` — 格式为 `3'b010`
- `type` — GPIO / PINMUX / ANALOG / VREF / POC
- `pu` / `pd` / `rx_smit` — 格式为 `1'b1` / `1'b0`
