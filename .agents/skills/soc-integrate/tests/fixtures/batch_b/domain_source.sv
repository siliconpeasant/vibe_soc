module domain_source(input tick, input reset_n, input data_i, output reg data_o);
    always @(posedge tick or negedge reset_n) begin
        if (!reset_n) begin
            data_o <= 1'b0;
        end else begin
            data_o <= data_i;
        end
    end
endmodule
