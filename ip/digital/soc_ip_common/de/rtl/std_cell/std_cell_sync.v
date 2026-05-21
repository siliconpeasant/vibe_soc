// Module       : std_cell_sync
// Function     : Multi-stage bit synchronizer (generic async-to-sync bridge).
//                Shifts async_in through STAGES DFFs on clk rising edge.
//                Default 2 stages; usable up to 8 for high-MTBF scenarios.
//                Active-low async reset clears the entire chain.
// Author       : RTL Designer Agent
// Version      : 1.0

module std_cell_sync #(
    parameter STAGES = 2
)(
    input  wire clk,
    input  wire rst_n,
    input  wire async_in,
    output wire sync_out
);

    // -------------------------------------------------------------------------
    // Synchronizer chain
    // -------------------------------------------------------------------------
    reg [STAGES-1:0] sync_chain;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sync_chain <= {STAGES{1'b0}};
        else
            sync_chain <= {sync_chain[STAGES-2:0], async_in};
    end

    assign sync_out = sync_chain[STAGES-1];

endmodule
