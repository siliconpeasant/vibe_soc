# std_cell_clk_mux constraints
# Glitch-free 2:1 clock multiplexer with async clock sources

# ---------------------------------------------------------------------------
# clk0 and clk1 are independent (potentially async) clock sources.
# Declare them as separate clocks; the mux safely switches between them
# using negative-level transparent latches.
# ---------------------------------------------------------------------------
create_clock -name clk0 -period 10.0 [get_ports clk0]
create_clock -name clk1 -period 10.0 [get_ports clk1]

# Async clock groups: no timing paths between clk0 and clk1
set_clock_groups -logically_exclusive -group {clk0} -group {clk1}

# sel and clk_en are async control signals; false path to clock outputs
set_false_path -from [get_ports sel]    -to [get_ports clk_out]
set_false_path -from [get_ports clk_en] -to [get_ports clk_out]

# Preserve latch-based clock mux structure for DFT / physical awareness
set_dont_touch [get_cells en0_latch_reg*]  ;# if synth names latches this way
set_dont_touch [get_cells en1_latch_reg*]
