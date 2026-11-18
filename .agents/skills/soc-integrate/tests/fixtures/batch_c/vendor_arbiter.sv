// A vendor diagnostic fixture with two combinational writers.
module vendor_arbiter(input logic [1:0] a, output logic [1:0] y);
    logic [1:0] tree;
    assign tree[0] = a[0];
    always_comb begin
        tree[1] = a[1];
        tree[0] = a[0] ^ a[1];
    end
    assign y = tree;
endmodule
