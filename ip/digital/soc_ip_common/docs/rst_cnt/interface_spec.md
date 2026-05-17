# rst_cnt Interface Spec

## 1. 模块标识

| 项 | 值 |
|---|---|
| 模块名 | `rst_cnt` |
| 文件路径 | `ip/digital/soc_ip_common/de/rtl/rst_gen/rst_cnt.v` |
| 顶层归属 | `ip/digital/soc_ip_common` |
| 编码规范 | Verilog-2001/2005 可综合子集 |
| 功能类别 | rst_gen / Reset stretcher(异步 assert,同步 deassert,可配置延迟周期数) |

## 2. 参数表

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `CNT_WIDTH` | integer | `8` | `[1, 32]` | 内部计数器位宽。最大可表达延迟为 `2**CNT_WIDTH - 1` 个 clk 周期。 |
| `STRETCH_CYCLES` | integer | `16` | `[1, 2**CNT_WIDTH - 1]` | `rst_n_in` 释放后,延迟多少个 `posedge clk` 再释放 `rst_n_out`。 |

**参数关系**:`STRETCH_CYCLES <= 2**CNT_WIDTH - 1`,RTL 中由 `initial $error` / `$fatal` 在 elaboration 阶段检查。

## 3. 端口表

| Signal | Direction | Width | Clock | Reset | Description |
|---|---|---|---|---|---|
| `clk` | input | 1 | self | — | 工作时钟,上升沿触发内部计数器与 `done` DFF。 |
| `rst_n_in` | input | 1 | async | self | 异步低有效复位输入。下降沿立即清零内部 DFF(异步 assert);上升沿启动同步计数(同步 deassert)。 |
| `rst_n_out` | output | 1 | `clk`(deassert 时) | `rst_n_in`(assert 时) | 延迟释放后的低有效复位输出。**异步 assert / 同步 deassert**,直接接到目标时钟域所有 DFF 的 async reset 端。 |

## 4. 时钟与复位

| 项 | 值 |
|---|---|
| 时钟 | `clk`(上升沿) |
| 复位 | `rst_n_in`(异步、低有效) |
| 复位有效电平 | 0 |
| 复位策略 | 异步置位 / 同步释放 + 计数延迟 |
| 时钟门控 | 无(模块内不门控,假设 `clk` 在 release 前后稳定) |
| 上电默认 | `rst_n_in = 0` 时,内部计数器 = 0、`done = 0`、`rst_n_out = 0` |

## 5. 时序约束(SDC 提示)

| 约束 | 说明 |
|---|---|
| `set_false_path -from [get_ports rst_n_in] -to [get_pins -hier *_reg*/CDN]` | `rst_n_in` 到内部 DFF async clear 端的路径设为 false_path,不纳入 STA。 |
| `dont_retime` / `dont_touch` on `cnt_reg[*]` 与 `done_reg` | 防止综合工具重定时改变释放沿的 clk 周期数,保证 STRETCH_CYCLES 语义。 |
| `set_max_fanout` on `rst_n_out` | 输出 fanout 通常很大,需控制或允许工具插 buffer tree。 |
| recovery / removal | 由 false_path 屏蔽;若改 `set_max_delay`,需小于 1 个 clk 周期。 |
| CTS | `clk` 与目标时钟域共用同一时钟树,不在本模块内做时钟门控。 |

## 6. 接口时序

- **异步 assert(t<sub>RST_TO_OUT_ASYNC</sub>)**:`rst_n_in` 下降沿后,经过组合传播延时(~ns 级)`rst_n_out` 变 0,不依赖 `clk`。
- **同步 deassert 延迟**:`rst_n_in` 由 0 -> 1 后,从下一个 `posedge clk` 开始累计,经过 `STRETCH_CYCLES` 个 `posedge clk` 后 `rst_n_out` 在该 clk 上升沿变 1。
- **最短低脉冲**:`rst_n_in` 低脉冲宽度需 ≥ 第一级 DFF 的 reset 最小脉宽(stdcell 库,通常 100ps 级别);只要触发异步清零,模块会把它拉长为 `STRETCH_CYCLES` 个 clk 周期的复位窗口。
- **计数中途 re-assert**:任意时刻 `rst_n_in` 拉低均异步重置;再次释放后从头计满 `STRETCH_CYCLES` 才释放。

## 7. 例化示例

### 默认配置(8-bit counter, 延迟 16 cycles)

```verilog
rst_cnt u_rst_cnt (
    .clk        (sys_clk),
    .rst_n_in   (por_n),
    .rst_n_out  (sys_rst_stretched_n)
);
```

### 自定义参数(16-bit counter, 延迟 1024 cycles)

```verilog
rst_cnt #(
    .CNT_WIDTH      (16),
    .STRETCH_CYCLES (1024)
) u_rst_cnt_long (
    .clk        (sys_clk),
    .rst_n_in   (por_n),
    .rst_n_out  (long_rst_n)
);
```

### 与 rst_synchronizer 级联(先 stretch 再 sync)

通常情况下 `rst_cnt` 本身已经提供"异步 assert / 同步 deassert"语义,但若需要进一步降低亚稳态风险,可在其后再级联 `rst_synchronizer`:

```verilog
wire stretched_rst_n;

rst_cnt #(
    .CNT_WIDTH      (8),
    .STRETCH_CYCLES (32)
) u_rst_cnt (
    .clk        (core_clk),
    .rst_n_in   (por_n),
    .rst_n_out  (stretched_rst_n)
);

rst_synchronizer #(
    .STAGES (2)
) u_rst_sync (
    .clk         (core_clk),
    .rst_async_n (stretched_rst_n),
    .rst_sync_n  (core_rst_n)
);
```

## 8. 依赖

无外部子模块依赖。本模块只使用基本 DFF + 组合逻辑(加法器、比较器、AND/OR)。
