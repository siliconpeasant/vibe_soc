// Module      : std_cell_inv
// Function    : Parameterized width inverter (NOT gate)
// Author      : vibe_soc RTL designer
// Version     : 1.0
// Description : Combinational standard cell, y = ~a

module std_cell_inv #(
    parameter WIDTH = 1
)(
    input  wire [WIDTH-1:0] a,
    output wire [WIDTH-1:0] y
);

    assign y = ~a;

endmodule
