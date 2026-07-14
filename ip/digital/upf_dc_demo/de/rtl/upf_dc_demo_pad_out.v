`ifndef SYNTHESIS
module upf_dc_demo_pad_out (
    input wire core_i,
    output wire pad_o,
    inout wire VDDIO,
    inout wire VSSIO
);
  wire powered = (VDDIO === 1'b1) && (VSSIO === 1'b0);
  assign pad_o = powered ? core_i : 1'b0;
endmodule
`endif
