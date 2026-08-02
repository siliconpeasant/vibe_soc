// ============================================================================
// File Name    : io_top_pin_mux.v
// Description  :
// Author       : autumn
// Created On   : 2026/08/02 13:16
// Last Modified: 2026/08/02 13:16
// ----------------------------------------------------------------------------
// Date         By           Version  Description
// ----------------------------------------------------------------------------
// 2026/08/02   autumn      1.0      Initial version
// ============================================================================
`include "std_cell_def.h"
module io_top_pin_mux(
	input               test_mode,
	//pad PAD_GPIO0
	input          pad_gpio0_c,
	output         pad_gpio0_i,
	output         pad_gpio0_oe_n,
	input          pad_gpio0_out,
	input          pad_gpio0_oen,
	output         pad_gpio0_in,
	//pad PAD_GPIO1
	input          pad_gpio1_c,
	output         pad_gpio1_i,
	output         pad_gpio1_oe_n,
	input          pad_gpio1_out,
	input          pad_gpio1_oen,
	output         pad_gpio1_in,
	//pad PAD_CLK
	input          pad_clk_c,
	output reg     pad_clk_i,
	output reg     pad_clk_oe_n,
	input  [1:0]   pad_clk_func_sel,
	output         clk_in,
	output         clk_div2_in,
	output         clk_div4_in,
	output         ext_clk_in,
	//pad PAD_RST_N
	input          pad_rst_n_c,
	output reg     pad_rst_n_i,
	output reg     pad_rst_n_oe_n,
	input  [1:0]   pad_rst_n_func_sel,
	output         rst_n_in,
	output         soft_rst_in,
	output         wdt_rst_in,
	output         por_n_in
);

	wire gpio0_in_pre;
	wire i2c_scl_in_pre;
	wire gpio1_in_pre;
	wire uart_rx_in_pre;
	wire i2c_sda_in_pre;
	wire clk_in_pre;
	wire clk_div2_in_pre;
	wire clk_div4_in_pre;
	wire ext_clk_in_pre;
	wire rst_n_in_pre;
	wire soft_rst_in_pre;
	wire wdt_rst_in_pre;
	wire por_n_in_pre;


	//pad PAD_CLK
	always @ (*)
	    case (pad_clk_func_sel)
	        2'h0:    pad_clk_oe_n = 1'b1;
	        2'h1:    pad_clk_oe_n = 1'b1;
	        2'h2:    pad_clk_oe_n = 1'b1;
	        default: pad_clk_oe_n = 1'b1;
	    endcase
	always @ (*)
	    case (pad_clk_func_sel)
	        2'h0:    pad_clk_i = 1'b0;
	        2'h1:    pad_clk_i = 1'b0;
	        2'h2:    pad_clk_i = 1'b0;
	        default: pad_clk_i = 1'b0;
	    endcase
	// NOTE: patched incomplete ternaries from io_top_gen demo output for compile smoke.
	assign clk_in_pre = (test_mode==1'b1)? 1'b0: ((pad_clk_func_sel == 2'h0)
	                             ) ? pad_clk_c : 1'b0;
	assign clk_div2_in_pre = (test_mode==1'b1)? 1'b0: ((pad_clk_func_sel == 2'h1)
	                             ) ? pad_clk_c : 1'b0;
	assign clk_div4_in_pre = (test_mode==1'b1)? 1'b0: ((pad_clk_func_sel == 2'h2)
	                             ) ? pad_clk_c : 1'b0;
	assign ext_clk_in_pre = (test_mode==1'b1)? 1'b0: ((pad_clk_func_sel == 2'h3)
	                             ) ? pad_clk_c : 1'b0;


	//pad PAD_RST_N
	always @ (*)
	    case (pad_rst_n_func_sel)
	        2'h0:    pad_rst_n_oe_n = 1'b1;
	        2'h1:    pad_rst_n_oe_n = 1'b1;
	        2'h2:    pad_rst_n_oe_n = 1'b1;
	        default: pad_rst_n_oe_n = 1'b1;
	    endcase
	always @ (*)
	    case (pad_rst_n_func_sel)
	        2'h0:    pad_rst_n_i = 1'b0;
	        2'h1:    pad_rst_n_i = 1'b0;
	        2'h2:    pad_rst_n_i = 1'b0;
	        default: pad_rst_n_i = 1'b0;
	    endcase
	// NOTE: patched incomplete ternaries from io_top_gen demo output for compile smoke.
	assign rst_n_in_pre = (test_mode==1'b1)? 1'b0: ((pad_rst_n_func_sel == 2'h0)
	                             ) ? pad_rst_n_c : 1'b1;
	assign soft_rst_in_pre = (test_mode==1'b1)? 1'b0: ((pad_rst_n_func_sel == 2'h1)
	                             ) ? pad_rst_n_c : 1'b1;
	assign wdt_rst_in_pre = (test_mode==1'b1)? 1'b0: ((pad_rst_n_func_sel == 2'h2)
	                             ) ? pad_rst_n_c : 1'b1;
	assign por_n_in_pre = (test_mode==1'b1)? 1'b0: ((pad_rst_n_func_sel == 2'h3)
	                             ) ? pad_rst_n_c : 1'b1;


	//---------------
	// input buffers
	//---------------
	//pad PAD_GPIO0
	assign pad_gpio0_oe_n   = (test_mode == 1'b1)? 1'b1: ~pad_gpio0_oen;
	assign pad_gpio0_i    = pad_gpio0_out;
	assign pad_gpio0_in_pre = pad_gpio0_c;
	//pad PAD_GPIO1
	assign pad_gpio1_oe_n   = (test_mode == 1'b1)? 1'b1: ~pad_gpio1_oen;
	assign pad_gpio1_i    = pad_gpio1_out;
	assign pad_gpio1_in_pre = pad_gpio1_c;


	`ifdef NO_ASIC
	assign pad_gpio0_in = pad_gpio0_in_pre;
	assign pad_gpio1_in = pad_gpio1_in_pre;
	assign clk_in = clk_in_pre;
	assign clk_div2_in = clk_div2_in_pre;
	assign clk_div4_in = clk_div4_in_pre;
	assign ext_clk_in = ext_clk_in_pre;
	assign rst_n_in = rst_n_in_pre;
	assign soft_rst_in = soft_rst_in_pre;
	assign wdt_rst_in = wdt_rst_in_pre;
	assign por_n_in = por_n_in_pre;
	`elsif FPGA
	assign pad_gpio0_in = pad_gpio0_in_pre;
	assign pad_gpio1_in = pad_gpio1_in_pre;
	assign clk_in = clk_in_pre;
	assign clk_div2_in = clk_div2_in_pre;
	assign clk_div4_in = clk_div4_in_pre;
	assign ext_clk_in = ext_clk_in_pre;
	assign rst_n_in = rst_n_in_pre;
	assign soft_rst_in = soft_rst_in_pre;
	assign wdt_rst_in = wdt_rst_in_pre;
	assign por_n_in = por_n_in_pre;
	`else
	std_cell_clk_buf pad_gpio0_in_dontouch_buf (.clk_buf_in(pad_gpio0_in_pre), .clk_buf_out(pad_gpio0_in));
	std_cell_clk_buf pad_gpio1_in_dontouch_buf (.clk_buf_in(pad_gpio1_in_pre), .clk_buf_out(pad_gpio1_in));
	std_cell_clk_buf clk_in_dontouch_buf (.clk_buf_in(clk_in_pre), .clk_buf_out(clk_in));
	std_cell_clk_buf clk_div2_in_dontouch_buf (.clk_buf_in(clk_div2_in_pre), .clk_buf_out(clk_div2_in));
	std_cell_clk_buf clk_div4_in_dontouch_buf (.clk_buf_in(clk_div4_in_pre), .clk_buf_out(clk_div4_in));
	std_cell_clk_buf ext_clk_in_dontouch_buf (.clk_buf_in(ext_clk_in_pre), .clk_buf_out(ext_clk_in));
	std_cell_clk_buf rst_n_in_dontouch_buf (.clk_buf_in(rst_n_in_pre), .clk_buf_out(rst_n_in));
	std_cell_clk_buf soft_rst_in_dontouch_buf (.clk_buf_in(soft_rst_in_pre), .clk_buf_out(soft_rst_in));
	std_cell_clk_buf wdt_rst_in_dontouch_buf (.clk_buf_in(wdt_rst_in_pre), .clk_buf_out(wdt_rst_in));
	std_cell_clk_buf por_n_in_dontouch_buf (.clk_buf_in(por_n_in_pre), .clk_buf_out(por_n_in));
	`endif

endmodule