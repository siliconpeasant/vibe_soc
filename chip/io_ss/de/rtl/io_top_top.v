// =================================================================================================
// Copyright(C) 2020 - Cygnusemi Co.,Ltd. All rights reserved.                                    
// =================================================================================================
// Powered by Gang He, Shuwei Xuan, Cuiping Zhou, etc.
// =================================================================================================
// File Name    : io_top_top.v
// Module       : io_top_top
// Function     : io_top_top integration
// Type         : RTL
// -------------------------------------------------------------------------------------------------
// Update History :
// -------------------------------------------------------------------------------------------------
// Rev.Level    Date                  Coded by                Contents
// 1.0          2026-08-02 13:16:09       your_name               Init
//
// =================================================================================================
// End Revision
// =================================================================================================

// =================================================================================================
// RTL Header
// =================================================================================================

module io_top_top(
	input                                apb_clk,
	input                                apb_rst_n,
	input                                apb_sel,
	input                                apb_enable,
	input                                apb_write,
	input  [31:0]                        apb_addr,
	input  [31:0]                        apb_wdata,
	input                                test_mode,
	input                                pad_gpio0_out,
	input                                pad_gpio0_oen,
	input                                pad_gpio1_out,
	input                                pad_gpio1_oen,
	output [31:0]                        apb_rdata,
	output                               apb_pready,
	output                               apb_slverr,
	output                               pad_gpio0_in,
	output                               pad_gpio1_in,
	output                               clk_in,
	output                               clk_div2_in,
	output                               clk_div4_in,
	output                               ext_clk_in,
	output                               rst_n_in,
	output                               soft_rst_in,
	output                               wdt_rst_in,
	output                               por_n_in,
	inout                                PAD_GPIO0,
	inout                                PAD_GPIO1,
	inout                                PAD_CLK,
	inout                                PAD_RST_N
);


// =================================================================================================
// Signals Declaration
// =================================================================================================
	wire [1:0]                                    pad_clk_func_sel;
	wire [1:0]                                    pad_clk_st;
	wire                                          pad_gpio1_oe_n;
	wire                                          pad_gpio1_pd;
	wire                                          pad_rst_n_ie;
	wire                                          pad_clk_pd;
	wire                                          pad_clk_c;
	wire [1:0]                                    pad_rst_n_st;
	wire                                          pad_gpio0_pd;
	wire                                          pad_gpio0_ie;
	wire                                          pad_gpio1_c;
	wire [1:0]                                    pad_gpio1_st;
	wire                                          pad_rst_n_oe_n;
	wire                                          pad_gpio0_oe_n;
	wire                                          pad_gpio0_pu;
	wire                                          pad_rst_n_pd;
	wire                                          pad_gpio0_i;
	wire [3:0]                                    pad_rst_n_ds;
	wire                                          pad_rst_n_pu;
	wire                                          pad_clk_i;
	wire [1:0]                                    pad_gpio0_st;
	wire                                          pad_rst_n_i;
	wire                                          pad_gpio1_i;
	wire                                          pad_rst_n_c;
	wire [3:0]                                    pad_gpio0_ds;
	wire                                          pad_gpio0_c;
	wire [3:0]                                    pad_gpio1_ds;
	wire                                          pad_clk_oe_n;
	wire [1:0]                                    pad_rst_n_func_sel;
	wire                                          pad_clk_ie;
	wire                                          pad_gpio1_pu;
	wire [3:0]                                    pad_clk_ds;
	wire                                          pad_gpio1_ie;
	wire                                          pad_clk_pu;


// =================================================================================================
// Interface Declaration
// =================================================================================================

