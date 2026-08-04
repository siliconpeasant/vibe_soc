// Module   : iobuf_s_model
// Function : Behavioral special-purpose pad (e.g. reset) for io-top-gen smoke.
//            Same pinout as iobuf_model; default pull-up when undriven.

`timescale 1ns / 1ps

module iobuf_s_model (
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
    // Prefer pull-up for reset-class pads when neither side drives.
    assign pad_pulled = (pad === 1'bz) ? (pd ? 1'b0 : 1'b1) : pad;

    assign c = ie ? pad_pulled : 1'b0;

    wire unused = |{ds, st, pu};

endmodule
