## -----------------------------------------------------------------------------
## rst_synchronizer.sdc
##
## IP 级 SDC 片段(template)。不可直接交给综合,需要由上层 SDC
##   source -echo .../rst_synchronizer.sdc
## 引入并按照例化层级把 `get_ports rst_async_n` / `get_pins u_rst_sync/...`
## 替换为该实例真实的 hier 路径。
##
## 约定:
##   - 顶层 SDC 已经定义好 clk(create_clock)
##   - 本模块例化名(默认建议)u_rst_sync,可由上层覆写变量
## -----------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# 用户可在 source 之前重新定义这两个变量,以适配不同的层级 / 顶层 IO 名
# ------------------------------------------------------------------------------
if {![info exists RST_SYNC_INST]}      { set RST_SYNC_INST       "u_rst_sync" }
if {![info exists RST_SYNC_ASYNC_PORT]} { set RST_SYNC_ASYNC_PORT "rst_async_n" }

# ------------------------------------------------------------------------------
# 1) 异步复位输入到第一级 DFF 的 async reset 端 -> false path
#    若 RST_SYNC_ASYNC_PORT 实际是内部 net(非顶层端口),请把 [get_ports ...]
#    换成 [get_pins <driver>/Z] 或 [get_nets <net_name>]。
# ------------------------------------------------------------------------------
set_false_path -from [get_ports ${RST_SYNC_ASYNC_PORT}]

# 同时把异步复位到同步链所有 DFF 的 reset 端都标 false_path
# (异步置位路径,recovery/removal 不再静态检查)
set_false_path -from [get_ports ${RST_SYNC_ASYNC_PORT}] \
               -to   [get_pins -hier "${RST_SYNC_INST}/sync_chain_reg*/CDN"]

# ------------------------------------------------------------------------------
# 2) 同步链 DFF -> 防止 retiming / 中间插组合逻辑
#    优先 dont_touch / 用 stdcell 库的专用 reset_sync 单元替换;
#    退而求其次用 set_max_delay 把 stage 之间约束在一个 clk 周期内。
# ------------------------------------------------------------------------------
# 综合工具命令(Genus / DC 都识别 set_dont_touch),供顶层 .tcl 调用,不在 SDC 写:
#   set_dont_touch [get_cells -hier ${RST_SYNC_INST}/sync_chain_reg*]
#   set_dont_retime [get_cells -hier ${RST_SYNC_INST}/sync_chain_reg*]

# 备用:如果 SDC 流程要明确给同步链之间标 ASYNC_REG / max_delay,
# 取 1 个 clk period(假设上层已经 create_clock -name clk -period <T>):
# set _clk_period [get_attribute [get_clocks clk] period]
# set_max_delay ${_clk_period} \
#     -from [get_pins -hier "${RST_SYNC_INST}/sync_chain_reg*/Q"] \
#     -to   [get_pins -hier "${RST_SYNC_INST}/sync_chain_reg*/D"]

# ------------------------------------------------------------------------------
# 3) CTS 提示:本模块 clk 不做独立 clock gating,与目标时钟域共时钟树
#    无需在 SDC 写,留作约束 review 文档。
# ------------------------------------------------------------------------------
