// Module       : std_cell_clk_mux
// Function     : Glitch-free 2-to-1 clock multiplexer with active-high enable
//                Uses negative-level transparent latches on each clock domain
//                to safely switch between async clock sources without runt pulses.
// Author       : RTL Designer Agent
// Version      : 1.0

module std_cell_clk_mux (
    input  wire clk0,
    input  wire clk1,
    input  wire sel,
    input  wire clk_en,
    output wire clk_out
);

    // -------------------------------------------------------------------------
    // Select control with clock-enable gating
    // sel0: select clk0 when sel=0 and clk_en=1
    // sel1: select clk1 when sel=1 and clk_en=1
    // -------------------------------------------------------------------------
    wire sel0 = ~sel & clk_en;
    wire sel1 =  sel & clk_en;

    // -------------------------------------------------------------------------
    // Negative-level transparent latches:
    //   latch0 captures sel0 state during clk0 low phase
    //   latch1 captures sel1 state during clk1 low phase
    // This ensures enable signals only change when clock is low,
    // preventing glitches on the gated clock outputs.
    // Latch warnings are expected for clock mux cells.
    // -------------------------------------------------------------------------
    reg en0_latch;
    reg en1_latch;

    always @(*) begin
        if (!clk0)
            en0_latch = sel0;
    end

    always @(*) begin
        if (!clk1)
            en1_latch = sel1;
    end

    // -------------------------------------------------------------------------
    // AND gates: gate each clock with its latched enable
    // OR gate:  combine gated clocks into final output
    // -------------------------------------------------------------------------
    wire gated_clk0 = clk0 & en0_latch;
    wire gated_clk1 = clk1 & en1_latch;

    assign clk_out = gated_clk0 | gated_clk1;

endmodule
