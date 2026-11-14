module irq_source (
    input wire clk_i,
    input wire rst_ni,
    input wire [1:0] event_i,
    output wire intr_a_o,
    output reg [2:1] intr_b_o
);
    assign intr_a_o = ^intr_b_o;
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            intr_b_o <= '0;
        end else begin
            intr_b_o <= event_i;
        end
    end
endmodule
