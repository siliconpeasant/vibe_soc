# rstn_test_mux Interface Spec

## 1. 模块标识

| 项 | 值 |
|---|---|
| 模块名 | `rstn_test_mux` |
| 文件路径 | `ip/digital/soc_ip_common/de/rtl/rst_gen/rstn_test_mux.v` |
| 顶层归属 | `ip/digital/soc_ip_common` |
| 编码规范 | Verilog-2001/2005 可综合子集 |

## 2. 参数表

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| 无 | — | — | — | 本模块无用户可配置参数。内部例化 `std_cell_mux` 时固定 `WIDTH = 1`。 |

## 3. 端口表

| Signal | Direction | Width | Description |
|---|---|---|---|
| `rst_n` | input | 1 | 功能复位,低有效(active-low)。正常工作时使用此复位。 |
| `test_rst_n` | input | 1 | 测试复位,低有效(active-low)。DFT / scan 测试模式下使用此复位。 |
| `test_mode` | input | 1 | 测试模式选择。`1'b0` = functional mode(选 `rst_n`);`1'b1` = test mode(选 `test_rst_n`)。 |
| `rst_n_out` | output | 1 | 选通后的复位输出,低有效(active-low)。由 `test_mode` 决定来源。 |

## 4. 时钟与复位

| 项 | 值 |
|---|---|
| 时钟 | 无(纯组合逻辑) |
| 复位 | 无(纯组合逻辑,无时序元件需要复位) |
| 复位有效电平 | — |
| 复位策略 | — |
| 时钟门控 | 无 |
| 上电默认 | 由输入决定(组合输出,无上电状态) |

## 5. 时序约束(SDC 提示)

| 约束 | 说明 |
|---|---|
| `set_max_delay -from [get_ports rst_n] -to [get_ports rst_n_out]` | `rst_n` 到 `rst_n_out` 的组合路径最大延时约束。 |
| `set_max_delay -from [get_ports test_rst_n] -to [get_ports rst_n_out]` | `test_rst_n` 到 `rst_n_out` 的组合路径最大延时约束。 |
| `set_max_delay -from [get_ports test_mode] -to [get_ports rst_n_out]` | `test_mode` 到 `rst_n_out` 的选择路径最大延时约束。 |
| `set_max_fanout` on `rst_n_out` | 输出通常驱动大量 DFF 的 reset 端,需控制 fanout 或允许工具自动插 buffer tree。 |
| `dont_touch` on `u_mux` | 内部 `std_cell_mux` 例化建议保留 hierarchy,便于 DFT 流程识别。 |

## 6. 接口时序

- **传播延时(t<sub>PD</sub>)**:任一输入(`rst_n` / `test_rst_n` / `test_mode`)变化到 `rst_n_out` 稳定的时间,等于 `std_cell_mux` 的组合传播延时(典型工艺下约 10~50 ps,取决于驱动强度与负载)。
- **无 setup/hold**:本模块不含时序元件,对输入信号无 setup/hold 要求。
- **无毛刺窗口**:由于 `std_cell_mux` 使用 `assign y = sel ? b : a`,当 `sel` 变化且 `a != b` 时,输出可能出现毛刺。建议 `test_mode` 切换时两路复位处于同一状态(均 asserted 或均 released)。

## 7. 例化示例

```verilog
rstn_test_mux u_rstn_test_mux (
    .rst_n       (sys_rst_n),
    .test_rst_n  (scan_rst_n),
    .test_mode   (dft_test_mode),
    .rst_n_out   (core_rst_n_selected)
);
```

级联 `rst_synchronizer` 的典型用法:

```verilog
wire core_rst_n_muxed;

rstn_test_mux u_rstn_test_mux (
    .rst_n       (sys_rst_n),
    .test_rst_n  (scan_rst_n),
    .test_mode   (dft_test_mode),
    .rst_n_out   (core_rst_n_muxed)
);

rst_synchronizer #(
    .STAGES (2)
) u_rst_sync (
    .clk         (core_clk),
    .rst_async_n (core_rst_n_muxed),
    .rst_sync_n  (core_rst_n)
);
```

## 8. 依赖

| 模块 | 路径 | 说明 |
|---|---|---|
| `std_cell_mux` | `ip/digital/soc_ip_common/de/rtl/std_cell/std_cell_mux.v` | 标准 2-to-1 多路选择器,参数 `WIDTH` 固定为 1。 |
