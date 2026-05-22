module std_cell_clk_mux (
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    output wire clk_out
);

    assign clk_out = sel ? clk1 : clk0;

endmodule
