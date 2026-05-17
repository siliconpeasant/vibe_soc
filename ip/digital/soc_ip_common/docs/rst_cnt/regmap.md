# rst_cnt Register Map

## 概述

`rst_cnt` 为纯硬件 reset stretcher IP,**不含任何 APB / AHB / 寄存器接口**。模块行为完全由编译期 `parameter` 配置:

| Parameter | Default | Description |
|---|---|---|
| `CNT_WIDTH` | 8 | 内部计数器位宽 |
| `STRETCH_CYCLES` | 16 | `rst_n_in` 释放后延迟多少个 `posedge clk` 才释放 `rst_n_out` |

参数在 RTL 例化时静态指定,运行期不可改。

## 寄存器列表

无。

本文件存在仅为保持 `docs/<module>/` 目录结构与同 IP 下其它模块(`rstn_test_mux`、`rst_synchronizer` 等)一致,便于 doc completeness 自动检查。
