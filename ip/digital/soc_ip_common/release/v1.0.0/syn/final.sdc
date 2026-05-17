# rstn_test_mux constraints
# Pure combinational module — no clocks, only max delay constraints

set_max_delay -from [get_ports rst_n]       -to [get_ports rst_n_out] 2.0
set_max_delay -from [get_ports test_rst_n]  -to [get_ports rst_n_out] 2.0
set_max_delay -from [get_ports test_mode]   -to [get_ports rst_n_out] 2.0

# Preserve std_cell_mux instance for DFT visibility
set_dont_touch [get_cells u_mux]
