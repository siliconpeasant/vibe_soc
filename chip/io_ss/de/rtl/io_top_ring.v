// ============================================================================
// File Name    : io_top_ring.v
// Description  :
// Author       : autumn
// Created On   : 2026/08/02 13:16
// Last Modified: 2026/08/02 13:16
// ----------------------------------------------------------------------------
// Date         By           Version  Description
// ----------------------------------------------------------------------------
// 2026/08/02   autumn      1.0      Initial version
// ============================================================================
module io_top_ring(
	input               test_mode,
	//pad PAD_GPIO0
	inout        PAD_GPIO0,
	input        pad_gpio0_oe_n,
	input        pad_gpio0_i,
	input        pad_gpio0_ie,
	input  [3:0] pad_gpio0_ds,
	input  [1:0] pad_gpio0_st,
	input        pad_gpio0_pu,
	input        pad_gpio0_pd,
	input        pad_gpio0_sl,
	input        pad_gpio0_msc,
	input        pad_gpio0_ps,
	input        pad_gpio0_he,
	input        pad_gpio0_pe,
	output       pad_gpio0_c,
	//pad PAD_GPIO1
	inout        PAD_GPIO1,
	input        pad_gpio1_oe_n,
	input        pad_gpio1_i,
	input        pad_gpio1_ie,
	input  [3:0] pad_gpio1_ds,
	input  [1:0] pad_gpio1_st,
	input        pad_gpio1_pu,
	input        pad_gpio1_pd,
	input        pad_gpio1_sl,
	input        pad_gpio1_msc,
	input        pad_gpio1_ps,
	input        pad_gpio1_he,
	input        pad_gpio1_pe,
	output       pad_gpio1_c,
	//pad PAD_CLK
	inout        PAD_CLK,
	input        pad_clk_oe_n,
	input        pad_clk_i,
	input        pad_clk_ie,
	input  [3:0] pad_clk_ds,
	input  [1:0] pad_clk_st,
	input        pad_clk_pu,
	input        pad_clk_pd,
	output       pad_clk_c,
	//pad PAD_RST_N
	inout        PAD_RST_N,
	input        pad_rst_n_oe_n,
	input        pad_rst_n_i,
	input        pad_rst_n_ie,
	input  [3:0] pad_rst_n_ds,
	input  [1:0] pad_rst_n_st,
	input        pad_rst_n_pu,
	input        pad_rst_n_pd,
	input        pad_rst_n_sl,
	input        pad_rst_n_msc,
	input        pad_rst_n_ps,
	input        pad_rst_n_he,
	input        pad_rst_n_pe,
	output       pad_rst_n_c
);

wire         dft_pad_gpio0_i;
wire         dft_pad_gpio0_c;
wire         dft_pad_gpio0_oe_n;
wire         dft_pad_gpio0_ie;
wire    [3:0] dft_pad_gpio0_ds;
wire    [1:0] dft_pad_gpio0_st;
wire         dft_pad_gpio0_pu;
wire         dft_pad_gpio0_pd;
wire         dft_pad_gpio1_i;
wire         dft_pad_gpio1_c;
wire         dft_pad_gpio1_oe_n;
wire         dft_pad_gpio1_ie;
wire    [3:0] dft_pad_gpio1_ds;
wire    [1:0] dft_pad_gpio1_st;
wire         dft_pad_gpio1_pu;
wire         dft_pad_gpio1_pd;
wire         dft_pad_clk_i;
wire         dft_pad_clk_c;
wire         dft_pad_clk_oe_n;
wire         dft_pad_clk_ie;
wire    [3:0] dft_pad_clk_ds;
wire    [1:0] dft_pad_clk_st;
wire         dft_pad_clk_pu;
wire         dft_pad_clk_pd;
wire         dft_pad_rst_n_i;
wire         dft_pad_rst_n_c;
wire         dft_pad_rst_n_oe_n;
wire         dft_pad_rst_n_ie;
wire    [3:0] dft_pad_rst_n_ds;
wire    [1:0] dft_pad_rst_n_st;
wire         dft_pad_rst_n_pu;
wire         dft_pad_rst_n_pd;
    test_tdr_mux #(1) u_pad_gpio0_oe_n_test_tdr_mux( test_mode, pad_gpio0_oe_n      , dft_pad_gpio0_oe_n      );
    test_tdr_mux #(1) u_pad_gpio0_i_test_tdr_mux( test_mode, pad_gpio0_i      , dft_pad_gpio0_i      );
    test_tdr_mux #(1) u_pad_gpio0_ie_test_tdr_mux( test_mode, pad_gpio0_ie      , dft_pad_gpio0_ie      );
    test_tdr_mux #(1) u_pad_gpio0_pu_test_tdr_mux( test_mode, pad_gpio0_pu      , dft_pad_gpio0_pu      );
    test_tdr_mux #(1) u_pad_gpio0_pd_test_tdr_mux( test_mode, pad_gpio0_pd      , dft_pad_gpio0_pd      );
    test_tdr_mux #(4) u_pad_gpio0_ds_test_tdr_mux( test_mode, pad_gpio0_ds      , dft_pad_gpio0_ds      );
    test_tdr_mux #(2) u_pad_gpio0_st_test_tdr_mux( test_mode, pad_gpio0_st      , dft_pad_gpio0_st      );
