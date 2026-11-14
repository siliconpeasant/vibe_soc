module counter (
    input wire clk_i,
    input wire rst_ni,
    input wire enable_i,
    output reg [3:0] count_o
);
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            count_o <= 4'b0000;
        end else if (enable_i) begin
            count_o <= count_o + 4'b0001;
        end
    end
endmodule
