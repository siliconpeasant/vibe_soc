---
name: crg-gen
description: 从 Excel 配置生成 CRG（时钟复位生成）RTL 和 SDC 约束。
---

# CRG 生成

优先通过已注册 MCP 工具调用：

```text
crg-gen.crg_gen(excel_file=<path.xlsx>, output_dir=<out_dir>)
```

本地等价 CLI：

```bash
python3 .agents/skills/crg-gen/scripts/crg_gen.py <crg_config.xlsx> <output_dir>/
```

从 Excel 配置生成时钟复位模块和 SDC 约束。

**输入**：Excel（含 `top_info`、`clk_gen`、`rst_gen`、`user_defined_reg`、`user_code`、`user_defined_intp`、`user_sdc` sheet）

**输出**：
- `<name>_clk_gen.v` — 时钟生成
- `<name>_rst_gen.v` — 复位生成
- `<name>_crg_top.v` — CRG 顶层
- `<name>_crg_top.csv` — 连接关系（自动调用 `soc_build.py`）
- `<name>_crg.yml` / `<name>_crg_apb_regfile.v` — 寄存器（自动调用 `yml2reg.py`）
- `.sdc` — 约束文件（若配置提供）

**约定**：
- 生成产物先落到模块 `de/run/crg_gen/`（或任务约定目录），再整理进 `de/rtl/` / `de/syn/`。
- 不手写替代已批准 Excel 配置下的时钟分频/复位同步树。
- Excel 模板：`references/crg_demo.xlsx`
