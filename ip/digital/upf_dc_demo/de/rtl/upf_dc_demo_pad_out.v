`ifndef SYNTHESIS
module upf_dc_demo_pad_out (
    input wire core_i,
    output wire pad_o
);
  assign pad_o = core_i;
endmodule
`endif
