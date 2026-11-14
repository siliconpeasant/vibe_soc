module irq_sink (
    input wire clk_i,
    input wire rst_ni,
    input wire [7:0] intr_src_i,
    output reg irq_o
);
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            irq_o <= 1'b0;
        end else begin
            irq_o <= |intr_src_i;
        end
    end
endmodule
