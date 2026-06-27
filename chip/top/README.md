# chip/top OpenTitan Integration

## 简介

`chip/top` now uses the OpenTitan Earlgrey vendor-island top as its only top-level path. The canonical RTL filelist is `de/rtl/filelist.f`.

当前集成范围是 OpenTitan Earlgrey vendor-island top。原生 `core/bus/uart` 最小顶层已从 `chip/top` 移除，后续如果要拆成 vibe_soc 原生模块，应在独立模块目录中逐步接回，而不是作为 `chip/top` 的默认回退路径。

## 目录结构

```
top/
├── de/
│   ├── rtl/      # RTL 源码
│   ├── lint/     # Lint 脚本/报告
│   ├── cdc/      # CDC 配置
│   ├── syn/      # 综合约束/脚本
│   ├── formal/   # 形式验证
│   └── run/      # 设计生成文件
├── dv/
│   ├── tb/       # Testbench、case 定义和 SW collateral
│   └── sim/      # 验证生成文件
└── Makefile      # 模块级仿真 / lint 入口
```

## 使用

```bash
cd chip/top       # 根目录执行
cd chip/top/de    # de 目录下也能执行
cd chip/top/dv    # dv 目录下也能执行
make flist    # 生成/校验 run filelist
make comp     # 编译 OpenTitan top
make sim      # 运行指定 TEST
```

The previous generated `vibe_soc_top` files have been removed from this module. Future native decomposition should add new module-owned RTL and update `de/rtl/filelist.f` deliberately.

## OpenTitan Vendor Mode

`chip/top` carries a staged OpenTitan Earlgrey vendor island for bootstrap bring-up.
The default `make` flow always enters the OpenTitan vendor path. With no explicit `TEST`, it uses the
validated `chip_sw_uart_smoketest` baseline.

Key files:

- `docs/opentitan_vendor_migration.md`: migration boundary and staged split plan
- `docs/opentitan_uart_bootstrap_case.md`: selected OpenTitan UART bootstrap case
- `docs/opentitan_source_manifest.md`: imported source size and file counts
- `de/rtl/vendor/opentitan/`: source-level OpenTitan import, excluding local caches and build output
- `de/rtl/filelist.f`: canonical vibe_soc-owned OpenTitan simulation filelist
- `dv/tb/tests/`: case definitions for `chip_sw_uart_smoketest` and `chip_sw_uart_tx_rx_bootstrap`

The smoke baseline uses the captured FuseSoC-generated filelist and has a passing `soc-build.soc_sim`
log. The bootstrap path should reuse this generated dependency order instead of the earlier hand-written
OpenTitan filelist.

OpenTitan vendor simulations default to `FSDB=0`, which passes `WAVES=none` into the OpenTitan runtime
TCL and avoids writing `dv/sim/<case>/waves.fsdb` during normal test runs. Use `FSDB=1` only when a debug waveform is needed.
