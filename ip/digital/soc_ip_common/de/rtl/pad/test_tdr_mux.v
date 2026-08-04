// Module   : test_tdr_mux
// Function : DFT / functional select for pad control signals (io-top-gen).
//            When test_mode=1 force functional path off (safe default for smoke).

`timescale 1ns / 1ps

module test_tdr_mux #(
    parameter WIDTH = 1
) (
    input  wire             test_mode,
    input  wire [WIDTH-1:0] func,
    output wire [WIDTH-1:0] dft
);

    assign dft = test_mode ? {WIDTH{1'b0}} : func;

endmodule