`ifdef TSMC22
    assign dft_pad_gpio0_c = test_mode ? pad_gpio0_c : 1'b0;
    `STD_CLK_BUF_CELL u_buf_pad_gpio0(
         .Z          (   ),
         .I          (dft_pad_gpio0_c)
     );
`else
    assign dft_pad_gpio0_c = 1'b0;
`endif
    iobuf_model u_pad_gpio0_pad (
        .oen(dft_pad_gpio0_oe_n),
        .i  (dft_pad_gpio0_i  ),
        .ie (dft_pad_gpio0_ie ),
        .ds (dft_pad_gpio0_ds ),
        .st (dft_pad_gpio0_st ),
        .pu (dft_pad_gpio0_pu ),
        .pd (dft_pad_gpio0_pd ),
        .c  (pad_gpio0_c  ),
        .pad(PAD_GPIO0    )
        );

    test_tdr_mux #(1) u_pad_gpio1_oe_n_test_tdr_mux( test_mode, pad_gpio1_oe_n      , dft_pad_gpio1_oe_n      );
    test_tdr_mux #(1) u_pad_gpio1_i_test_tdr_mux( test_mode, pad_gpio1_i      , dft_pad_gpio1_i      );
    test_tdr_mux #(1) u_pad_gpio1_ie_test_tdr_mux( test_mode, pad_gpio1_ie      , dft_pad_gpio1_ie      );
    test_tdr_mux #(1) u_pad_gpio1_pu_test_tdr_mux( test_mode, pad_gpio1_pu      , dft_pad_gpio1_pu      );
    test_tdr_mux #(1) u_pad_gpio1_pd_test_tdr_mux( test_mode, pad_gpio1_pd      , dft_pad_gpio1_pd      );
    test_tdr_mux #(4) u_pad_gpio1_ds_test_tdr_mux( test_mode, pad_gpio1_ds      , dft_pad_gpio1_ds      );
    test_tdr_mux #(2) u_pad_gpio1_st_test_tdr_mux( test_mode, pad_gpio1_st      , dft_pad_gpio1_st      );
`ifdef TSMC22
    assign dft_pad_gpio1_c = test_mode ? pad_gpio1_c : 1'b0;
    `STD_CLK_BUF_CELL u_buf_pad_gpio1(
         .Z          (   ),
         .I          (dft_pad_gpio1_c)
     );
