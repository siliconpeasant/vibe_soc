`ifndef SYNTHESIS
module upf_dc_demo_pad_in (
    input wire pad_i,
    output wire core_o
);
  assign core_o = pad_i;
endmodule
`endif
