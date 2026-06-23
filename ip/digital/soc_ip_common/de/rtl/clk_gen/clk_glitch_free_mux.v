// Module       : clk_glitch_free_mux
// Function     : Glitch-free 2-to-1 clock multiplexer.
//                Uses std_cell_sync + std_cell_icg standard cells.
//                sel is async-safe: each enable is synchronized to its target
//                clock domain via a 2-stage std_cell_sync, then gated by
//                std_cell_icg.  Feedback interlock (en0 & ~en1) ensures
//                break-before-make even when sel changes asynchronously.
// Author       : RTL Designer Agent
// Version      : 3.3

module clk_glitch_free_mux (
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    input  wire rst_n,
    input  wire test_mode,
    output wire clk_out
);

    // -------------------------------------------------------------------------
    // Feedback interlock: new clock can only enable after old clock is off.
    // The combinational cross-coupled AND forms a break-before-make latch.
    // sel0/sel1 are used directly (no intermediate wires) to reduce area.
    // -------------------------------------------------------------------------
    wire en0_sync;
    wire en1_sync;

    wire en0_raw = ~sel & ~en1_sync;
    wire en1_raw =  sel & ~en0_sync;

    // -------------------------------------------------------------------------
    // Synchronize each enable to its target clock domain (2-stage)
    // std_cell_sync: active-low async reset, posedge clk sampling
    // -------------------------------------------------------------------------

    std_cell_sync #(.STAGES(2)) u_sync_en0 (
        .clk       (clk0),
        .rst_n     (rst_n),
        .async_in  (en0_raw),
        .sync_out  (en0_sync)
    );

    std_cell_sync #(.STAGES(2)) u_sync_en1 (
        .clk       (clk1),
        .rst_n     (rst_n),
        .async_in  (en1_raw),
        .sync_out  (en1_sync)
    );

    // -------------------------------------------------------------------------
    // Clock gating with std_cell_icg standard cell
    // -------------------------------------------------------------------------
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

    // -------------------------------------------------------------------------
    // OR combine gated clocks with std_cell_or standard cell
    // -------------------------------------------------------------------------
    std_cell_clk_or u_or (
        .a (gated_clk0),
        .b (gated_clk1),
        .y (clk_out)
    );

endmodule
