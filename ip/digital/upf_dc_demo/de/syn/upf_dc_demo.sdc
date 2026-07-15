create_clock -name clk -period 10.000 [get_ports clk]
create_clock -name sw_clk -period 10.000 [get_ports sw_clk]
set_clock_uncertainty 0.10 [get_clocks {clk sw_clk}]
set_clock_transition 0.10 [get_clocks {clk sw_clk}]

set_input_delay 1.0 -clock clk [get_ports {sw_power_req_i req_data_i[*] req_valid_i mem_cs_i mem_we_i mem_addr_i[*] mem_wdata_i[*] pll_enable_i pad_in_i pad_out_core_i}]
set_output_delay 1.0 -clock clk [get_ports {rsp_data_o[*] rsp_valid_o sw_powered_o sw_isolated_o mem_rdata_o[*] mem_rvalid_o pll_clk_mon_o pll_locked_o pad_in_core_o pad_out_o}]
set_load 0.05 [get_ports {rsp_data_o[*] rsp_valid_o sw_powered_o sw_isolated_o mem_rdata_o[*] mem_rvalid_o pll_clk_mon_o pll_locked_o pad_in_core_o pad_out_o}]

set_false_path -from [get_ports rst_n]
