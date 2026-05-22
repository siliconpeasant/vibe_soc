// pcie - Self-Developed IP Template
// TODO: Replace with actual IP logic

`timescale 1ns / 1ps

module pcie (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  data_in,
    input  wire        valid_in,
    output reg  [7:0]  data_out,
    output reg         valid_out
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out  <= 8'b0;
            valid_out <= 1'b0;
        end else if (valid_in) begin
            data_out  <= data_in + 1'b1;  // Example logic
            valid_out <= 1'b1;
        end else begin
            valid_out <= 1'b0;
        end
    end

endmodule
