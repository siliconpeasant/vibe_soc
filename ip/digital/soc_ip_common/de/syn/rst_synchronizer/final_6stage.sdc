# =============================================================================
# SDC Constraints: rst_synchronizer (STAGES = 6)
# =============================================================================

# Clock definition
set clk_period 10.0
create_clock -name clk -period $clk_period [get_ports clk]

# Async reset: false path (cross-clock-domain signal)
set_false_path -from [get_ports rst_async_n]

# Sync chain DFFs: dont_touch to prevent tool from inserting logic between stages
set sync_cells [get_cells -hier *sync_chain*]
if {[llength $sync_cells] > 0} {
    set_dont_touch $sync_cells true
}

# Reset recovery/removal: not checked for async paths with set_false_path
# If needed, use set_max_delay instead:
# set_max_delay -from [get_ports rst_async_n] -to [get_cells -hier *sync_chain_reg*] 1.0

# Output delay
set_output_delay -clock clk -max 0.5 [get_ports rst_sync_n]
set_output_delay -clock clk -min 0.0 [get_ports rst_sync_n]
