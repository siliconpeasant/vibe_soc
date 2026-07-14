`ifndef SYNTHESIS
module upf_dc_demo_pad_in (
    input wire pad_i,
    output wire core_o,
    inout wire VDDIO,
    inout wire VSSIO
);
  wire powered = (VDDIO === 1'b1) && (VSSIO === 1'b0);
  assign core_o = powered ? pad_i : 1'b0;
endmodule
`endif
