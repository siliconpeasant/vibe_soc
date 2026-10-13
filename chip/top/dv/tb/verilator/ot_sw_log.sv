// Keep the default VCS/UVM filelist inert without the Verilator status define.
`ifdef VERILATOR_TEST_STATUS_ADDR
// Optional observation of the sim_dv software log window; no DUT driving.
module ot_sw_log (
  input logic clk_i,
  input logic rst_ni,
  input logic wr_valid,
  input logic [31:0] addr,
  input logic [31:0] data
);
  bit enabled;
  initial enabled = $test$plusargs("ot_debug_sw");
  always @(posedge clk_i) begin
    if (enabled && rst_ni && wr_valid && addr == (`VERILATOR_TEST_STATUS_ADDR + 4))
      $display("OT_SW_LOG %0t %08x", $time, data);
  end
endmodule

bind sim_sram ot_sw_log u_ot_sw_log (
  .clk_i,
  .rst_ni,
  .wr_valid(u_sim_sram_if.wr_valid),
  .addr(u_sim_sram_if.tl_h2d.a_address),
  .data(u_sim_sram_if.tl_h2d.a_data)
);
`endif
