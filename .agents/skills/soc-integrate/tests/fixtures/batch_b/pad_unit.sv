module pad_unit #(parameter N=2) (
    input wire clk_i,
    input wire rst_ni,
    input wire enable_i,
    input wire pad_i,
    input wire [N-1:0] config_i,
    output wire tx_o,
    output reg [N-1:0] intr_o,
    output wire status_o
);
    assign tx_o = pad_i ^ enable_i;
    assign status_o = |intr_o;
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            intr_o <= '0;
        end else begin
            intr_o <= config_i & {N{enable_i}};
        end
    end
endmodule
