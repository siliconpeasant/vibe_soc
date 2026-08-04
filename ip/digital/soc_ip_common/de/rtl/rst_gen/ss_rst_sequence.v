// Module   : ss_rst_sequence
// Function : Subsystem reset sequencer used by crg-gen.
//            Combines POR, software reset, power-ready, and DFT test reset.

module ss_rst_sequence (
    input  wire       clk_in,
    input  wire       por_sys_n,
    input  wire [2:0] sw_rst,
    input  wire       test_mode,
    input  wire       test_rstn,
    input  wire       ss_pwr_rdy,
    output wire       clk_gen_rst_n,
    output wire       ss_rst_n
);

    wire func_por_n      = por_sys_n & ss_pwr_rdy & ~(|sw_rst);
    wire clk_gen_func_n  = por_sys_n & ~(|sw_rst);
    wire ss_rst_n_func;
    wire clk_gen_rst_n_func;

    // Functional async assert, sync release for subsystem reset.
    rst_synchronizer #(
        .STAGES(3)
    ) u_ss_sync (
        .clk         (clk_in),
        .rst_async_n (func_por_n),
        .rst_sync_n  (ss_rst_n_func)
    );

    rstn_test_mux u_ss_test (
        .test_md   (test_mode),
        .rstn_in   (ss_rst_n_func),
        .test_rstn (test_rstn),
        .rstn_out  (ss_rst_n)
    );

    rst_synchronizer #(
        .STAGES(2)
    ) u_cg_sync (
        .clk         (clk_in),
        .rst_async_n (clk_gen_func_n),
        .rst_sync_n  (clk_gen_rst_n_func)
    );

    rstn_test_mux u_cg_test (
        .test_md   (test_mode),
        .rstn_in   (clk_gen_rst_n_func),
        .test_rstn (test_rstn),
        .rstn_out  (clk_gen_rst_n)
    );

endmodule
