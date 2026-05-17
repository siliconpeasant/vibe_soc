# rst_cnt Design Spec

## 1. 概述

`rst_cnt`(Reset Stretcher / 复位延迟释放计数器)用于把外部异步低有效复位 `rst_n_in` 整形为一个"**异步 assert / 同步 deassert 且延迟释放**"的复位输出 `rst_n_out`。当 `rst_n_in` 拉低时,`rst_n_out` 立即被拉低;当 `rst_n_in` 释放(变高)后,模块在工作时钟 `clk` 域内继续计数 `STRETCH_CYCLES` 个时钟周期,计数完成后才把 `rst_n_out` 拉高。

主要用途:
- 上电后给 PLL / clock generator / DLL 提供稳定时间窗口,保证下游逻辑在稳定时钟下出复位
- 把外部按键 / PMU / WDT 触发的复位脉冲延展到一个最小宽度,避免短脉冲导致部分下游逻辑漏复位
- 与 `rst_synchronizer` 配合,在 reset tree 顶层为整个域提供"长且整齐"的复位窗口

本模块**含时序**:内部有一组 DFF 实现计数器与释放控制,核心采用"异步 assert / 同步 release"标准做法,与 `rst_synchronizer` 在边界语义上保持一致。

## 2. 功能描述

- **异步 assert**:`rst_n_in = 0` 时,所有内部 DFF(计数器、释放标志)被异步清零,`rst_n_out` 立刻变为 0,与时钟无关。
- **同步 deassert**:`rst_n_in` 由 0 -> 1 之后,从下一个 `posedge clk` 开始,内部计数器每个 clk 周期 +1。
- **延迟释放**:当计数器累计达到 `STRETCH_CYCLES` 时,在该 `posedge clk` 上把 `rst_n_out` 拉高(1);计数器之后停在终值,直到下次 `rst_n_in` 再次被 assert 才被异步清零重新开始。
- **计数中途再次 assert**:若计数过程中 `rst_n_in` 再次被拉低,所有 DFF 立即被异步清零,`rst_n_out` 立即变 0,计数从头重新开始(异步置位语义)。
- **rst_n_in 长保持**:`rst_n_in` 一直保持 0 时,`rst_n_out` 也一直保持 0;`rst_n_in` 释放后才进入计数阶段。
- **上电状态**:`rst_n_in` 初始为 0 时,所有内部 DFF 处于 reset asserted 状态,`rst_n_out = 0`,计数器 = 0。

## 3. 参数

| 参数 | 类型 | 默认 | 合法范围 | 说明 |
|---|---|---|---|---|
| `CNT_WIDTH` | integer | `8` | `[1, 32]` | 内部计数器位宽,决定可表达的最大延迟周期数为 `2**CNT_WIDTH - 1`。 |
| `STRETCH_CYCLES` | integer | `16` | `[1, 2**CNT_WIDTH - 1]` | `rst_n_in` 释放后到 `rst_n_out` 释放之间的 clk 周期数。 |

**参数关系约束**:`STRETCH_CYCLES <= 2**CNT_WIDTH - 1`,否则计数器位宽不足以承载终值。

**参数合法性检查**:RTL 中通过 `initial` 块 + `$error` / `$fatal` 在仿真期间检查,综合期间通过 `generate` 配合 `$error` 提供 elaboration-time 报错:

```verilog
initial begin
    if (STRETCH_CYCLES > ((1 << CNT_WIDTH) - 1)) begin
        $error("rst_cnt: STRETCH_CYCLES (%0d) exceeds CNT_WIDTH (%0d) capacity (%0d)",
               STRETCH_CYCLES, CNT_WIDTH, (1 << CNT_WIDTH) - 1);
        $fatal;
    end
end
```

## 4. 框图

```
                              +-----------------------------------------------+
                              |                                               |
                              |    +---------------------+    +--------+      |
   rst_n_in (async, low) ---->|--->|  count_en gate      |    |        |      |
                              |    |  (only when         |    |        |      |
                              |    |   !done & rst_n_in) |    |        |      |
                              |    +-----+---------------+    |        |      |
                              |          | en                 |        |      |
                              |    +-----v---------+          |        |      |
                              |    |  cnt_reg      |          |        |      |
                              |    |  [CNT_WIDTH-1:0] +1     | done   | done  |
                              |    |  (sync, async  |--cmp-->|  DFF   +----> rst_n_out
   clk -------------------------->>|   clear by      |  ==   |        |       (active-low)
                              |    |   rst_n_in)    |  STRETCH_CYCLES |       |
                              |    +---------------+          |        |      |
                              |                               |        |      |
                              |   rst_n_in -- async clr ----->|        |      |
                              |                               +--------+      |
                              |                                               |
                              +-----------------------------------------------+
                                        rst_cnt internal datapath

  - cnt_reg : CNT_WIDTH-bit 计数器,异步 active-low 清零(由 rst_n_in 驱动)
  - done    : 1-bit DFF,标记是否计数完成;复位时为 0;计数达到 STRETCH_CYCLES 时被置 1 并锁住
  - rst_n_out 直接由 done 输出(rst_n_out = done),done = 0 表示复位仍 asserted
```

