# clk_glitch_free_mux 综合报告 v3.3

## 基本信息

| 项目 | 内容 |
|------|------|
| 模块名 | clk_glitch_free_mux |
| 版本 | v3.3 |
| 功能 | 无毛刺 2 选 1 时钟多路复用器，带 async rst_n |
| 工具 | Yosys 0.9 |
| 综合命令 | `make syn RTL_TOP=clk_glitch_free_mux` |
| 网表 | `de/syn/clk_glitch_free_mux_netlist.v` |
| SDC | `de/syn/clk_glitch_free_mux.sdc` |

## 版本变更 (v3.3 vs v3.2)

| 项目 | v3.2 | v3.3 |
|------|------|------|
| clk_out OR 门 | `std_cell_or u_or` | **`std_cell_clk_or u_or`** |
| 总 cell 数 | 18 | 18 (优化后等价) |

## 架构说明 (v3.3)

v3.3 采用标准单元构建的 glitch-free 时钟切换结构：

1. **选择解码**: `en0_raw = ~sel & ~en1_sync`, `en1_raw = sel & ~en0_sync`
2. **反馈互锁**: 组合 AND+NOT 逻辑形成 break-before-make 互锁
3. **2 级同步器** (`std_cell_sync`, STAGES=2):
   - `u_sync_en0`: 将 `en0_raw` 同步到 `clk0` 域 (2 DFFs, async rst_n)
   - `u_sync_en1`: 将 `en1_raw` 同步到 `clk1` 域 (2 DFFs, async rst_n)
4. **时钟门控** (`std_cell_icg`):
   - `u_icg0`: 用 latch + AND 门控 `clk0`
   - `u_icg1`: 用 latch + AND 门控 `clk1`
5. **时钟合并** (`std_cell_clk_or`):
   - `u_or`: `clk_out = gated_clk0 | gated_clk1` (时钟域专用 OR 门)

## 网表统计

| 指标 | 数值 |
|------|------|
| 总 cell 数 | 18 |
| $_AND_ | 4 |
| $_DFF_PN0_ | 4 |
| $_DLATCH_P_ | 2 (intentional ICG latches) |
| $_NOT_ | 5 |
| $_OR_ | 3 |
| Wires | 42 |
| Wire bits | 44 |
| Memories | 0 |

**Latch/FF 明细**:
- 4 个 DFF (`$_DFF_PN0_`): `u_sync_en0` (2) + `u_sync_en1` (2) -- 2 级同步器链，带 async rst_n
- 2 个 latch (`$_DLATCH_P_`): `u_icg0` (1) + `u_icg1` (1) -- ICG 负电平透明锁存器
- **0 个非预期 latch**

**估算面积**: ~29.5 GE (28nm 典型库)

## 时序结论

- **WNS**: 1.50 ns (estimated, combinational clock path through ICG)
- **TNS**: 0.00 ns
- **关键路径**: clk0/clk1 -> DLATCH_P (transparent window) -> AND -> OR -> clk_out
- **约束**: max_delay 2.0 ns (from SDC, clk0/clk1 -> clk_out)
- **估算延迟**: ~0.5 ns (latch transparency + 2 级门)
- **Slack**: +1.5 ns
- **结果**: TIMING MET

**注意**: 同步器路径 (`en0_raw` -> 2-stage DFF -> `en0_sync`) 和反馈互锁路径在 SDC 中已设为 false_path，因为它们是异步控制信号。真实 STA 需在 SoC 层级用实际工艺库进行。

## 等价性说明

综合后网表与 RTL 功能等价：
- 4 个 `$_DFF_PN0_` 对应 2 个 `std_cell_sync` 实例的 2 级同步链 (各 2 DFFs)，带 async rst_n
- 2 个 `$_DLATCH_P_` 对应 2 个 `std_cell_icg` 实例的透明锁存器
- 4 个 `$_AND_` 分别实现: `en0_raw`, `en1_raw`, `gated_clk0`, `gated_clk1`
- 3 个 `$_OR_` 分别实现: `test_mode` bypass (2) + `clk_out` 合并 (1)
- 5 个 `$_NOT_` 分别实现: `~sel`, `~clk0`, `~clk1`, `~en1_sync`, `~en0_sync`
- `std_cell_clk_or u_or` 实例在网表中展开为 `$_OR_` 门驱动 clk_out，与 `std_cell_or` 功能等价，但使用 `std_cell_clk_or` 有助于工具识别时钟域路径

## 改进建议

1. **物理实现**: 建议将每个 ICG 的 latch 和 AND 门靠近放置，减少时钟偏斜 (clock skew)
2. **时钟树**: `clk_out` 需接入时钟树综合 (CTS)，避免长连线导致的 clock latency 差异
3. **DFT**: ICG 和同步器结构需标记 `set_dont_touch`，防止综合工具优化掉 glitch-free 机制
4. **STA**: 真实时序分析需在 SoC 层级进行，关注:
   - latch 透明窗与 clock 低电平期的重叠
   - 同步器链的 MTBF (metastability resolution time)
   - 反馈互锁的 break-before-make 延迟 (约 2-3 个目标时钟周期)
5. **复位策略**: rst_n 确保同步器链在复位时清零，避免上电时输出毛刺
6. **功耗**: 无时钟使能时，两个 ICG 由 sel 控制开关；若需同时关闭两个时钟，建议在更高层级控制 sel
7. **v3.3 结构改进**: 使用 `std_cell_clk_or` 实例替代 `std_cell_or`，有助于工具在时钟树综合和 STA 阶段识别时钟域路径，便于施加时钟相关约束
