// Module      : std_cell_buf
// Function    : Parameterized width buffer (pass-through)
// Author      : vibe_soc RTL designer
// Version     : 1.0
// Description : Combinational standard cell, y = a (maps to BUF cell after synthesis)

`timescale 1ns / 1ps

module std_cell_buf #(
    parameter WIDTH = 1
)(
    input  wire [WIDTH-1:0] a,
    output wire [WIDTH-1:0] y
);

    assign y = a;

endmodule
