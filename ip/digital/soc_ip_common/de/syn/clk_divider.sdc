# ============================================================================
# SDC: clk_divider
# Description: Block-level timing constraints for programmable clock divider.
#              Integration STA should override generated-clock divide factors
#              with the ratios used in the target SoC configuration.
# ============================================================================

if {![info exists CLK_DIVIDER_CLK_PERIOD]} { set CLK_DIVIDER_CLK_PERIOD 10.0 }
if {![info exists CLK_DIVIDER_DIVIDE_BY]}  { set CLK_DIVIDER_DIVIDE_BY  2 }

# ----------------------------------------------------------------------------
# Source clock
# ----------------------------------------------------------------------------
create_clock -name clk -period ${CLK_DIVIDER_CLK_PERIOD} [get_ports clk]

# ----------------------------------------------------------------------------
# Generated clock output
#   - div_ratio = 1 is a combinational bypass of clk to clk_out.
#   - div_ratio >= 2 creates a divided generated clock.
# The default divide factor is 2 for block-level synthesis sanity; top-level
# constraints should set CLK_DIVIDER_DIVIDE_BY to the selected integration mode.
# ----------------------------------------------------------------------------
create_generated_clock -name clk_out \
    -source [get_ports clk] \
    -divide_by ${CLK_DIVIDER_DIVIDE_BY} \
    [get_ports clk_out]

# ----------------------------------------------------------------------------
# Active-low asynchronous reset
# ----------------------------------------------------------------------------
set_false_path -from [get_ports rst_n]

# ----------------------------------------------------------------------------
# div_ratio is synchronous to clk at this module boundary.
# ----------------------------------------------------------------------------
set_input_delay  0.5 -clock clk [get_ports div_ratio*]
set_output_delay 0.5 -clock clk [get_ports clk_out]

# ----------------------------------------------------------------------------
# Basic block-level environment assumptions
# ----------------------------------------------------------------------------
set_input_transition 0.05 [get_ports clk]
set_input_transition 0.10 [get_ports div_ratio*]
set_load 0.01 [get_ports clk_out]
