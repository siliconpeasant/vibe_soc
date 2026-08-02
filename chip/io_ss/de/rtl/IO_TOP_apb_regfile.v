// +FHDR----------------------------------------------------------------------------
// Copyright (c) 2026 Silicon Peasant.
// ALL RIGHTS RESERVED Worldwide
//         
// Author        : autumn
// Email         : autumn@foxmail.com
// Created On    : 2026/08/02 13:16
// Last Modified : 2026/08/02 13:16
// File Name     : IO_TOP_apb_regfile.v
// Description   :
// 
// ---------------------------------------------------------------------------------
// Modification History:
// Date         By              Version                 Change Description
// ---------------------------------------------------------------------------------
// 2026/08/02   autumn     1.0                     Original
// -FHDR----------------------------------------------------------------------------
module IO_TOP_apb_regfile(
    input           apb_clk,
    input           apb_rst_n,
    input           apb_sel,
    input           apb_enable,
    input           apb_write,
    input   [31:0]  apb_addr, 
    input   [31:0]  apb_wdata,
    output          apb_ready,
    output          apb_slverr,
    output reg [31:0]  apb_rdata,
	output reg			pad_gpio0_ie,
	output reg	[3:0]		pad_gpio0_ds,
	output reg	[1:0]		pad_gpio0_st,
	output reg			pad_gpio0_pu,
	output reg			pad_gpio0_pd,
	output reg			pad_gpio1_ie,
	output reg	[3:0]		pad_gpio1_ds,
	output reg	[1:0]		pad_gpio1_st,
	output reg			pad_gpio1_pu,
	output reg			pad_gpio1_pd,
	output reg			pad_clk_ie,
	output reg	[3:0]		pad_clk_ds,
	output reg	[1:0]		pad_clk_func_sel,
	output reg	[1:0]		pad_clk_st,
	output reg			pad_clk_pu,
	output reg			pad_clk_pd,
	output reg			pad_rst_n_ie,
	output reg	[3:0]		pad_rst_n_ds,
	output reg	[1:0]		pad_rst_n_func_sel,
	output reg	[1:0]		pad_rst_n_st,
	output reg			pad_rst_n_pu,
	output reg			pad_rst_n_pd
);

wire	pad_gpio0_ie_wr;
wire	pad_gpio0_ds_wr;
wire	pad_gpio0_st_wr;
wire	pad_gpio0_pu_wr;
wire	pad_gpio0_pd_wr;
wire	pad_ctrl_pad_gpio0_rd;
wire	[31:0]	pad_ctrl_pad_gpio0_rdata;
wire	pad_gpio1_ie_wr;
wire	pad_gpio1_ds_wr;
wire	pad_gpio1_st_wr;
wire	pad_gpio1_pu_wr;
wire	pad_gpio1_pd_wr;
wire	pad_ctrl_pad_gpio1_rd;
wire	[31:0]	pad_ctrl_pad_gpio1_rdata;
wire	pad_clk_ie_wr;
wire	pad_clk_ds_wr;
wire	pad_clk_func_sel_wr;
wire	pad_clk_st_wr;
wire	pad_clk_pu_wr;
wire	pad_clk_pd_wr;
wire	pad_ctrl_pad_clk_rd;
wire	[31:0]	pad_ctrl_pad_clk_rdata;
wire	pad_rst_n_ie_wr;
wire	pad_rst_n_ds_wr;
wire	pad_rst_n_func_sel_wr;
wire	pad_rst_n_st_wr;
wire	pad_rst_n_pu_wr;
wire	pad_rst_n_pd_wr;
wire	pad_ctrl_pad_rst_n_rd;
wire	[31:0]	pad_ctrl_pad_rst_n_rdata;
wire	wr_en;
wire	rd_en;
reg 	[31:0]	apb_rdata_pre;

assign	apb_ready = 1'b1;
assign	apb_slverr = 1'b0;

assign	wr_en = apb_write & !apb_enable & apb_sel;
assign	rd_en = !apb_write & !apb_enable & apb_sel;

