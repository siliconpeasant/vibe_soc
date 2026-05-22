# pcie IP

## 简介

pcie 是自研 IP 模块。

## 目录结构

```
pcie/
├── de/
│   ├── rtl/      # RTL 源码
│   ├── lint/     # Lint 脚本/报告
│   ├── cdc/      # CDC 配置
│   ├── syn/      # 综合约束/脚本
│   ├── formal/   # 形式验证
│   └── run/      # 设计生成文件
├── dv/
│   ├── tb/       # Testbench (可独立编译仿真)
│   ├── verif/    # 验证脚本
│   ├── tests/    # Test case
│   └── sim/      # 验证生成文件
├── Makefile      # IP 级仿真入口
└── README.md     # 本文档
```

## 独立仿真

```bash
cd ip/digital/pcie       # 根目录执行
cd ip/digital/pcie/de    # de 目录下也能执行
cd ip/digital/pcie/dv    # dv 目录下也能执行
make comp    # 编译
make sim     # 运行仿真
make wave    # 查看波形
make clean   # 清理
```

## 集成到 Chip

将 RTL 文件放入 `chip/periph/de/rtl/` 或 `chip/bus/de/rtl/` 等对应目录，
然后在 `chip/top/de/rtl/` 的顶层模块中实例化。

## 端口说明

| 信号名 | 方向 | 位宽 | 说明 |
|--------|------|------|------|
| clk    | input | 1 | 时钟 |
| rst_n  | input | 1 | 异步复位，低有效 |
| data_in | input | 8 | 输入数据 |
| valid_in | input | 1 | 输入有效 |
| data_out | output | 8 | 输出数据 |
| valid_out | output | 1 | 输出有效 |
