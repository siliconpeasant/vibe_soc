## -----------------------------------------------------------------------------
## rst_cnt.sdc
##
## IP 级 SDC 片段(template)。直接 source 时按本模块独立综合,可用作
## block-level STA;集成到顶层时由顶层 SDC 重新定义时钟并替换层级路径。
##
## 约定:
##   - 顶层若已 create_clock,本文件中的 create_clock 应被覆盖或注释掉
##   - 默认时钟周期 10ns(100MHz),与同分类 rst_gen 模块保持一致
##   - 例化名(默认建议)u_rst_cnt,可由上层覆写变量
## -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 用户可在 source 之前重新定义变量,以适配不同的层级 / 顶层 IO 名
# ------------------------------------------------------------------------------
if {![info exists RST_CNT_CLK_PERIOD]} { set RST_CNT_CLK_PERIOD 10.0 }
if {![info exists RST_CNT_INST]}       { set RST_CNT_INST       "u_rst_cnt" }

# ------------------------------------------------------------------------------
# 1) 工作时钟(block-level 时由本文件创建,顶层集成时由顶层创建)
# ------------------------------------------------------------------------------
create_clock -name clk -period ${RST_CNT_CLK_PERIOD} [get_ports clk]

# ------------------------------------------------------------------------------
# 2) 异步复位输入路径标 false_path
#    - 从 rst_n_in 出发的所有路径都是异步的(进入 DFF 的 async clear 端)
#    - 同时覆盖 recovery / removal,不做静态检查
# ------------------------------------------------------------------------------
set_false_path -from [get_ports rst_n_in]

# 显式把 rst_n_in 到内部 cnt_reg / done_reg async clear 端的路径标为 false
set_false_path -from [get_ports rst_n_in] \
               -to   [get_pins -hier "*cnt_reg*/CDN"]
set_false_path -from [get_ports rst_n_in] \
               -to   [get_pins -hier "*done_reg*/CDN"]

# ------------------------------------------------------------------------------
# 3) 输出 rst_n_out 是异步复位输出,接到下游 DFF 的 async reset 端
#    -> false_path 屏蔽,不让 STA 试图按 setup/hold 检查
# ------------------------------------------------------------------------------
set_false_path -to [get_ports rst_n_out]

# ------------------------------------------------------------------------------
# 4) 防止 retiming 改变 STRETCH_CYCLES 语义
#    SDC 不写 set_dont_retime;留给顶层综合 .tcl 调用:
#      set_dont_touch  [get_cells -hier "${RST_CNT_INST}/cnt_reg*"]
#      set_dont_touch  [get_cells -hier "${RST_CNT_INST}/done_reg"]
#      set_dont_retime [get_cells -hier "${RST_CNT_INST}/cnt_reg*"]
#      set_dont_retime [get_cells -hier "${RST_CNT_INST}/done_reg"]
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 5) 输出 fanout 控制(rst_n_out 通常驱动整个时钟域复位)
#    顶层可按目标域规模重新设置:
#      set_max_fanout 64 [get_ports rst_n_out]
# ------------------------------------------------------------------------------
