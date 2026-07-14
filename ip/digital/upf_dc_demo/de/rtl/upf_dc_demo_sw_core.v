module upf_dc_demo_sw_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       pwr_on_i,
    input  wire [7:0] req_data_i,
    input  wire       req_valid_i,
    output reg  [7:0] rsp_data_o,
    output reg        rsp_valid_o
);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rsp_data_o  <= 8'h00;
      rsp_valid_o <= 1'b0;
    end else if (!pwr_on_i) begin
      rsp_data_o  <= 8'h00;
      rsp_valid_o <= 1'b0;
    end else begin
      rsp_valid_o <= req_valid_i;
      if (req_valid_i)
        rsp_data_o <= req_data_i + 8'h01;
    end
  end
endmodule
