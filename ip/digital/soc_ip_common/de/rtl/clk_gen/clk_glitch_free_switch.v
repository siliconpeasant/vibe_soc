// Module   : clk_glitch_free_switch
// Function : Glitch-free 2:1 clock switch with select status (crg-gen ports).
//            Built on the same break-before-make structure as clk_glitch_free_mux,
//            plus clk0_sel / clk1_sel / sel_done status for software polling.

module clk_glitch_free_switch (
    input  wire test_mode,
    input  wire rst0_n,
    input  wire rst1_n,
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    output wire clk0_sel,
    output wire clk1_sel,
    output wire sel_done,
    output wire clk_out
);

    wire en0_sync;
    wire en1_sync;
    wire en0_raw = ~sel & ~en1_sync;
    wire en1_raw =  sel & ~en0_sync;

    std_cell_sync #(.STAGES(2)) u_sync_en0 (
        .clk      (clk0),
        .rst_n    (rst0_n),
        .async_in (en0_raw),
        .sync_out (en0_sync)
    );

    std_cell_sync #(.STAGES(2)) u_sync_en1 (
        .clk      (clk1),
        .rst_n    (rst1_n),
        .async_in (en1_raw),
        .sync_out (en1_sync)
    );

    wire gated_clk0;
    wire gated_clk1;

    std_cell_icg u_icg0 (
        .clk       (clk0),
        .en        (en0_sync),
        .test_en   (test_mode),
        .gated_clk (gated_clk0)
    );

    std_cell_icg u_icg1 (
        .clk       (clk1),
        .en        (en1_sync),
        .test_en   (test_mode),
        .gated_clk (gated_clk1)
    );

    std_cell_clk_or u_or (
        .a (gated_clk0),
        .b (gated_clk1),
        .y (clk_out)
    );

    // Status: which source is currently enabled after sync.
    assign clk0_sel = en0_sync;
    assign clk1_sel = en1_sync;
    // Done when only one side is enabled and matches requested sel (or both off briefly).
    assign sel_done = (en0_sync ^ en1_sync) && ((sel == 1'b0 && en0_sync) || (sel == 1'b1 && en1_sync));

endmodule
