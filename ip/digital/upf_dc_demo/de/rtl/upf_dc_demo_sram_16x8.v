`ifndef SYNTHESIS
module upf_dc_demo_sram_16x8 (
    input wire clk,
    input wire rst_n,
    input wire cs_i,
    input wire we_i,
    input wire [3:0] addr_i,
    input wire [7:0] wdata_i,
    output reg [7:0] rdata_o,
    output reg rvalid_o
);
  reg [7:0] mem [0:15];
  integer index;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rdata_o  <= 8'h00;
      rvalid_o <= 1'b0;
      for (index = 0; index < 16; index = index + 1)
        mem[index] <= 8'h00;
    end else begin
      rvalid_o <= 1'b0;
      if (cs_i) begin
        if (we_i)
          mem[addr_i] <= wdata_i;
        else begin
          rdata_o  <= mem[addr_i];
          rvalid_o <= 1'b1;
        end
      end
    end
  end
endmodule
`endif