行为要点:
- 所有内部 DFF 的 async clear 都接 `rst_n_in`,实现"异步 assert"
- 计数器只在 `rst_n_in = 1 && !done` 时累加,避免溢出与不必要翻转
- `done` 一旦在 `posedge clk` 上被置 1,就靠 enable / 自反馈锁住,直到下次 `rst_n_in` 拉低

## 5. 设计要点(含假设)

1. **异步 assert / 同步 deassert 语义**:与 `rst_synchronizer` 一致,所有内部 DFF 的 async clear 端接 `rst_n_in`,`rst_n_in` 下降沿不依赖 `clk`,但 `rst_n_out` 的上升沿严格对齐 `clk` 边沿,避免在下游 DFF 上出现"半释放"。
2. **计数完成锁存**:`done` 用自反馈(`done <= done | (cnt == STRETCH_CYCLES-1)`)或显式 enable,保证一旦置 1 不会因为后续计数器翻转(若未停)而误置 0;计数器一般同时停在终值。
3. **重新计数语义**:计数中途再次 `rst_n_in = 0`,所有 DFF 异步清零,counter 回 0,done 回 0,`rst_n_out` 立即 0;之后释放再走完整 STRETCH_CYCLES。这是工业界 reset stretcher 的标准行为。
4. **参数边界**:`STRETCH_CYCLES = 1` 是最小合法值,表示"释放后 1 个 clk 周期就出复位";`STRETCH_CYCLES = 0` 不允许(否则等价无 stretch,失去本模块意义);RTL elaboration 阶段 `$error` 拦截。
5. **CNT_WIDTH 选择**:默认 8 bit,可覆盖 1~255 cycles;高频率时钟(如 1GHz)下若需要 us 级延迟可放大到 16 bit。
6. **rst_n_in 短脉冲**:只要脉冲宽度满足第一级 DFF 的 reset 最小脉宽(stdcell 库通常 100ps 级别),即可可靠触发异步清零,被本模块"拉长"为 `STRETCH_CYCLES` 个 clk 周期的复位窗口。这是 reset stretcher 的核心价值。
7. **clk gating 兼容**:本模块假设 `clk` 在 `rst_n_in` 释放前后均处于活跃状态;若 `clk` 在复位期间停摆(典型上电场景),计数会等到 `clk` 恢复后才开始,这是预期行为(也是为什么需要这个模块——保证 clk 稳定后再放下游)。
8. **严禁 latch**:计数器与 done 均为 DFF,组合路径只是 +1、比较与 mux,无任何条件分支缺失。
9. **不可被 scan 替代**:与 `rst_synchronizer` 类似,本模块输出直接驱动大量下游 reset 端,DFT 流程通常将其本身的 DFF 排除在 scan chain 之外,或用专用 reset stretcher 库单元。
10. **假设**:用户已说明端口约定,假设输出 `rst_n_out` 直接驱动该时钟域所有 DFF 的 async reset 端,fanout 由后端 buffer tree 处理。

## 6. 时序图

### Case 1: 基本释放(rst_n_in 释放后等 STRETCH_CYCLES=4 个 clk 才放 rst_n_out)

```
clk          ___     ___     ___     ___     ___     ___     ___     ___
          __|   |___|   |___|   |___|   |___|   |___|   |___|   |___|   |__
                    ^p1     ^p2     ^p3     ^p4     ^p5

rst_n_in    ______                  __________________________________________
                  |                |
                  |________________|
                                   ^ release (async deassert)

cnt_reg      0  0  0  0  0  0  0   0    1    2    3    4    4    4    4
                                        ^p1  ^p2  ^p3  ^p4(==STRETCH_CYCLES,
                                                         done<=1)

done         0  0  0  0  0  0  0   0    0    0    0    1    1    1    1
                                                       ^ sync deassert

rst_n_out   ______                  ___________________
                  |                                    |
                  |____________________________________|
                                                       ^ aligned to posedge clk
```

