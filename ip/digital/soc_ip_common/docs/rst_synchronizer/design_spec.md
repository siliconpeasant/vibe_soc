# rst_synchronizer Design Spec

## 1. 概述

`rst_synchronizer` 是经典的 **异步置位 / 同步释放(async-assert, sync-release)** 复位同步器。它把一个异步、低有效的复位信号 `rst_async_n` 整理成在目标时钟域 `clk` 上同步释放的复位输出 `rst_sync_n`,用于驱动该时钟域内所有 DFF 的复位端,避免复位 **释放沿** 在不同 DFF 上跨越 setup/hold 而导致部分电路释放、部分电路仍复位,引发亚稳态或状态机进入非法态。

适用场景:
- 外部 power-on reset / PMU reset 进入芯片后,每个时钟域配一个 `rst_synchronizer`
- PLL / CRG 输出时钟与 reset 配对的复位整形
- 任意跨时钟域的 reset 信号整形

## 2. 功能描述

- 输入异步低有效复位 `rst_async_n`,**无需 `clk` 边沿即可立即生效**(异步置位):当 `rst_async_n` 下降沿到来,所有同步链 DFF 被异步清零,`rst_sync_n` 立刻拉低。
- 复位释放(`rst_async_n` 由 0 -> 1)时,同步链的源头 D 端为常数 1,这个 1 通过 `STAGES` 级 DFF 在 `clk` 上升沿依次推进,经过 `STAGES` 个 `posedge clk` 后输出 `rst_sync_n` 才回到 1。
- 上电(`rst_async_n` 初始为 0)时所有 DFF 处于 reset asserted,`rst_sync_n = 0`。
- 极短毛刺:只要 `rst_async_n` 的低脉冲宽度足够触发第一级 DFF 的异步清零(即满足 reset recovery / removal),即使其宽度小于半个 `clk` 周期,也会被捕获,并使同步链完整重新走一遍释放过程。

## 3. 参数

| 参数 | 类型 | 默认 | 合法范围 | 说明 |
|---|---|---|---|---|
| `STAGES` | parameter | `2` | `[2, 8]` | 同步链 DFF 级数。级数越多,亚稳态平均失效率(MTBF)越好,但释放延迟越大。典型工程取 2~3。 |

## 4. 框图

```
                                +-------------------- async reset (low) -----------------+
                                |             |                |                          |
                                v             v                v                          v
                              +----+        +----+           +----+                     +----+
                rst_async_n   |    |        |    |           |    |                     |    |
                  |           |    |        |    |           |    |                     |    |
                 (active-low) |    |        |    |           |    |                     |    |
                              |    |        |    |           |    |                     |    |
                 1'b1 ------->| D Q|------->| D Q|---------->| D Q|--- ... ------------>| D Q|----> rst_sync_n
                              |    |        |    |           |    |                     |    |
                       clk -->|>   |  clk ->|>   |   clk --->|>   |    ...      clk --->|>   |
                              | rn |        | rn |           | rn |                     | rn |
                              +----+        +----+           +----+                     +----+
                              stage[0]      stage[1]         stage[2]                   stage[STAGES-1]

  - 每个 DFF 的异步 active-low reset 端均接 rst_async_n
  - 第一级 D 端为常数 1'b1(tie-high)
  - 输出 rst_sync_n = stage[STAGES-1]
  - STAGES 默认 2;图中省略号代表可扩展级数
```

## 5. 设计要点

1. **异步置位**:所有同步链 DFF 都用同一根 `rst_async_n` 作 async active-low clear,实现拉低即清零的“异步置位”语义,无需等待 `clk`。
2. **同步释放**:第一级 D 端固定为 `1'b1`,只有时钟到来后 1 才能逐级传播,这样保证 `rst_sync_n` 的上升沿一定对齐 `clk` 上升沿。
3. **STAGES 选择**:2 级是工业最小值,适用大多数低风险场景;高速 / 高 MTBF 要求场合可取 3~4 级。
4. **上电状态**:由于异步复位接到所有 DFF 的 reset 端,只要 `rst_async_n` 上电初始为 0,所有寄存器自动进入 reset 状态,`rst_sync_n = 0`。
5. **严禁 latch**:同步链全部为 DFF,组合路径仅是 tie-high 与级间互连,无任何条件分支,综合后不会产生 latch。
6. **DFT**:本模块通常不进 scan(reset 端不可控会破坏 scan shift),需在 DFT 流程中标 `dont_touch` 或使用特定 reset synchronizer 库单元,详见综合考虑。

## 6. 时序图

```
clk          ___     ___     ___     ___     ___     ___     ___     ___
          __|   |___|   |___|   |___|   |___|   |___|   |___|   |___|   |__
                                                         ^ rising edge

rst_async_n  __________                ____________________________________
                       |              |
                       |______________|
                       ^ async assert  ^ release (deassert)

stage[0]     __________                              ___________________
                       |                            |
                       |____________________________|
                                                    ^ aligned to first clk after release

stage[1]=    __________                                      ___________
rst_sync_n             |                                    |
(STAGES=2)             |____________________________________|
                                                            ^ STAGES posedge clk after release
```

说明:
- `rst_async_n` 下降沿立即把所有 stage 拉低 → `rst_sync_n` **不等时钟** 即变 0。
- `rst_async_n` 由 0->1 之后,在第 N 个 `posedge clk` (N = STAGES) 上,`rst_sync_n` 才变为 1。

## 7. 状态机

无。本模块为复位整形电路,无显式状态机。

## 8. 综合 / 时序约束考虑

1. **跨异步路径**:`rst_async_n` 进入同步链第一级 DFF 的 async reset 端是一条异步路径,需要在 SDC 中标:
   - `set_false_path -from [get_ports rst_async_n] -to [get_pins -hier *stage_reg*/CDN]`(或对应 reset pin 名),由顶层 base.sdc 统一处理,本阶段文档仅提示。
2. **同步链 DFF 之间的 D->Q 路径**:虽然在功能上是 `clk` 同一时钟域,但物理上希望工具不要在中间插组合逻辑、不要打 buffer 影响 metastability resolution time,建议:
   - 对 `stage_reg[*]` 加 `dont_touch` / `dont_retime`
   - 或使用 stdcell 库中专用的 reset sync 单元(如 `SYNC2DFF`)
3. **reset recovery / removal**:释放沿在第一级 DFF 上需满足 recovery/removal,base.sdc 给出 `set_false_path` 后工具不再检查;若用 `set_max_delay`,需保证小于 1 个 clk period。
4. **CTS**:`clk` 进入本模块的网络应与该时钟域其它 DFF 同一时钟树,不要单独 clock gating。
5. **第一级 D 端**:`1'b1` 综合后会落到 tie-high cell,代码不要写成可被优化掉的形式。

## 9. 验证要点(详见 verification_plan.md)

- 上电默认 rst_sync_n=0
- rst_async_n 异步置位,无需 clk
- 释放延迟严格等于 STAGES 个 posedge clk
- 短脉冲(< 0.5 clk)能正确被捕获
- STAGES = 2/3/4 三组参数化覆盖
