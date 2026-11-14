module glue_sink(
    input logic clk_i,
    input logic rst_ni,
    input logic [1:0] select_i,
    input logic valid_i,
    input logic irq_i,
    output logic response_o
);
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            response_o <= 1'b0;
        end else begin
            response_o <= (^select_i) ^ valid_i ^ irq_i;
        end
    end
endmodule