`else
    assign dft_pad_gpio1_c = 1'b0;
`endif
    iobuf_model u_pad_gpio1_pad (
        .oen(dft_pad_gpio1_oe_n),
        .i  (dft_pad_gpio1_i  ),
        .ie (dft_pad_gpio1_ie ),
        .ds (dft_pad_gpio1_ds ),
        .st (dft_pad_gpio1_st ),
        .pu (dft_pad_gpio1_pu ),
        .pd (dft_pad_gpio1_pd ),
        .c  (pad_gpio1_c  ),
        .pad(PAD_GPIO1    )
        );

    test_tdr_mux #(1) u_pad_clk_oe_n_test_tdr_mux( test_mode, pad_clk_oe_n      , dft_pad_clk_oe_n      );
    test_tdr_mux #(1) u_pad_clk_i_test_tdr_mux( test_mode, pad_clk_i      , dft_pad_clk_i      );
    test_tdr_mux #(1) u_pad_clk_ie_test_tdr_mux( test_mode, pad_clk_ie      , dft_pad_clk_ie      );
    test_tdr_mux #(1) u_pad_clk_pu_test_tdr_mux( test_mode, pad_clk_pu      , dft_pad_clk_pu      );
    test_tdr_mux #(1) u_pad_clk_pd_test_tdr_mux( test_mode, pad_clk_pd      , dft_pad_clk_pd      );
    test_tdr_mux #(4) u_pad_clk_ds_test_tdr_mux( test_mode, pad_clk_ds      , dft_pad_clk_ds      );
    test_tdr_mux #(2) u_pad_clk_st_test_tdr_mux( test_mode, pad_clk_st      , dft_pad_clk_st      );
`ifdef TSMC22
    assign dft_pad_clk_c = test_mode ? pad_clk_c : 1'b0;
    `STD_CLK_BUF_CELL u_buf_pad_clk(
         .Z          (   ),
         .I          (dft_pad_clk_c)
     );
`else
    assign dft_pad_clk_c = 1'b0;
`endif
    clkbuf_model u_pad_clk_pad (
        .oen(dft_pad_clk_oe_n),
        .i  (dft_pad_clk_i  ),
        .ie (dft_pad_clk_ie ),
        .ds (dft_pad_clk_ds ),
        .st (dft_pad_clk_st ),
        .pu (dft_pad_clk_pu ),
        .pd (dft_pad_clk_pd ),
        .c  (pad_clk_c  ),
        .pad(PAD_CLK    )
        );

    test_tdr_mux #(1) u_pad_rst_n_oe_n_test_tdr_mux( test_mode, pad_rst_n_oe_n      , dft_pad_rst_n_oe_n      );
    test_tdr_mux #(1) u_pad_rst_n_i_test_tdr_mux( test_mode, pad_rst_n_i      , dft_pad_rst_n_i      );
    test_tdr_mux #(1) u_pad_rst_n_ie_test_tdr_mux( test_mode, pad_rst_n_ie      , dft_pad_rst_n_ie      );
    test_tdr_mux #(1) u_pad_rst_n_pu_test_tdr_mux( test_mode, pad_rst_n_pu      , dft_pad_rst_n_pu      );
    test_tdr_mux #(1) u_pad_rst_n_pd_test_tdr_mux( test_mode, pad_rst_n_pd      , dft_pad_rst_n_pd      );
    test_tdr_mux #(4) u_pad_rst_n_ds_test_tdr_mux( test_mode, pad_rst_n_ds      , dft_pad_rst_n_ds      );
    test_tdr_mux #(2) u_pad_rst_n_st_test_tdr_mux( test_mode, pad_rst_n_st      , dft_pad_rst_n_st      );
`ifdef TSMC22
    assign dft_pad_rst_n_c = test_mode ? pad_rst_n_c : 1'b0;
    `STD_CLK_BUF_CELL u_buf_pad_rst_n(
         .Z          (   ),
         .I          (dft_pad_rst_n_c)
     );
`else
    assign dft_pad_rst_n_c = 1'b0;
`endif
    iobuf_s_model u_pad_rst_n_pad (
        .oen(dft_pad_rst_n_oe_n),
        .i  (dft_pad_rst_n_i  ),
        .ie (dft_pad_rst_n_ie ),
        .ds (dft_pad_rst_n_ds ),
        .st (dft_pad_rst_n_st ),
        .pu (dft_pad_rst_n_pu ),
        .pd (dft_pad_rst_n_pd ),
        .c  (pad_rst_n_c  ),
        .pad(PAD_RST_N    )
        );


endmodule