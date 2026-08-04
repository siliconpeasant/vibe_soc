// Module   : rstn_test_mux
// Function : Select functional reset vs DFT test reset (active-low).
//            Port names match crg-gen: test_md / rstn_in / test_rstn / rstn_out.

module rstn_test_mux (
    input  wire test_md,
    input  wire rstn_in,
    input  wire test_rstn,
    output wire rstn_out
);

    std_cell_mux #(
        .WIDTH(1)
    ) u_mux (
        .sel (test_md),
        .a   (rstn_in),
        .b   (test_rstn),
        .y   (rstn_out)
    );

endmodule
