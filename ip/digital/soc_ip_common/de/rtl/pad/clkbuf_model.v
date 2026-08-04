// Module   : clkbuf_model
// Function : Behavioral clock pad model for io-top-gen (input-centric).
//            When oen=0 can drive pad for test; otherwise pad is input.

`timescale 1ns / 1ps

module clkbuf_model (
    input  wire       oen,
    input  wire       i,
    input  wire       ie,
    input  wire [3:0] ds,
    input  wire [1:0] st,
    input  wire       pu,
    input  wire       pd,
    output wire       c,
    inout  wire       pad
);

    assign pad = oen ? 1'bz : i;

    wire pad_pulled;
    assign pad_pulled = (pad === 1'bz) ? (pu ? 1'b1 : (pd ? 1'b0 : 1'b0)) : pad;

    assign c = ie ? pad_pulled : 1'b0;

    wire unused = |{ds, st};

endmodule
