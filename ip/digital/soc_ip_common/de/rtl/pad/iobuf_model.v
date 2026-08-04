// Module   : iobuf_model
// Function : Behavioral GPIO pad model for RTL / DV smoke (io-top-gen).
//            Not a foundry cell — replace with process IO library for PD.

`timescale 1ns / 1ps

module iobuf_model (
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

    // Drive pad when output enable is active-low (oen=0).
    assign pad = oen ? 1'bz : i;

    // Simple pull modeling when undriven.
    wire pad_pulled;
    assign pad_pulled = (pad === 1'bz) ? (pu ? 1'b1 : (pd ? 1'b0 : 1'bx)) : pad;

    assign c = ie ? pad_pulled : 1'b0;

    // ds/st reserved for drive strength / schmitt — unused in behavioral model.
    wire unused = |{ds, st};

endmodule
