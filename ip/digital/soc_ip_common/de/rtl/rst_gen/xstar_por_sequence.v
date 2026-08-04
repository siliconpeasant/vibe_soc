// Module   : xstar_por_sequence
// Function : Multi-domain POR filter / distributor used by crg-gen.
//            Filters pad POR with optional software reset and DFT override.

module xstar_por_sequence (
    input  wire       clk_38p4m,
    input  wire       demo_32k_clk,
    input  wire       pad_por_n,
    input  wire [2:0] sw_rst,
    input  wire       test_mode,
    input  wire       test_rstn,
    output wire       por_flt_n,
    output wire       por_sc_n,
    output wire       por_sys_n
);

    wire por_raw_n = pad_por_n & ~(|sw_rst);
    wire por_flt_n_func;
    wire por_sc_n_func;
    wire por_sys_n_func;

    // Filter POR on fast clock (stretch/sync).
    rst_synchronizer #(
        .STAGES(4)
    ) u_flt (
        .clk         (clk_38p4m),
        .rst_async_n (por_raw_n),
        .rst_sync_n  (por_flt_n_func)
    );

    // Slow-clock copy for always-on / SC domain.
    rst_synchronizer #(
        .STAGES(3)
    ) u_sc (
        .clk         (demo_32k_clk),
        .rst_async_n (por_raw_n),
        .rst_sync_n  (por_sc_n_func)
    );

    assign por_sys_n_func = por_flt_n_func;

    rstn_test_mux u_flt_tm (
        .test_md   (test_mode),
        .rstn_in   (por_flt_n_func),
        .test_rstn (test_rstn),
        .rstn_out  (por_flt_n)
    );

    rstn_test_mux u_sc_tm (
        .test_md   (test_mode),
        .rstn_in   (por_sc_n_func),
        .test_rstn (test_rstn),
        .rstn_out  (por_sc_n)
    );

    rstn_test_mux u_sys_tm (
        .test_md   (test_mode),
        .rstn_in   (por_sys_n_func),
        .test_rstn (test_rstn),
        .rstn_out  (por_sys_n)
    );

endmodule
