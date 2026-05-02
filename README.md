# vibe_soc SoC 前端开发项目

## 目录结构

```
vibe_soc/
├── chip/                 # SoC 芯片设计源码 (RTL)
│   ├── core/             # 处理器核心 (RISC-V Core)
│   ├── bus/              # 总线架构 (AXI/AHB/APB)
│   ├── periph/           # 外设 IP (UART/SPI/I2C/PWM/Timer等)
│   ├── interconnect/     # 互联与交叉开关
│   ├── top/              # SoC 顶层模块
│   └── lib/              # 通用库 / 标准单元封装
├── ip/
│   ├── third_party/      # 第三方 IP / 外购软核
│   └── digital/          # 自研 IP / 复用模块
│       └── template_ip/  # IP 模板示例 (可独立编译仿真)
│           ├── rtl/
│           ├── tb/
│           └── Makefile
├── scripts/              # 项目级公共脚本
│   ├── setup.sh          # 环境初始化
│   └── common.mk         # 公共仿真编译规则
├── doc/                  # 文档
│   ├── arch/             # 架构设计文档
│   └── spec/             # 接口规范与需求
└── Makefile              # 顶层构建入口
```

## 快速开始

### 1. 环境初始化
```bash
source scripts/setup.sh
```

### 2. IP 独立仿真
```bash
cd ip/digital/template_ip
make comp    # 编译 IP 级 testbench
make sim     # 运行 IP 级仿真
make wave    # 查看波形
```

### 3. Chip 级仿真
```bash
cd chip/core && make comp && make sim
cd chip/top  && make comp && make sim
```

## 工具链支持

- **仿真**: VCS, Verilator, Iverilog, Xcelium

## 开发规范

- 所有 RTL 文件使用 `*.v` / `*.sv` 扩展名
- 模块名与文件名保持一致
- 每个 IP 独立目录，包含 RTL + 可独立编译的 testbench
- 顶层模块统一放在 `chip/top/`
- 所有子目录 Makefile 均引用 `scripts/common.mk`，确保编译环境一致
