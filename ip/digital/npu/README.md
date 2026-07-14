# npu IP

`npu` 是一个软件管理的 INT8 GEMV/线性层加速器，支持四路 INT8 MAC、
INT32 bias、定点 requantization、output zero point、ReLU/ReLU6 和 INT8
饱和输出。

## 当前配置

顶层模块为 `npu`，使用单时钟、低有效异步复位和本地 32-bit MMIO target
接口。NPU v2 phase 1 提供四个编译期容量参数：

| 参数 | 默认值 | 合法范围 |
|---|---:|---:|
| `ACT_SPM_BYTES` | 64 | 4..64，4-byte 对齐 |
| `WGT_SPM_BYTES` | 64 | 4..64，4-byte 对齐 |
| `OUT_SPM_BYTES` | 64 | 4..64，4-byte 对齐 |
| `BIAS_SPM_WORDS` | 16 | 1..16 |

固定地址 aperture 和寄存器映射保持不变。缩容后的未实现 aperture 尾部返回
`INVALID_ADDR`。当前 scratchpad 是可复位的行为级寄存器数组；本阶段不宣称
SRAM inference。未来同步 1R1W SRAM 替换契约见 `docs/interface_spec.md`。

## 接口

| 信号 | 方向 | 位宽 | 说明 |
|---|---|---:|---|
| `clk` | input | 1 | 工作时钟 |
| `rst_n` | input | 1 | 低有效异步复位 |
| `mm_valid` | input | 1 | MMIO 请求有效 |
| `mm_write` | input | 1 | 写请求选择 |
| `mm_addr` | input | 16 | 本地 byte address |
| `mm_wdata` | input | 32 | 写数据 |
| `mm_wstrb` | input | 4 | byte write strobes |
| `mm_rdata` | output | 32 | 读数据 |
| `mm_ready` | output | 1 | 请求完成/读数据有效 |
| `mm_error` | output | 1 | 当前请求错误 |
| `irq` | output | 1 | done/error level interrupt |

完整行为、寄存器和验证要求见 `docs/`。RTL 位于 `de/rtl/`，testbench 位于
`dv/tb/`，综合约束和结果位于 `de/syn/`。Agent 执行 lint、编译、仿真和综合时
必须使用注册的 `soc-build` MCP 工具，并通过 `pipeline_state.json` 门控。