### Case 2: rst_n_in 短脉冲被拉长

```
clk          ___     ___     ___     ___     ___     ___     ___     ___
          __|   |___|   |___|   |___|   |___|   |___|   |___|   |___|   |__

rst_n_in    ____                  __________________________________________
                |                |
                |________________|
                ^ 非常窄的低脉冲(< 1 clk),足以异步清零

rst_n_out   ____                                      ______________________
                |                                    |
                |____________________________________|
                                                     ^ 拉长为 STRETCH_CYCLES 个 clk
```

### Case 3: 计数中途再次 assert(重新计数)

```
clk          ___     ___     ___     ___     ___     ___     ___     ___
          __|   |___|   |___|   |___|   |___|   |___|   |___|   |___|   |__

rst_n_in    __                        ____                        __________
              |                      |    |                      |
              |______________________|    |______________________|
              ^ first release             ^ re-assert during cnt
                                          ^ release again, cnt restarts

cnt_reg      0  0    1    2    3      0    0  0    1    2    3    4    4
                                      ^ async clear by rst_n_in
                                      
done         0  0    0    0    0      0    0  0    0    0    0    1    1
                                                                  ^ release after full STRETCH_CYCLES from 2nd release

rst_n_out   __                        ____                              ____
              |                      |    |                            |
              |______________________|    |____________________________|
```

说明:
- `rst_n_in` 下降沿任意时刻都能立即把 `rst_n_out` 拉低(异步)
- `rst_n_out` 上升沿一定对齐 `clk` 上升沿,且距离 `rst_n_in` 上升沿恰好 STRETCH_CYCLES 个 clk 周期(同步释放)
- 计数中途 re-assert 重置计数,完整复位窗口由最后一次 release 开始算起

## 7. 状态机

无显式 FSM。模块的"状态"全部由计数器 `cnt_reg` 和单 bit `done` 表示:

| 状态 | cnt_reg | done | rst_n_out | 触发转移 |
|---|---|---|---|---|
| RESET_ASSERTED | 0 | 0 | 0 | rst_n_in = 0(异步入此态) |
| COUNTING | 1 ~ STRETCH_CYCLES-1 | 0 | 0 | rst_n_in = 1,每 clk +1 |
| RELEASED | STRETCH_CYCLES | 1 | 1 | cnt 达到 STRETCH_CYCLES,done 锁住 |

任何状态下 `rst_n_in = 0` 都会异步回到 `RESET_ASSERTED`。可以视为一个 3 状态的隐式 FSM,但用计数器表达更简洁。

## 8. 综合 / 时序约束考虑

1. **异步路径**:`rst_n_in` 进入内部 DFF 的 async reset 端是异步路径,需在 SDC 中标 `set_false_path -from [get_ports rst_n_in] -to [get_pins -hier *_reg*/CDN]`,由顶层 base.sdc 统一处理。
2. **dont_touch / dont_retime**:`done` DFF 与计数器的最后一级建议加 `dont_retime`,保证释放沿严格在 `STRETCH_CYCLES` 个 clk 之后,不被工具优化掉个数。
3. **rst_n_out fanout**:输出通常驱动整个时钟域的 DFF reset 端,fanout 可达数百~数千,后端需要 buffer tree;本模块只输出一条线。
4. **CTS**:`clk` 网络与目标域共用同一时钟树,本模块内部不做 clock gating。
5. **recovery / removal**:由 SDC false_path 屏蔽;若使用 `set_max_delay` 替代,需小于 1 个 clk 周期。
6. **参数检查**:`initial $error` 在 elaboration 阶段拦截非法参数,综合工具(Yosys / DC)均支持,且不会引入硬件。

## 9. 验证要点(详见 verification_plan.md)

- 基本 stretch:`rst_n_in` 释放后,经过 `STRETCH_CYCLES` 个 clk 才释放 `rst_n_out`
- 短脉冲被拉长:`rst_n_in` 低脉冲 < 1 clk 时也能可靠触发并拉长
- 长保持:`rst_n_in` 持续低时 `rst_n_out` 不释放
- 计数中途再次 assert:计数重置,从最后一次 release 开始重新计数
- 参数化覆盖:`CNT_WIDTH=4` + `STRETCH_CYCLES=3` 等小边界,默认 `STRETCH_CYCLES=16`
- reset glitch:窄毛刺 / 双沿等边界场景
- 上电默认 `rst_n_out = 0`
