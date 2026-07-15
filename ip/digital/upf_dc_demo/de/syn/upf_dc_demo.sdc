create_clock -name clk -period 10.000 [get_ports clk]
create_clock -name sw_clk -period 10.000 [get_ports sw_clk]
create_clock -name acc_clk -period 10.000 [get_ports acc_clk]
create_clock -name peri_clk -period 10.000 [get_ports peri_clk]
create_clock -name media_clk -period 10.000 [get_ports media_clk]
set_clock_uncertainty 0.10 [get_clocks {clk sw_clk acc_clk peri_clk media_clk}]
set_clock_transition 0.10 [get_clocks {clk sw_clk acc_clk peri_clk media_clk}]

set_input_delay 1.0 -clock clk [get_ports {
  sw_power_req_i sw_req_data_i[*] sw_req_valid_i
  acc_power_req_i acc_req_data_i[*] acc_req_valid_i
  peri_power_req_i peri_req_data_i[*] peri_req_valid_i
  media_power_req_i media_req_data_i[*] media_req_valid_i
  mem_cs_i mem_we_i mem_addr_i[*] mem_wdata_i[*]
  pll_enable_i pad_in_i pad_out_core_i
}]
set_output_delay 1.0 -clock clk [get_ports {
  sw_rsp_data_o[*] sw_rsp_valid_o sw_powered_o sw_isolated_o
  acc_rsp_data_o[*] acc_rsp_valid_o acc_powered_o acc_isolated_o
  peri_rsp_data_o[*] peri_rsp_valid_o peri_powered_o peri_isolated_o
  media_rsp_data_o[*] media_rsp_valid_o media_powered_o media_isolated_o
  mem_rdata_o[*] mem_rvalid_o pll_clk_mon_o pll_locked_o pad_in_core_o pad_out_o
}]
set_load 0.05 [get_ports {
  sw_rsp_data_o[*] sw_rsp_valid_o sw_powered_o sw_isolated_o
  acc_rsp_data_o[*] acc_rsp_valid_o acc_powered_o acc_isolated_o
  peri_rsp_data_o[*] peri_rsp_valid_o peri_powered_o peri_isolated_o
  media_rsp_data_o[*] media_rsp_valid_o media_powered_o media_isolated_o
  mem_rdata_o[*] mem_rvalid_o pll_clk_mon_o pll_locked_o pad_in_core_o pad_out_o
}]

set_false_path -from [get_ports rst_n]
