# rstn_test_mux Design Spec

## 1. 概述

`rstn_test_mux` 是一个**复位测试模式多路选择器(reset test mode multiplexer)**。在 SoC 的 DFT 流程中,功能复位(`rst_n`)与测试复位(`test_rst_n`)需要分离:正常工作时使用功能复位,scan / ATPG 测试模式下切换到测试复位,以保证测试向量对复位端的可控性。本模块通过 `test_mode` 信号在两路低有效复位之间进行选择,输出 `rst_n_out`。

本模块为**纯组合逻辑**,内部例化 `std_cell_mux #(WIDTH=1)` 实现选择功能,无时钟、无寄存器、无状态机。

适用场景:
- SoC 顶层 reset tree 中,每个时钟域的复位在进入该域前经过本模块,实现 test / functional 切换
- 与 `rst_synchronizer` 级联使用:先经过 `rstn_test_mux` 选通,再送入 `rst_synchronizer` 做同步释放
- 任意需要 test_mode 控制复位来源的数字逻辑

## 2. 功能描述

- 当 `test_mode = 1'b0`(functional mode):`rst_n_out = rst_n`
- 当 `test_mode = 1'b1`(test mode):`rst_n_out = test_rst_n`
- 选择逻辑由 `std_cell_mux` 实现,`sel = test_mode`,`a = rst_n`,`b = test_rst_n`
- 输出 `rst_n_out` 为低有效复位信号,与输入同极性,无需极性转换
- 纯组合:输出在任一输入变化后,经过 `std_cell_mux` 的 prop delay 即变化,无时钟依赖

## 3. 参数

| 参数 | 类型 | 默认 | 合法范围 | 说明 |
|---|---|---|---|---|
| 无 | — | — | — | 本模块无自定义参数,内部 `std_cell_mux` 的 `WIDTH` 固定为 1。 |

## 4. 框图

```
                    +-------------------+
    rst_n --------->|                   |
      (active-low)  |                   |
                    |   std_cell_mux    |----> rst_n_out
    test_rst_n ---->|   #(WIDTH=1)      |      (active-low)
      (active-low)  |                   |
                    |   sel = test_mode |
    test_mode ----->|   a   = rst_n     |
                    |   b   = test_rst_n|
                    |   y   = rst_n_out |
                    +-------------------+
```

- `std_cell_mux` 为项目已有标准单元,纯组合 2-to-1 mux
- `sel = 0` 时选 `a`(`rst_n`),`sel = 1` 时选 `b`(`test_rst_n`)
- 所有信号均为 1-bit,`WIDTH` 固定为 1

## 5. 设计要点

1. **纯组合无时序**:本模块不含任何 DFF / latch,输出完全由输入组合决定,无时钟、无复位、无上电状态。
2. **test_mode 静态假设**:在典型 SoC 中,`test_mode` 由顶层 pin 或 fuse 控制,在芯片运行期间基本保持不变(只在进入/退出测试时切换)。虽然本模块支持动态切换,但 `test_mode` 在功能模式下应稳定为 0,避免复位毛刺。
3. **无毛刺保证**:由于 `std_cell_mux` 使用简单 `assign y = sel ? b : a`,当 `sel` 变化时若 `a` 与 `b` 状态不同,输出可能出现毛刺。在 reset 场景下,若 `rst_n` 和 `test_rst_n` 同时有效(均为 0),切换 `test_mode` 不会产生毛刺;若一高一低,切换会产生 0/1 跳变。建议在 `test_mode` 切换前确保两路复位处于同一状态(均 asserted 或均 released)。
4. **极性保持**:输入输出均为 active-low,`std_cell_mux` 本身不反转极性,无需额外反相器。
5. **严禁 latch**:纯组合 assign / mux,无任何条件分支缺失,综合后不会产生 latch。
6. **DFT**:本模块本身就是 DFT 基础设施的一部分。在 test mode 下,`test_rst_n` 由 ATE / scan controller 驱动,保证复位端可控;在 functional mode 下,`test_rst_n` 通常被 tied off 或忽略。
7. **级联使用**:典型用法为 `rstn_test_mux` -> `rst_synchronizer`,即先选通再同步,保证进入目标时钟域的复位已经过 test mode 筛选。

## 6. 时序图

```
Case 1: test_mode = 0 (functional mode)

test_mode    ________________________________________________

rst_n        __________                ______________________
                          |          |
                          |__________|
                          ^ assert   ^ release

rst_n_out    __________                ______________________
                          |          |
                          |__________|

Case 2: test_mode = 1 (test mode)

test_mode    ________________________________________________
             (constant 1)

rst_n        __________                ______________________
                          |          |
                          |__________|

test_rst_n   _____________________                ___________
                                   |              |
                                   |______________|
                                   ^ assert       ^ release

rst_n_out    _____________________                ___________
                                   |              |
                                   |______________|

Case 3: test_mode 动态切换 (rst_n = 1, test_rst_n = 0)

test_mode    _____________                    _______________
                          |__________________|
                          ^ switch to test   ^ switch back

rst_n        ________________________________________________
             (constant 1, released)

test_rst_n   _____________________                ___________
                                   |              |
                                   |______________|

rst_n_out    _____________                    _______________
                          |__________________|
                          ^ follow test_rst_n ^ follow rst_n
```

说明:
- 纯组合:输出变化仅由输入变化 + `std_cell_mux` 传播延时决定,无时钟对齐要求。
- `test_mode` 切换时,输出在组合延时后跟随所选输入。

## 7. 状态机

无。本模块为纯组合逻辑,无显式状态机。

## 8. 综合 / 时序约束考虑

1. **纯组合路径**:从 `rst_n` / `test_rst_n` / `test_mode` 到 `rst_n_out` 是纯组合路径,需纳入静态时序分析:
   - `set_max_delay` 或常规 `setup`/`hold` 检查适用
   - 由于输出通常驱动大量 DFF 的异步 reset 端,该路径的 fanout 很大,需在综合/布局阶段关注驱动能力
2. **Fanout 管理**:若 `rst_n_out` 驱动整个时钟域的 DFF reset 端,fanout 可达数百~数千。建议在综合时对该 net 做 `set_max_fanout` 约束,或让工具自动插 buffer tree。本模块本身只提供一个 mux 输出,不处理 buffer tree。
3. **std_cell_mux 约束**:内部 `std_cell_mux` 为标准单元,不应被 flatten 或优化掉,建议 `dont_touch` 或作为 hierarchy preserve 处理,便于 DFT 流程识别。
4. **test_mode 路径**:从 `test_mode` pin 到 `rst_n_out` 的路径也需满足 setup/hold,虽然 `test_mode` 通常变化极慢,但静态切换时仍需检查。
5. **CTS**:本模块无时钟输入,不涉及时钟树综合。

## 9. 验证要点(详见 verification_plan.md)

- test_mode = 0 时,rst_n_out = rst_n
- test_mode = 1 时,rst_n_out = test_rst_n
- test_mode 动态切换时,输出在组合延时后正确跟随
- 所有输入组合(2^3 = 8 种)真值表覆盖
- 无毛刺 / 无 latch 推断
