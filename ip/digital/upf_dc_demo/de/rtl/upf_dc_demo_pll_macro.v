`ifndef SYNTHESIS
module upf_dc_demo_pll_macro (
    input wire ref_clk_i,
    input wire rst_n,
    input wire enable_i,
    output wire pll_clk_o,
    output reg locked_o
);
  reg [2:0] lock_count;
  assign pll_clk_o = enable_i ? ref_clk_i : 1'b0;
  always @(posedge ref_clk_i or negedge rst_n) begin
    if (!rst_n) begin
      lock_count <= 3'd0;
      locked_o   <= 1'b0;
    end else if (!enable_i) begin
      lock_count <= 3'd0;
      locked_o   <= 1'b0;
    end else if (!locked_o) begin
      if (lock_count == 3'd3)
        locked_o <= 1'b1;
      else
        lock_count <= lock_count + 3'd1;
    end
  end
endmodule
`endif
