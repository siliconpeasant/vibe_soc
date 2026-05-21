# ============================================================================
# SDC: clk_glitch_free_mux
# Description: Timing constraints for glitch-free 2-to-1 clock multiplexer v3.3
#              Uses std_cell_sync (2-stage synchronizer) + std_cell_icg (ICG)
#              + std_cell_clk_or with feedback interlock for break-before-make switching.
# ============================================================================

# ----------------------------------------------------------------------------
# Clock definitions (async clocks — no phase relationship assumed)
# ----------------------------------------------------------------------------
create_clock -name clk0 -period 10.0 [get_ports clk0]
create_clock -name clk1 -period 10.0 [get_ports clk1]

# The two clocks are mutually exclusive — they are never active simultaneously
set_clock_groups -logically_exclusive -group {clk0} -group {clk1}

# ----------------------------------------------------------------------------
# Feedback interlock (break-before-make):
#   en0_raw = sel0 & ~en1_sync,  en1_raw = sel1 & ~en0_sync
#   The path en0_raw -> u_sync_en0 -> en0_sync -> en1_raw -> u_sync_en1 -> en1_sync -> en0_raw
#   involves registers inside std_cell_sync, so it is NOT a true combinational loop.
#   However, STA tools may flag it; the false_path below breaks the analysis.
# ----------------------------------------------------------------------------
set_false_path -through [get_pins u_sync_en0/sync_out] -through [get_pins u_sync_en1/sync_out]

# ----------------------------------------------------------------------------
# std_cell_sync instances: async_in is sampled by clk, no timing from async_in
# ----------------------------------------------------------------------------
set_false_path -to [get_pins u_sync_en0/async_in]
set_false_path -to [get_pins u_sync_en1/async_in]

# ----------------------------------------------------------------------------
# std_cell_icg instances: en input is async to clock, captured by latch
# ----------------------------------------------------------------------------
set_false_path -to [get_pins u_icg0/en]
set_false_path -to [get_pins u_icg1/en]

# ----------------------------------------------------------------------------
# test_mode: async test control, bypasses ICG latch
# ----------------------------------------------------------------------------
set_false_path -from [get_ports test_mode] -to [get_pins u_icg0/test_en]
set_false_path -from [get_ports test_mode] -to [get_pins u_icg1/test_en]

# ----------------------------------------------------------------------------
# rst_n: active-low async reset — no timing check on reset paths
# ----------------------------------------------------------------------------
set_false_path -from [get_ports rst_n] -to [get_pins u_sync_en0/rst_n]
set_false_path -from [get_ports rst_n] -to [get_pins u_sync_en1/rst_n]

# ----------------------------------------------------------------------------
# clk_out is a generated clock derived from whichever source is selected.
# Since selection is dynamic, we define it as a muxed output.
# ----------------------------------------------------------------------------
# No create_generated_clock here — the output clock is dynamically selected.
# STA tools should propagate the active clock through the mux.

# ----------------------------------------------------------------------------
# Control inputs: sel is async to both clocks (slow / static)
# ----------------------------------------------------------------------------
set_false_path -from [get_ports sel] -to [get_ports clk_out]

# ----------------------------------------------------------------------------
# Combinational path through the mux (AND-OR tree)
# ----------------------------------------------------------------------------
set_max_delay 2.0 -from [get_ports clk0] -to [get_ports clk_out]
set_max_delay 2.0 -from [get_ports clk1] -to [get_ports clk_out]

# ----------------------------------------------------------------------------
# Set input transition / drive for clock ports
# ----------------------------------------------------------------------------
set_input_transition 0.05 [get_ports clk0]
set_input_transition 0.05 [get_ports clk1]

# ----------------------------------------------------------------------------
# Set output load
# ----------------------------------------------------------------------------
set_load 0.01 [get_ports clk_out]
