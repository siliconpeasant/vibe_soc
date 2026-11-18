// Original fixture: header imports, array parameters and assertion macros.
`include "assertions.svh"
module peripheral
  import demo_pkg::*;
#(
  parameter policy_t Policy[NumRegs] = '{NumRegs{0}},
  parameter int Width = 4
) (
  input logic clk_i,
  input logic rst_ni,
  input demo_pkg::h2d_t tl_i,
  output logic [Width-1:0] data_o
);
  assign data_o = {Width{(^tl_i) & rst_ni & (^Policy[0]) & (^Policy[1])}};
  `CHECK(CheckReset, rst_ni |-> rst_ni)
endmodule
