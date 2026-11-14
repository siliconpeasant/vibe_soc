module gpio (
    input wire [7:0] data_i,
    output wire [7:0] data_o
);
    assign data_o = data_i;
endmodule