// =================================================================================================
// Instance
// =================================================================================================

	IO_TOP_apb_reg	u_IO_TOP_apb_reg(
		.clk                                                         (apb_clk                                                     ), //u_IO_TOP_apb_reg.input,
		.rst_n                                                       (apb_rst_n                                                   ), //u_IO_TOP_apb_reg.input,
		.psel                                                        (apb_sel                                                     ), //u_IO_TOP_apb_reg.input,
		.penable                                                     (apb_enable                                                  ), //u_IO_TOP_apb_reg.input,
		.pwrite                                                      (apb_write                                                   ), //u_IO_TOP_apb_reg.input,
		.paddr                                                       (apb_addr[31:0]                                              ), //u_IO_TOP_apb_reg.input,
		.pwdata                                                      (apb_wdata[31:0]                                             ), //u_IO_TOP_apb_reg.input,
		.prdata                                                      (apb_rdata[31:0]                                             ), //u_IO_TOP_apb_reg.output,
		.pready                                                      (apb_pready                                                  ), //u_IO_TOP_apb_reg.output,
		.pslverr                                                     (apb_slverr                                                  ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio0_pad_gpio0_ie                             (pad_gpio0_ie                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio0_pad_gpio0_ds                             (pad_gpio0_ds[3:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio0_pad_gpio0_st                             (pad_gpio0_st[1:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio0_pad_gpio0_pu                             (pad_gpio0_pu                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio0_pad_gpio0_pd                             (pad_gpio0_pd                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio1_pad_gpio1_ie                             (pad_gpio1_ie                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio1_pad_gpio1_ds                             (pad_gpio1_ds[3:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio1_pad_gpio1_st                             (pad_gpio1_st[1:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio1_pad_gpio1_pu                             (pad_gpio1_pu                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_gpio1_pad_gpio1_pd                             (pad_gpio1_pd                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_ie                                 (pad_clk_ie                                                  ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_ds                                 (pad_clk_ds[3:0]                                             ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_func_sel                           (pad_clk_func_sel[1:0]                                       ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_st                                 (pad_clk_st[1:0]                                             ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_pu                                 (pad_clk_pu                                                  ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_clk_pad_clk_pd                                 (pad_clk_pd                                                  ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_ie                             (pad_rst_n_ie                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_ds                             (pad_rst_n_ds[3:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_func_sel                       (pad_rst_n_func_sel[1:0]                                     ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_st                             (pad_rst_n_st[1:0]                                           ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_pu                             (pad_rst_n_pu                                                ), //u_IO_TOP_apb_reg.output,
		.pad_ctrl_pad_rst_n_pad_rst_n_pd                             (pad_rst_n_pd                                                ) //u_IO_TOP_apb_reg.output,
	);

	io_top_pin_mux	u_io_top_pin_mux(
		.test_mode                                                   (test_mode                                                   ), //u_io_top_pin_mux.input,
		.pad_gpio0_c                                                 (pad_gpio0_c                                                 ), //u_io_top_pin_mux.input,
		.pad_gpio0_i                                                 (pad_gpio0_i                                                 ), //u_io_top_pin_mux.output,
		.pad_gpio0_oe_n                                              (pad_gpio0_oe_n                                              ), //u_io_top_pin_mux.output,
		.pad_gpio0_out                                               (pad_gpio0_out                                               ), //u_io_top_pin_mux.input,
		.pad_gpio0_oen                                               (pad_gpio0_oen                                               ), //u_io_top_pin_mux.input,
		.pad_gpio0_in                                                (pad_gpio0_in                                                ), //u_io_top_pin_mux.output,
		.pad_gpio1_c                                                 (pad_gpio1_c                                                 ), //u_io_top_pin_mux.input,
		.pad_gpio1_i                                                 (pad_gpio1_i                                                 ), //u_io_top_pin_mux.output,
		.pad_gpio1_oe_n                                              (pad_gpio1_oe_n                                              ), //u_io_top_pin_mux.output,
		.pad_gpio1_out                                               (pad_gpio1_out                                               ), //u_io_top_pin_mux.input,
		.pad_gpio1_oen                                               (pad_gpio1_oen                                               ), //u_io_top_pin_mux.input,
		.pad_gpio1_in                                                (pad_gpio1_in                                                ), //u_io_top_pin_mux.output,
		.pad_clk_c                                                   (pad_clk_c                                                   ), //u_io_top_pin_mux.input,
		.pad_clk_i                                                   (pad_clk_i                                                   ), //u_io_top_pin_mux.output,
		.pad_clk_oe_n                                                (pad_clk_oe_n                                                ), //u_io_top_pin_mux.output,
		.pad_clk_func_sel                                            (pad_clk_func_sel[1:0]                                       ), //u_io_top_pin_mux.input,
		.clk_in                                                      (clk_in                                                      ), //u_io_top_pin_mux.output,
		.clk_div2_in                                                 (clk_div2_in                                                 ), //u_io_top_pin_mux.output,
		.clk_div4_in                                                 (clk_div4_in                                                 ), //u_io_top_pin_mux.output,
		.ext_clk_in                                                  (ext_clk_in                                                  ), //u_io_top_pin_mux.output,
		.pad_rst_n_c                                                 (pad_rst_n_c                                                 ), //u_io_top_pin_mux.input,
		.pad_rst_n_i                                                 (pad_rst_n_i                                                 ), //u_io_top_pin_mux.output,
		.pad_rst_n_oe_n                                              (pad_rst_n_oe_n                                              ), //u_io_top_pin_mux.output,
		.pad_rst_n_func_sel                                          (pad_rst_n_func_sel[1:0]                                     ), //u_io_top_pin_mux.input,
		.rst_n_in                                                    (rst_n_in                                                    ), //u_io_top_pin_mux.output,
		.soft_rst_in                                                 (soft_rst_in                                                 ), //u_io_top_pin_mux.output,
		.wdt_rst_in                                                  (wdt_rst_in                                                  ), //u_io_top_pin_mux.output,
		.por_n_in                                                    (por_n_in                                                    ) //u_io_top_pin_mux.output,
	);

	io_top_ring	u_io_top_ring(
		.test_mode                                                   (test_mode                                                   ), //u_io_top_ring.input ,
		.PAD_GPIO0                                                   (PAD_GPIO0                                                   ), //u_io_top_ring.inout ,
		.pad_gpio0_oe_n                                              (pad_gpio0_oe_n                                              ), //u_io_top_ring.input ,
		.pad_gpio0_i                                                 (pad_gpio0_i                                                 ), //u_io_top_ring.input ,
		.pad_gpio0_ie                                                (pad_gpio0_ie                                                ), //u_io_top_ring.input ,
		.pad_gpio0_ds                                                (pad_gpio0_ds[3:0]                                           ), //u_io_top_ring.input ,
		.pad_gpio0_st                                                (pad_gpio0_st                                                ), //u_io_top_ring.input ,
		.pad_gpio0_pu                                                (pad_gpio0_pu                                                ), //u_io_top_ring.input ,
		.pad_gpio0_pd                                                (pad_gpio0_pd                                                ), //u_io_top_ring.input ,
		.pad_gpio0_c                                                 (pad_gpio0_c                                                 ), //u_io_top_ring.output,
		.PAD_GPIO1                                                   (PAD_GPIO1                                                   ), //u_io_top_ring.inout ,
		.pad_gpio1_oe_n                                              (pad_gpio1_oe_n                                              ), //u_io_top_ring.input ,
		.pad_gpio1_i                                                 (pad_gpio1_i                                                 ), //u_io_top_ring.input ,
		.pad_gpio1_ie                                                (pad_gpio1_ie                                                ), //u_io_top_ring.input ,
		.pad_gpio1_ds                                                (pad_gpio1_ds[3:0]                                           ), //u_io_top_ring.input ,
		.pad_gpio1_st                                                (pad_gpio1_st                                                ), //u_io_top_ring.input ,
		.pad_gpio1_pu                                                (pad_gpio1_pu                                                ), //u_io_top_ring.input ,
		.pad_gpio1_pd                                                (pad_gpio1_pd                                                ), //u_io_top_ring.input ,
		.pad_gpio1_c                                                 (pad_gpio1_c                                                 ), //u_io_top_ring.output,
		.PAD_CLK                                                     (PAD_CLK                                                     ), //u_io_top_ring.inout ,
		.pad_clk_oe_n                                                (pad_clk_oe_n                                                ), //u_io_top_ring.input ,
		.pad_clk_i                                                   (pad_clk_i                                                   ), //u_io_top_ring.input ,
		.pad_clk_ie                                                  (pad_clk_ie                                                  ), //u_io_top_ring.input ,
		.pad_clk_ds                                                  (pad_clk_ds[3:0]                                             ), //u_io_top_ring.input ,
		.pad_clk_st                                                  (pad_clk_st                                                  ), //u_io_top_ring.input ,
		.pad_clk_pu                                                  (pad_clk_pu                                                  ), //u_io_top_ring.input ,
		.pad_clk_pd                                                  (pad_clk_pd                                                  ), //u_io_top_ring.input ,
		.pad_clk_c                                                   (pad_clk_c                                                   ), //u_io_top_ring.output,
		.PAD_RST_N                                                   (PAD_RST_N                                                   ), //u_io_top_ring.inout ,
		.pad_rst_n_oe_n                                              (pad_rst_n_oe_n                                              ), //u_io_top_ring.input ,
		.pad_rst_n_i                                                 (pad_rst_n_i                                                 ), //u_io_top_ring.input ,
		.pad_rst_n_ie                                                (pad_rst_n_ie                                                ), //u_io_top_ring.input ,
		.pad_rst_n_ds                                                (pad_rst_n_ds[3:0]                                           ), //u_io_top_ring.input ,
		.pad_rst_n_st                                                (pad_rst_n_st                                                ), //u_io_top_ring.input ,
		.pad_rst_n_pu                                                (pad_rst_n_pu                                                ), //u_io_top_ring.input ,
		.pad_rst_n_pd                                                (pad_rst_n_pd                                                ), //u_io_top_ring.input ,
		.pad_rst_n_c                                                 (pad_rst_n_c                                                 ) //u_io_top_ring.output,
	);

endmodule

