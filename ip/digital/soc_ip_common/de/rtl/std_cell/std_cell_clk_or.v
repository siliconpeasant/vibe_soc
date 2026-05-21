// Module       : std_cell_clk_or
// Function     : Clock-domain OR gate for glitch-free clock multiplexer output.
//                Combines multiple gated clock branches into a single clock tree.
//                Identical logic to std_cell_or but marked for clock-path usage.
// Author       : RTL Designer Agent
// Version      : 1.0

module std_cell_clk_or (
    input  wire a,
    input  wire b,
    output wire y
);

    assign y = a | b;

endmodule
