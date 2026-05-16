// Module       : std_cell_icg
// Function     : Positive-edge Integrated Clock Gating Cell (ICG)
//                Active-low transparent latch captures (en | test_en) when clk is low,
//                AND gate produces gated_clk = clk & en_latch.
// Author       : RTL Designer Agent
// Version      : 1.0

`timescale 1ns / 1ps

module std_cell_icg (
    input  wire clk,
    input  wire en,
    input  wire test_en,
    output wire gated_clk
);

    // Active-low transparent latch: transparent when clk is low
    // This is the standard ICG structure; latch warning is expected.
    reg en_latch;
    always @(*) begin
        if (!clk)
            en_latch = en | test_en;
    end

    // AND gate: gated clock only rises when en_latch is high
    assign gated_clk = clk & en_latch;

endmodule
