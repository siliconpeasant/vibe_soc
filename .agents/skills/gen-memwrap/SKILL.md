---
name: gen-memwrap
description: 从 Excel 生成统一 memory wrap RTL，并附带 sky130 OpenRAM / nangate45 FakeRAM 的 lib/lef。
  Use when: building SRAM/TPRAM/FIFO wrappers for open-source PDK flows from a mem config workbook.
---

# gen-memwrap

Excel 存储器表 → **统一 SoC 端口 wrap** + **开源宏 .lib/.lef**（catalog 匹配或在线生成）。

| 后端 | 来源 | 交付 |
|------|------|------|
| `sky130` | ORFS `sky130ram` OpenRAM 预置宏 / 在线 OpenRAM | `.v` `.lib` `.lef`（+gds 在源树） |
| `nangate45` | ORFS FakeRAM / bsg_fakeram / builtin | `.lib` `.lef` + 行为 `.v` |

## MCP

```text
gen_memwrap(excel_file, sheet_name, output_dir, platform="auto", relaxed=false, generate=true)
gen_memwrap_status()
```

## CLI

```bash
python3 .agents/skills/gen-memwrap/scripts/gen_memwrap.py \
  <mem.xlsx> <sheet_name> <output_dir> [sky130|nangate45|auto] \
  [--generate|--no-generate] [--relaxed]

python3 .agents/skills/gen-memwrap/scripts/gen_memwrap.py --status
```

环境变量：

| 变量 | 用途 |
|------|------|
| `ORFS_PLATFORMS` | catalog 预置宏根（ORFS `flow/platforms`） |
| `SILICON_CREW_ORFS_DIR` / `OPENROAD_FLOW_HOME` | 若未设 `ORFS_PLATFORMS`，回退 `$VAR/platforms` |
| `OPENRAM_HOME` | OpenRAM compiler 目录 |
| `OPENRAM_TECH` | OpenRAM technology 目录 |
| `OPENRAM_COMPILER` | `sram_compiler.py` 入口 |
| `OPENRAM_PYTHON` | 推荐 conda-env 中的 python |
| `PDK_ROOT` | sky130A / skywater-pdk 根 |
| `BSG_FAKERAM` / `FAKERAM_HOME` | nangate45 在线 bsg_fakeram（可选） |

一键加载（本机已装）：

```bash
# bash
source "$OPENRAM_ROOT/env.sh"   # set OPENRAM_ROOT to your OpenRAM install
# 或
source scripts/openram_env.sh

# csh
source "$OPENRAM_ROOT/env.csh"
```

## 在线生成新 size

`generate=true`（默认）时，**catalog 精确 depth×width 未命中**会：

| platform | 顺序 |
|----------|------|
| `sky130` | 调 **OpenRAM** 写 config → 出 `.v/.lib/.lef` 到 `output_dir/generated/sky130/...` |
| `nangate45` | 优先 **bsg_fakeram**；失败或未安装 → **builtin FakeRAM**（黑盒 `.lib/.lef` + 行为 `.v`） |

预置 catalog 命中时不调用 generator。`--no-generate` 则仅 catalog（可加 `--relaxed` 就近）。

## Excel 列

| 列 | 必填 | 说明 |
|----|------|------|
| `TYPE` | 是 | `spram` / `tpram` / `tpram(asynchronous)` / `sfifo` / `asfifo` / `rom` |
| `NumberOfWords` | 是 | depth |
| `BitsInWord` | 是 | width |
| `PLATFORM` | 否 | `sky130` \| `nangate45`（缺省用 CLI platform / sky130） |
| `PORTS` | 否 | `1rw` / `1rw1r` |
| `BitWordWrite` | 否 | ON/OFF（默认 ON） |
| `WriteSize` | 否 | mask 粒度（sky130 默认 8） |
| `Name` | 否 | wrap 逻辑名 |
| `ExactMacro` | 否 | 强制 catalog 宏名 |

`sheet_name` 为**子串匹配**（sheet 名包含即处理）。

## 输出

```text
<output_dir>/
  rtl/           # *_wrap.v + 复制/生成的底层 .v
  lib/           # 复制的 .lib
  lef/           # 复制的 .lef
  beh/           # FakeRAM 行为模型（如有）
  generated/     # 在线生成的宏
  report/        # selection.csv / selection.json
  filelist.f
```

## 统一 wrap 端口（摘要）

**SPRAM**：`clk, me, we, addr, din, [wem,] dout`  
**TPRAM**：`clk|clka/clkb, ena, wea, addra, dina, [wem,] douta, enb, addrb, doutb`  
**SFIFO / ASFIFO**：自带指针逻辑，内部例化 spram/tpram wrap  

## Catalog

- `references/catalog_sky130.json`
- `references/catalog_nangate45.json`
- Demo：`references/memwrap_demo.xlsx`

- catalog 命中：直接 copy 预置宏  
- catalog 未命中 + `generate`：OpenRAM / bsg_fakeram / builtin  
- nangate45 无双口宏：`tpram`/`asfifo` 仍走行为模型  

## 依赖

- `pandas`（+ Excel 引擎 `openpyxl`）
- ORFS platforms 路径（预置 catalog）
- 可选：OpenRAM（sky130 新 size）、bsg_fakeram（n45 外部生成）

## 范围

仅支持下列工艺后端：

| platform | 含义 |
|----------|------|
| `sky130` | SkyWater 130nm + OpenRAM |
| `nangate45` | FreePDK45 + FakeRAM / builtin 黑盒 |

交付物为统一 wrap RTL + `.lib` / `.lef`（及行为 `.v`）。
