# vibe_soc_top Integration

## 简介

`vibe_soc_top` 是当前可 lint/compile 的最小顶层集成，由 `soc-integrate` MCP 自动生成。

当前集成范围：

- `chip/core/de/rtl/core.v`
- `chip/bus/de/rtl/bus.v`
- `ip/digital/uart/de/rtl/uart.v`

当前数据通路为 `core -> bus`，UART 以独立 TX/RX 顶层端口接出。时钟和低有效复位由三个实例共享。

以下模块尚未纳入当前顶层：SPI、PCIe、periph、interconnect、lib。它们需要先完成接口定义和 lint，再通过 `soc-integrate` MCP 加入；不得将当前顶层描述为完整 full-chip 集成。

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
│   ├── tb/       # Testbench
│   ├── verif/    # 验证脚本
│   ├── tests/    # Test case
│   └── sim/      # 验证生成文件
└── Makefile      # 模块级仿真 / lint 入口
```

## 使用

```bash
cd chip/top       # 根目录执行
cd chip/top/de    # de 目录下也能执行
cd chip/top/dv    # dv 目录下也能执行
make flist    # 生成 rtl/filelist.f
make lint     # 语法检查
make comp     # 编译仿真
make sim      # 运行仿真
```

`de/rtl/vibe_soc_top.v`、`.integrate.json` 和 `.integrate.csv` 均为自动生成文件。端口或子模块变化后应使用 `soc_update`/`soc_integrate` MCP 刷新，禁止直接编辑顶层 RTL。
