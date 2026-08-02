// Generator-compatible stub: positional ports, parameter WIDTH
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