assign	pad_gpio0_ie_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	pad_gpio0_ds_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	pad_gpio0_st_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	pad_gpio0_pu_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	pad_gpio0_pd_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	pad_ctrl_pad_gpio0_rd = (apb_addr[31:0] == 32'h0) & rd_en;
assign	pad_gpio1_ie_wr = (apb_addr[31:0] == 32'h4) & wr_en;
assign	pad_gpio1_ds_wr = (apb_addr[31:0] == 32'h4) & wr_en;
assign	pad_gpio1_st_wr = (apb_addr[31:0] == 32'h4) & wr_en;
assign	pad_gpio1_pu_wr = (apb_addr[31:0] == 32'h4) & wr_en;
assign	pad_gpio1_pd_wr = (apb_addr[31:0] == 32'h4) & wr_en;
assign	pad_ctrl_pad_gpio1_rd = (apb_addr[31:0] == 32'h4) & rd_en;
assign	pad_clk_ie_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_clk_ds_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_clk_func_sel_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_clk_st_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_clk_pu_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_clk_pd_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	pad_ctrl_pad_clk_rd = (apb_addr[31:0] == 32'h8) & rd_en;
assign	pad_rst_n_ie_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_rst_n_ds_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_rst_n_func_sel_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_rst_n_st_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_rst_n_pu_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_rst_n_pd_wr = (apb_addr[31:0] == 32'hc) & wr_en;
assign	pad_ctrl_pad_rst_n_rd = (apb_addr[31:0] == 32'hc) & rd_en;

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio0_ie <= 1'h1;
	else if (pad_gpio0_ie_wr == 1'b1)
		pad_gpio0_ie <= apb_wdata[2:2];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio0_ds <= 4'h4;
	else if (pad_gpio0_ds_wr == 1'b1)
		pad_gpio0_ds <= apb_wdata[7:4];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio0_st <= 2'h0;
	else if (pad_gpio0_st_wr == 1'b1)
		pad_gpio0_st <= apb_wdata[13:12];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio0_pu <= 1'h1;
	else if (pad_gpio0_pu_wr == 1'b1)
		pad_gpio0_pu <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio0_pd <= 1'h1;
	else if (pad_gpio0_pd_wr == 1'b1)
		pad_gpio0_pd <= apb_wdata[1:1];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio1_ie <= 1'h1;
	else if (pad_gpio1_ie_wr == 1'b1)
		pad_gpio1_ie <= apb_wdata[2:2];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio1_ds <= 4'h4;
	else if (pad_gpio1_ds_wr == 1'b1)
		pad_gpio1_ds <= apb_wdata[7:4];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio1_st <= 2'h0;
	else if (pad_gpio1_st_wr == 1'b1)
		pad_gpio1_st <= apb_wdata[13:12];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio1_pu <= 1'h1;
	else if (pad_gpio1_pu_wr == 1'b1)
		pad_gpio1_pu <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_gpio1_pd <= 1'h1;
	else if (pad_gpio1_pd_wr == 1'b1)
		pad_gpio1_pd <= apb_wdata[1:1];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_ie <= 1'h1;
	else if (pad_clk_ie_wr == 1'b1)
		pad_clk_ie <= apb_wdata[2:2];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_ds <= 4'h4;
	else if (pad_clk_ds_wr == 1'b1)
		pad_clk_ds <= apb_wdata[7:4];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_func_sel <= 2'h0;
	else if (pad_clk_func_sel_wr == 1'b1)
		pad_clk_func_sel <= apb_wdata[9:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_st <= 2'h0;
	else if (pad_clk_st_wr == 1'b1)
		pad_clk_st <= apb_wdata[13:12];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_pu <= 1'h0;
	else if (pad_clk_pu_wr == 1'b1)
		pad_clk_pu <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_clk_pd <= 1'h0;
	else if (pad_clk_pd_wr == 1'b1)
		pad_clk_pd <= apb_wdata[1:1];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_ie <= 1'h1;
	else if (pad_rst_n_ie_wr == 1'b1)
		pad_rst_n_ie <= apb_wdata[2:2];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_ds <= 4'h4;
	else if (pad_rst_n_ds_wr == 1'b1)
		pad_rst_n_ds <= apb_wdata[7:4];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_func_sel <= 2'h0;
	else if (pad_rst_n_func_sel_wr == 1'b1)
		pad_rst_n_func_sel <= apb_wdata[9:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_st <= 2'h0;
	else if (pad_rst_n_st_wr == 1'b1)
		pad_rst_n_st <= apb_wdata[13:12];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_pu <= 1'h1;
	else if (pad_rst_n_pu_wr == 1'b1)
		pad_rst_n_pu <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		pad_rst_n_pd <= 1'h1;
	else if (pad_rst_n_pd_wr == 1'b1)
		pad_rst_n_pd <= apb_wdata[1:1];
end

assign	pad_ctrl_pad_gpio0_rdata[2:2] = pad_gpio0_ie;
assign	pad_ctrl_pad_gpio0_rdata[7:4] = pad_gpio0_ds;
assign	pad_ctrl_pad_gpio0_rdata[13:12] = pad_gpio0_st;
assign	pad_ctrl_pad_gpio0_rdata[0:0] = pad_gpio0_pu;
assign	pad_ctrl_pad_gpio0_rdata[1:1] = pad_gpio0_pd;
assign	pad_ctrl_pad_gpio0_rdata[3] = 1'b0;
assign	pad_ctrl_pad_gpio0_rdata[11:8] = 4'b0;
assign	pad_ctrl_pad_gpio0_rdata[31:14] = 18'b0;
assign	pad_ctrl_pad_gpio1_rdata[2:2] = pad_gpio1_ie;
assign	pad_ctrl_pad_gpio1_rdata[7:4] = pad_gpio1_ds;
assign	pad_ctrl_pad_gpio1_rdata[13:12] = pad_gpio1_st;
assign	pad_ctrl_pad_gpio1_rdata[0:0] = pad_gpio1_pu;
assign	pad_ctrl_pad_gpio1_rdata[1:1] = pad_gpio1_pd;
assign	pad_ctrl_pad_gpio1_rdata[3] = 1'b0;
assign	pad_ctrl_pad_gpio1_rdata[11:8] = 4'b0;
assign	pad_ctrl_pad_gpio1_rdata[31:14] = 18'b0;
assign	pad_ctrl_pad_clk_rdata[2:2] = pad_clk_ie;
assign	pad_ctrl_pad_clk_rdata[7:4] = pad_clk_ds;
assign	pad_ctrl_pad_clk_rdata[9:8] = pad_clk_func_sel;
assign	pad_ctrl_pad_clk_rdata[13:12] = pad_clk_st;
assign	pad_ctrl_pad_clk_rdata[0:0] = pad_clk_pu;
assign	pad_ctrl_pad_clk_rdata[1:1] = pad_clk_pd;
assign	pad_ctrl_pad_clk_rdata[3] = 1'b0;
assign	pad_ctrl_pad_clk_rdata[11:10] = 2'b0;
assign	pad_ctrl_pad_clk_rdata[31:14] = 18'b0;
assign	pad_ctrl_pad_rst_n_rdata[2:2] = pad_rst_n_ie;
assign	pad_ctrl_pad_rst_n_rdata[7:4] = pad_rst_n_ds;
assign	pad_ctrl_pad_rst_n_rdata[9:8] = pad_rst_n_func_sel;
assign	pad_ctrl_pad_rst_n_rdata[13:12] = pad_rst_n_st;
assign	pad_ctrl_pad_rst_n_rdata[0:0] = pad_rst_n_pu;
assign	pad_ctrl_pad_rst_n_rdata[1:1] = pad_rst_n_pd;
assign	pad_ctrl_pad_rst_n_rdata[3] = 1'b0;
assign	pad_ctrl_pad_rst_n_rdata[11:10] = 2'b0;
assign	pad_ctrl_pad_rst_n_rdata[31:14] = 18'b0;

assign apb_rdata_pre[31:0] = 
	pad_ctrl_pad_gpio0_rd ? pad_ctrl_pad_gpio0_rdata[31:0] :
	pad_ctrl_pad_gpio1_rd ? pad_ctrl_pad_gpio1_rdata[31:0] :
	pad_ctrl_pad_clk_rd ? pad_ctrl_pad_clk_rdata[31:0] :
	pad_ctrl_pad_rst_n_rd ? pad_ctrl_pad_rst_n_rdata[31:0] :
	32'hdeadbeef;

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		apb_rdata[31:0] <= 32'h0;
	else
		apb_rdata[31:0] <= apb_rdata_pre[31:0];
end

endmodule
