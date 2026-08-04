// Module   : std_cell_clk_mux
// Function : 2:1 clock mux (combinational). Port names match crg-gen.
// Notes    : For glitch-sensitive paths use clk_glitch_free_switch / mux.

module std_cell_clk_mux (
    input  wire clk_in0,
    input  wire clk_in1,
    input  wire clk_sel,
    output wire clk_out
);

    assign clk_out = clk_sel ? clk_in1 : clk_in0;

endmodule
