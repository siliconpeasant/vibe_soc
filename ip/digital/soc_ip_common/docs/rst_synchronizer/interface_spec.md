# rst_synchronizer Interface Spec

## 1. 模块标识

| 项 | 值 |
|---|---|
| 模块名 | `rst_synchronizer` |
| 文件路径 | `ip/digital/soc_ip_common/de/rtl/rst_gen/rst_synchronizer.v` |
| 顶层归属 | `ip/digital/soc_ip_common` |
| 编码规范 | Verilog-2001/2005 可综合子集 |

## 2. 参数表

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `STAGES` | integer | `2` | `[2, 8]` | 同步链 DFF 级数。决定复位释放后多少个 `posedge clk` 输出才回 1。 |

## 3. 端口表

| Signal | Direction | Width | Description |
|---|---|---|---|
| `clk` | input | 1 | 目标时钟域时钟,同步链所有 DFF 由其 posedge 触发。 |
| `rst_async_n` | input | 1 | 异步低有效复位输入。下降沿立即异步清零同步链(无需 clk);上升沿表示释放,需经 STAGES 级同步。 |
| `rst_sync_n` | output | 1 | 同步释放后的低有效复位输出。异步置位、同步释放。直接接到目标时钟域所有 DFF 的 async reset 端。 |

## 4. 时钟与复位

| 项 | 值 |
|---|---|
| 时钟 | `clk`(上升沿) |
| 复位 | `rst_async_n`(异步、低有效) |
| 复位有效电平 | 0 |
| 复位策略 | 异步置位,同步释放 |
| 时钟门控 | 无 |
| 上电默认 | reset asserted,`rst_sync_n = 0` |

## 5. 时序约束(SDC 提示)

| 约束 | 说明 |
|---|---|
| `set_false_path -from rst_async_n -to <stage_reg/CDN>` | 异步复位输入到第一级 DFF reset 端为异步路径,不纳入静态时序检查。 |
| `dont_touch` on `stage_reg[*]` | 防止综合工具在同步链中间插逻辑或重定时,保留 metastability resolution window。 |
| recovery / removal | 由 SDC false_path 后不再检查;若改 `set_max_delay`,需小于 1 个 clk period。 |
| CTS | `clk` 网络与目标时钟域共用同一时钟树,不在本模块内做时钟门控。 |

## 6. 接口时序

- **异步置位**:`rst_async_n` 下降沿后 (t<sub>RST_TO_OUT_ASYNC</sub>) 内,`rst_sync_n` 立即变 0,不依赖 `clk`。
- **同步释放**:`rst_async_n` 由 0->1 后,从第 1 个 `posedge clk` 起,1 在同步链中逐级推进,第 `STAGES` 个 `posedge clk` 上 `rst_sync_n` 变 1。
- **最短低脉冲**:`rst_async_n` 低脉冲宽度需 ≥ 第一级 DFF 的 reset 最小脉宽(由 stdcell library 决定,通常 100ps 级别),即可可靠触发异步清零。

## 7. 例化示例

```verilog
rst_synchronizer #(
    .STAGES (2)
) u_rst_sync_core (
    .clk         (core_clk),
    .rst_async_n (por_n),
    .rst_sync_n  (core_rst_n)
);
```

## 8. 依赖

无。本模块不依赖任何子模块,纯 DFF + tie-high。

