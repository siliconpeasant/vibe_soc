// Module   : clk_buf_for_occ
// Function : Clock buffer placeholder used by crg-gen OCC / test clock paths.

module clk_buf_for_occ (
    input  wire clkin,
    output wire clkout
);

    std_cell_buf #(
        .WIDTH(1)
    ) u_buf (
        .a (clkin),
        .y (clkout)
    );

endmodule
