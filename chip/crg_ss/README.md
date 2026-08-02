# crg_ss Module

## 简介

crg_ss 是芯片 vibe_soc 的子模块。

## 目录结构

```
crg_ss/
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
cd chip/crg_ss       # 根目录执行
cd chip/crg_ss/de    # de 目录下也能执行
cd chip/crg_ss/dv    # dv 目录下也能执行
make flist    # 生成 rtl/filelist.f
make lint     # 语法检查
make comp     # 编译仿真
make sim      # 运行仿真
```

## Generate + compile (current demo)

See `docs/compile_notes.md` for generator issues and stub strategy.

```bash
# RTL top: demo_crg_top
# make from repo root via MCP: soc_comp MODULE=chip/crg_ss top=demo_crg_top
```
