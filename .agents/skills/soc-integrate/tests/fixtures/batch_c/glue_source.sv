module glue_source(
    input logic [7:0] address_i,
    input logic request_i,
    output logic [7:0] address_o,
    output logic request_o,
    output logic [1:0] intr_o
);
    assign address_o = address_i;
    assign request_o = request_i;
    assign intr_o = address_i[1:0];
endmodule
