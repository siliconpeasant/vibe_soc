---
name: gen-asic-memmap
description: 从 Excel memory map 生成芯片地址映射 YAML 与 C/SV sysmap header。Use when building SoC address map from a memmap workbook.
---

# gen-asic-memmap

从 Excel `memmap` sheet 读取地址块，生成：

| 输出 | 说明 |
|------|------|
| `{project}_ASIC.yml` | `blocks: name / offset / size / file` |
| `{project}_sysmap.h` | C `#define ASIC_<BLOCK>_BASEADDR` |
| `{project}_sysmap.svh` | SystemVerilog `` `define ASIC_<BLOCK>_BASEADDR `` |

## MCP

```text
gen_asic_memmap(excel_file, project_name, output_dir=".")
```

## CLI

```bash
python3 .agents/skills/gen-asic-memmap/scripts/gen_asic_memmap.py \
  <memmap.xlsx> <project_name> [output_dir]
```

## Excel 列（sheet 名含 `memmap`）

| 列 | 含义 |
|----|------|
| B | block name（跳过 `Slave` / `RESERVE` / 重复名） |
| F | offset（START，如 `0x80000000`） |
| H | size（如 `2GB`、`256KB`） |
| J | yml path（可选） |

模板：`references/memmap_demo.xlsx`

## 注意

- 依赖 `pandas`
- 输出默认写到 `output_dir`（含 yml 与 sysmap headers）
- 与 `yml2reg` 互补：本工具管**块基址**；yml2reg 管**模块寄存器**
