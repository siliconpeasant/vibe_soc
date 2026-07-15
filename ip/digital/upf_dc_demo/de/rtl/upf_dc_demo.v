// Teaching-only five-domain UPF/DC integration demo.
module upf_dc_demo (
    input  wire       clk,
    input  wire       rst_n,

    input  wire       sw_clk,
    input  wire       sw_power_req_i,
    input  wire [7:0] sw_req_data_i,
    input  wire       sw_req_valid_i,
    output wire [7:0] sw_rsp_data_o,
    output wire       sw_rsp_valid_o,
    output wire       sw_powered_o,
    output wire       sw_isolated_o,

    input  wire       acc_clk,
    input  wire       acc_power_req_i,
    input  wire [7:0] acc_req_data_i,
    input  wire       acc_req_valid_i,
    output wire [7:0] acc_rsp_data_o,
    output wire       acc_rsp_valid_o,
    output wire       acc_powered_o,
    output wire       acc_isolated_o,

    input  wire       peri_clk,
    input  wire       peri_power_req_i,
    input  wire [7:0] peri_req_data_i,
    input  wire       peri_req_valid_i,
    output wire [7:0] peri_rsp_data_o,
    output wire       peri_rsp_valid_o,
    output wire       peri_powered_o,
    output wire       peri_isolated_o,

    input  wire       media_clk,
    input  wire       media_power_req_i,
    input  wire [7:0] media_req_data_i,
    input  wire       media_req_valid_i,
    output wire [7:0] media_rsp_data_o,
    output wire       media_rsp_valid_o,
    output wire       media_powered_o,
    output wire       media_isolated_o,

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
  wire       sw_traffic_enable;
  wire [7:0] sw_core_rsp_data;
  wire       sw_core_rsp_valid;
  wire       acc_en;
  wire       acc_iso_n;
  wire       acc_traffic_enable;
  wire [7:0] acc_core_rsp_data;
  wire       acc_core_rsp_valid;
  wire       peri_en;
  wire       peri_iso_n;
  wire       peri_traffic_enable;
  wire [7:0] peri_core_rsp_data;
  wire       peri_core_rsp_valid;
  wire       media_en;
  wire       media_iso_n;
  wire       media_traffic_enable;
  wire [7:0] media_core_rsp_data;
  wire       media_core_rsp_valid;

  assign sw_powered_o     = sw_en;
  assign sw_isolated_o    = ~sw_iso_n;
  assign acc_powered_o    = acc_en;
  assign acc_isolated_o   = ~acc_iso_n;
  assign peri_powered_o   = peri_en;
  assign peri_isolated_o  = ~peri_iso_n;
  assign media_powered_o  = media_en;
  assign media_isolated_o = ~media_iso_n;

  upf_dc_demo_aon_ctrl u_aon_ctrl (
      .clk(clk), .rst_n(rst_n), .sw_power_req_i(sw_power_req_i),
      .core_rsp_data_i(sw_core_rsp_data), .core_rsp_valid_i(sw_core_rsp_valid),
      .sw_en_o(sw_en), .sw_iso_n_o(sw_iso_n),
      .traffic_enable_o(sw_traffic_enable),
      .rsp_data_o(sw_rsp_data_o), .rsp_valid_o(sw_rsp_valid_o)
  );

  upf_dc_demo_aon_ctrl u_acc_aon_ctrl (
      .clk(clk), .rst_n(rst_n), .sw_power_req_i(acc_power_req_i),
      .core_rsp_data_i(acc_core_rsp_data), .core_rsp_valid_i(acc_core_rsp_valid),
      .sw_en_o(acc_en), .sw_iso_n_o(acc_iso_n),
      .traffic_enable_o(acc_traffic_enable),
      .rsp_data_o(acc_rsp_data_o), .rsp_valid_o(acc_rsp_valid_o)
  );

  upf_dc_demo_aon_ctrl u_peri_aon_ctrl (
      .clk(clk), .rst_n(rst_n), .sw_power_req_i(peri_power_req_i),
      .core_rsp_data_i(peri_core_rsp_data), .core_rsp_valid_i(peri_core_rsp_valid),
      .sw_en_o(peri_en), .sw_iso_n_o(peri_iso_n),
      .traffic_enable_o(peri_traffic_enable),
      .rsp_data_o(peri_rsp_data_o), .rsp_valid_o(peri_rsp_valid_o)
  );

  upf_dc_demo_aon_ctrl u_media_aon_ctrl (
      .clk(clk), .rst_n(rst_n), .sw_power_req_i(media_power_req_i),
      .core_rsp_data_i(media_core_rsp_data), .core_rsp_valid_i(media_core_rsp_valid),
      .sw_en_o(media_en), .sw_iso_n_o(media_iso_n),
      .traffic_enable_o(media_traffic_enable),
      .rsp_data_o(media_rsp_data_o), .rsp_valid_o(media_rsp_valid_o)
  );

  upf_dc_demo_sw_core u_sw_core (
      .clk(sw_clk), .rst_n(rst_n), .pwr_on_i(sw_en),
      .req_data_i(sw_req_data_i),
      .req_valid_i(sw_req_valid_i & sw_traffic_enable),
      .rsp_data_o(sw_core_rsp_data), .rsp_valid_o(sw_core_rsp_valid)
  );

  upf_dc_demo_sw_core u_acc_core (
      .clk(acc_clk), .rst_n(rst_n), .pwr_on_i(acc_en),
      .req_data_i(acc_req_data_i),
      .req_valid_i(acc_req_valid_i & acc_traffic_enable),
      .rsp_data_o(acc_core_rsp_data), .rsp_valid_o(acc_core_rsp_valid)
  );

  upf_dc_demo_sw_core u_peri_core (
      .clk(peri_clk), .rst_n(rst_n), .pwr_on_i(peri_en),
      .req_data_i(peri_req_data_i),
      .req_valid_i(peri_req_valid_i & peri_traffic_enable),
      .rsp_data_o(peri_core_rsp_data), .rsp_valid_o(peri_core_rsp_valid)
  );

  upf_dc_demo_sw_core u_media_core (
      .clk(media_clk), .rst_n(rst_n), .pwr_on_i(media_en),
      .req_data_i(media_req_data_i),
      .req_valid_i(media_req_valid_i & media_traffic_enable),
      .rsp_data_o(media_core_rsp_data), .rsp_valid_o(media_core_rsp_valid)
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
