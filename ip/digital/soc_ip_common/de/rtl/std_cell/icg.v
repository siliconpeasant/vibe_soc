// Module   : icg
// Function : CRG-generator-compatible clock gate wrapper around std_cell_icg.

module icg (
    input  wire clkin,
    input  wire enable,
    input  wire icg_test_mode,
    output wire clkout
);

    std_cell_icg u_icg (
        .clk       (clkin),
        .en        (enable),
        .test_en   (icg_test_mode),
        .gated_clk (clkout)
    );

endmodule
