// Teaching-only two-domain UPF/DC integration demo.
module upf_dc_demo (
    input  wire       clk,
    input  wire       sw_clk,
    input  wire       rst_n,
    input  wire       sw_power_req_i,
    input  wire [7:0] req_data_i,
    input  wire       req_valid_i,
    output wire [7:0] rsp_data_o,
    output wire       rsp_valid_o,
    output wire       sw_powered_o,
    output wire       sw_isolated_o,
    input  wire       mem_cs_i,
    input  wire       mem_we_i,
    input  wire [3:0] mem_addr_i,
    input  wire [7:0] mem_wdata_i,
    output wire [7:0] mem_rdata_o,
    output wire       mem_rvalid_o,
    input  wire       pll_enable_i,
    output wire       pll_clk_mon_o,
    output wire       pll_locked_o,
    input  wire       pad_in_i,
    output wire       pad_in_core_o,
    input  wire       pad_out_core_i,
    output wire       pad_out_o
);

  wire       sw_en;
  wire       sw_iso_n;
  wire       traffic_enable;
  wire [7:0] core_rsp_data;
  wire       core_rsp_valid;

  assign sw_powered_o  = sw_en;
  assign sw_isolated_o = ~sw_iso_n;

  upf_dc_demo_aon_ctrl u_aon_ctrl (
      .clk(clk), .rst_n(rst_n), .sw_power_req_i(sw_power_req_i),
      .core_rsp_data_i(core_rsp_data), .core_rsp_valid_i(core_rsp_valid),
      .sw_en_o(sw_en), .sw_iso_n_o(sw_iso_n),
      .traffic_enable_o(traffic_enable),
      .rsp_data_o(rsp_data_o), .rsp_valid_o(rsp_valid_o)
  );

  upf_dc_demo_sw_core u_sw_core (
      .clk(sw_clk), .rst_n(rst_n), .pwr_on_i(sw_en),
      .req_data_i(req_data_i),
      .req_valid_i(req_valid_i & traffic_enable),
      .rsp_data_o(core_rsp_data), .rsp_valid_o(core_rsp_valid)
  );

  upf_dc_demo_pll_macro u_pll_macro (
      .ref_clk_i(clk), .rst_n(rst_n), .enable_i(pll_enable_i),
      .pll_clk_o(pll_clk_mon_o), .locked_o(pll_locked_o)
  );

  upf_dc_demo_sram_16x8 u_sram_macro (
      .clk(clk), .rst_n(rst_n), .cs_i(mem_cs_i), .we_i(mem_we_i),
      .addr_i(mem_addr_i), .wdata_i(mem_wdata_i),
      .rdata_o(mem_rdata_o), .rvalid_o(mem_rvalid_o)
  );

  upf_dc_demo_pad_in u_pad_in (
      .pad_i(pad_in_i), .core_o(pad_in_core_o)
  );

  upf_dc_demo_pad_out u_pad_out (
      .core_i(pad_out_core_i), .pad_o(pad_out_o)
  );
endmodule
