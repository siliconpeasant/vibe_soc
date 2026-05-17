module rstn_test_mux (
    input  wire rst_n,
    input  wire test_rst_n,
    input  wire test_mode,
    output wire rst_n_out
);

    std_cell_mux #(
        .WIDTH(1)
    ) u_mux (
        .sel (test_mode),
        .a   (rst_n),
        .b   (test_rst_n),
        .y   (rst_n_out)
    );

endmodule
