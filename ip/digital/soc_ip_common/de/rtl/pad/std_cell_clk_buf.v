// Module   : std_cell_clk_buf
// Function : Named clock buffer used by io-top-gen pin_mux dontouch paths.
//            Port names match generator: clk_buf_in / clk_buf_out.

`timescale 1ns / 1ps

module std_cell_clk_buf (
    input  wire clk_buf_in,
    output wire clk_buf_out
);

    std_cell_buf #(
        .WIDTH(1)
    ) u_buf (
        .a (clk_buf_in),
        .y (clk_buf_out)
    );

endmodule
