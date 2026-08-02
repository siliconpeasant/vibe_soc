// +FHDR----------------------------------------------------------------------------
// Copyright (c) 2026 Silicon Peasant.
// ALL RIGHTS RESERVED Worldwide
//         
// Author        : autumn
// Email         : autumn@foxmail.com
// Created On    : 2026/08/02 13:16
// Last Modified : 2026/08/02 13:16
// File Name     : DEMO_CRG_apb_regfile.v
// Description   :
// 
// ---------------------------------------------------------------------------------
// Modification History:
// Date         By              Version                 Change Description
// ---------------------------------------------------------------------------------
// 2026/08/02   autumn     1.0                     Original
// -FHDR----------------------------------------------------------------------------
module DEMO_CRG_apb_regfile(
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
	output reg			rt32k_muxed0_clk_sel,
	input 				rt32k_muxed0_clk_sel_clk0_sel,
	input 				rt32k_muxed0_clk_sel_clk1_sel,
	input 				rt32k_muxed0_clk_sel_done,
	output reg			demo_main_muxed_clk_sel,
	input 				demo_main_muxed_clk_sel_clk0_sel,
	input 				demo_main_muxed_clk_sel_clk1_sel,
	input 				demo_main_muxed_clk_sel_done,
	output reg			demo_lp_core_clk_ea,
	input 				demo_lp_core_clk_ea_status,
	output reg			demo_lp_mtime_clk_ea,
	input 				demo_lp_mtime_clk_ea_status,
	output reg			demo_uart_apb_clk_ea,
	input 				demo_uart_apb_clk_ea_status,
	output reg			demo_uart_core_clk_ea,
	input 				demo_uart_core_clk_ea_status,
	output reg			demo_usim0_32k_clk_ea,
	input 				demo_usim0_32k_clk_ea_status,
	output reg			demo_usim0_apb_clk_ea,
	input 				demo_usim0_apb_clk_ea_status,
	output reg			demo_gpio_apb_clk_ea,
	output reg			demo_gpio_apb_clk_sel,
	input 				demo_gpio_apb_clk_ea_status,
	input 				demo_gpio_apb_clk_sel_clk0_sel,
	input 				demo_gpio_apb_clk_sel_clk1_sel,
	input 				demo_gpio_apb_clk_sel_done,
	output reg			demo_i2c_core_clk_ea,
	input 				demo_i2c_core_clk_ea_status,
	output reg			demo_i2c_apb_clk_ea,
	input 				demo_i2c_apb_clk_ea_status,
	output reg			demo_usim1_32k_clk_ea,
	input 				demo_usim1_32k_clk_ea_status,
	output reg			demo_usim1_apb_clk_ea,
	input 				demo_usim1_apb_clk_ea_status,
	output reg			demo_spi_core_clk_ea,
	input 				demo_spi_core_clk_ea_status,
	output reg			demo_spi_apb_clk_ea,
	input 				demo_spi_apb_clk_ea_status,
	output reg			demo_pmu_32k_clk_ea,
	input 				demo_pmu_32k_clk_ea_status,
	output reg			demo_pmu_clk_ea,
	input 				demo_pmu_clk_ea_status,
	output reg			demo_pmu_apb_clk_ea,
	input 				demo_pmu_apb_clk_ea_status,
	output reg			demo_drx_timer_32k_clk_ea,
	input 				demo_drx_timer_32k_clk_ea_status,
	output reg			demo_drx_timer_apb_clk_ea,
	input 				demo_drx_timer_apb_clk_ea_status,
	output reg			demo_rtc_apb_clk_ea,
	input 				demo_rtc_apb_clk_ea_status,
	output reg			demo_rtc_core_clk_ea,
	input 				demo_rtc_core_clk_ea_status,
	output reg			demo_wdt_apb_clk_ea,
	input 				demo_wdt_apb_clk_ea_status,
	output reg			demo_wdt_clk_ea,
	input 				demo_wdt_clk_ea_status,
	output reg			demo_timer_apb_clk_ea,
	output reg			demo_timer_apb_clk_sel,
	input 				demo_timer_apb_clk_ea_status,
	input 				demo_timer_apb_clk_sel_clk0_sel,
	input 				demo_timer_apb_clk_sel_clk1_sel,
	input 				demo_timer_apb_clk_sel_done,
	output reg			demo_timer_cnt_clk_ea,
	input 				demo_timer_cnt_clk_ea_status,
	output reg			demo_sc_apb_clk_ea,
	input 				demo_sc_apb_clk_ea_status,
	output reg			demo_rom_ahb_clk_ea,
	input 				demo_rom_ahb_clk_ea_status,
	output reg			demo_rdc_ahb_clk_ea,
	input 				demo_rdc_ahb_clk_ea_status,
	output reg			demo_rdc_clk_ea,
	input 				demo_rdc_clk_ea_status,
	output reg			demo_cipher_sec_core_clk_ea,
	input 				demo_cipher_sec_core_clk_ea_status,
	output reg			demo_cipher_sec_aes_clk_ea,
	input 				demo_cipher_sec_aes_clk_ea_status,
	output reg			demo_cipher_sec_hash_clk_ea,
	input 				demo_cipher_sec_hash_clk_ea_status,
	output reg			demo_cipher_sec_sm4_clk_ea,
	input 				demo_cipher_sec_sm4_clk_ea_status,
	output reg			demo_cipher_sec_pk_clk_ea,
	input 				demo_cipher_sec_pk_clk_ea_status,
	output reg			demo_cipher_sec_pkdiv2_clk_ea,
	output reg			demo_cipher_sec_pkdiv2_clk_divider_ea_req,
	output reg	[2:0]		demo_cipher_sec_pkdiv2_clk_divider,
	input 				demo_cipher_sec_pkdiv2_clk_ea_status,
	input 				demo_cipher_sec_pkdiv2_clk_divider_done,
	input 	[2:0]		demo_cipher_sec_pkdiv2_clk_divider_status,
	output reg			demo_efuse_ctrl_ahb_clk_ea,
	input 				demo_efuse_ctrl_ahb_clk_ea_status,
	output reg			demo_sec_ctrl0_clk_ea,
	input 				demo_sec_ctrl0_clk_ea_status,
	output reg			demo_sec_ctrl1_clk_ea,
	input 				demo_sec_ctrl1_clk_ea_status,
	output reg			demo_sec_ctrl2_clk_ea,
	input 				demo_sec_ctrl2_clk_ea_status,
	output reg			demo_io_apb_clk_ea,
	input 				demo_io_apb_clk_ea_status,
	output reg			misc_ahb_clk_ea,
	input 				misc_ahb_clk_ea_status,
	output reg			dtss_dt_clk_ea,
	input 				dtss_dt_clk_ea_status,
	output reg			demo_ocmem_ahb_clk_ea,
	input 				demo_ocmem_ahb_clk_ea_status,
	output reg			demo_timer64_ahb_clk_ea,
	input 				demo_timer64_ahb_clk_ea_status,
	output reg			demo_timer64_clk_ea,
	input 				demo_timer64_clk_ea_status,
	output reg			demo_pwm_apb_clk_ea,
	input 				demo_pwm_apb_clk_ea_status,
	output reg			demo_pwm_core_clk_ea,
	output reg			demo_pwm_core_clk_sel,
	input 				demo_pwm_core_clk_ea_status,
	input 				demo_pwm_core_clk_sel_clk0_sel,
	input 				demo_pwm_core_clk_sel_clk1_sel,
	input 				demo_pwm_core_clk_sel_done,
	output reg			demo_sc_ref_clk_ea,
	input 				demo_sc_ref_clk_ea_status,
	output reg			demo_lp_core_rst_n_sftrstn,
	output reg			demo_lp_core_demo_por_rst_n_sftrstn,
	output reg			demo_uart_apb_rst_n_sftrstn,
	output reg			demo_usim0_32k_rst_n_sftrstn,
	output reg			demo_gpio_apb_rst_n_sftrstn,
	output reg			demo_i2c_core_rst_n_sftrstn,
	output reg			demo_usim1_32k_rst_n_sftrstn,
	output reg			demo_spi_core_rst_n_sftrstn,
	output reg			demo_drx_timer_32k_rst_n_sftrstn,
	output reg			demo_rtc_apb_rst_n_sftrstn,
	output reg			demo_wdt_apb_rst_n_sftrstn,
	output reg			demo_timer_apb_rst_n_sftrstn,
	output reg			demo_sc_apb_rst_n_sftrstn,
	output reg			demo_rom_ahb_rst_n_sftrstn,
	output reg			demo_rdc_ahb_rst_n_sftrstn,
	output reg			demo_rdc_rst_n_sftrstn,
	output reg			demo_cipher_sec_core_rst_n_sftrstn,
	output reg			demo_efuse_ctrl_logic_rst_n_sftrstn,
	output reg			demo_sec_ctrl0_rst_n_sftrstn,
	output reg			demo_io_apb_rst_n_sftrstn,
	output reg			misc_ahb_rst_n_sftrstn,
	output reg			dtss_dt_rst_n_sftrstn,
	output reg			demo_ocmem_ahb_rst_n_sftrstn,
	output reg			demo_timer64_ahb_rst_n_sftrstn,
	output reg			demo_pwm_apb_rst_n_sftrstn,
	output reg			demo_timer_cnt_rst_n_sftrstn,
	output reg			demo_top_lp_bus_rst_n_sftrstn,
	input 				demo_lp_core_rst_n_status,
	input 				demo_lp_core_demo_por_rst_n_status,
	input 				demo_uart_apb_rst_n_status,
	input 				demo_usim0_32k_rst_n_status,
	input 				demo_gpio_apb_rst_n_status,
	input 				demo_i2c_core_rst_n_status,
	input 				demo_usim1_32k_rst_n_status,
	input 				demo_spi_core_rst_n_status,
	input 				demo_drx_timer_32k_rst_n_status,
	input 				demo_rtc_apb_rst_n_status,
	input 				demo_wdt_apb_rst_n_status,
	input 				demo_timer_apb_rst_n_status,
	input 				demo_sc_apb_rst_n_status,
	input 				demo_rom_ahb_rst_n_status,
	input 				demo_rdc_ahb_rst_n_status,
	input 				demo_rdc_rst_n_status,
	input 				demo_cipher_sec_core_rst_n_status,
	input 				demo_efuse_ctrl_logic_rst_n_status,
	input 				demo_sec_ctrl0_rst_n_status,
	input 				demo_io_apb_rst_n_status,
	input 				misc_ahb_rst_n_status,
	input 				dtss_dt_rst_n_status,
	input 				demo_ocmem_ahb_rst_n_status,
	input 				demo_timer64_ahb_rst_n_status,
	input 				demo_pwm_apb_rst_n_status,
	input 				demo_timer_cnt_rst_n_status,
	input 				demo_top_lp_bus_rst_n_status,
	output reg			demo_rst,
	output reg			soc_soft_rst_n,
	output reg			mdm_rst_n,
	output reg			full_chip_sw_rst,
	output reg			soft_demo_hw_rst_n,
	output reg			demo_top_soft_rst_n,
	input 				soc_async_rst_n_status,
	input 				demo_lp_core_demo_por_rst_n_status,
	input 				demo_lp_bus_rst_n_status,
	input 				demo_efuse_ctrl_demo_por_rst_n_status,
	input 				demo_pmu_rst_n_status,
	input 				demo_pmu_apb_rst_n_status,
	input 				demo_pmu_32k_rst_n_status,
	input 				demo_pmu_demo_por_rst_n_status,
	input 				demo_crg_apb_rst_n_status,
	input 				demo_sc_demo_por_rst_n_status,
	input 				soc_soft_rst_n_out_status,
	input 				mdm_sys_rst_n_status,
	output reg			demo_lp_cpu_rst_ijtag_ctrl
);

wire	rt32k_muxed0_clk_sel_wr;
wire	rt32k_muxed0_clk_ctrl_rd;
wire	[31:0]	rt32k_muxed0_clk_ctrl_rdata;
wire	rt32k_muxed0_clk_status_rd;
wire	[31:0]	rt32k_muxed0_clk_status_rdata;
wire	demo_main_muxed_clk_sel_wr;
wire	demo_main_muxed_clk_ctrl_rd;
wire	[31:0]	demo_main_muxed_clk_ctrl_rdata;
wire	demo_main_muxed_clk_status_rd;
wire	[31:0]	demo_main_muxed_clk_status_rdata;
wire	demo_lp_core_clk_ea_wr;
wire	demo_lp_core_clk_ctrl_rd;
wire	[31:0]	demo_lp_core_clk_ctrl_rdata;
wire	demo_lp_core_clk_status_rd;
wire	[31:0]	demo_lp_core_clk_status_rdata;
wire	demo_lp_mtime_clk_ea_wr;
wire	demo_lp_mtime_clk_ctrl_rd;
wire	[31:0]	demo_lp_mtime_clk_ctrl_rdata;
wire	demo_lp_mtime_clk_status_rd;
wire	[31:0]	demo_lp_mtime_clk_status_rdata;
wire	demo_uart_apb_clk_ea_wr;
wire	demo_uart_apb_clk_ctrl_rd;
wire	[31:0]	demo_uart_apb_clk_ctrl_rdata;
wire	demo_uart_apb_clk_status_rd;
wire	[31:0]	demo_uart_apb_clk_status_rdata;
wire	demo_uart_core_clk_ea_wr;
wire	demo_uart_core_clk_ctrl_rd;
wire	[31:0]	demo_uart_core_clk_ctrl_rdata;
wire	demo_uart_core_clk_status_rd;
wire	[31:0]	demo_uart_core_clk_status_rdata;
wire	demo_usim0_32k_clk_ea_wr;
wire	demo_usim0_32k_clk_ctrl_rd;
wire	[31:0]	demo_usim0_32k_clk_ctrl_rdata;
wire	demo_usim0_32k_clk_status_rd;
wire	[31:0]	demo_usim0_32k_clk_status_rdata;
wire	demo_usim0_apb_clk_ea_wr;
wire	demo_usim0_apb_clk_ctrl_rd;
wire	[31:0]	demo_usim0_apb_clk_ctrl_rdata;
wire	demo_usim0_apb_clk_status_rd;
wire	[31:0]	demo_usim0_apb_clk_status_rdata;
wire	demo_gpio_apb_clk_ea_wr;
wire	demo_gpio_apb_clk_sel_wr;
wire	demo_gpio_apb_clk_ctrl_rd;
wire	[31:0]	demo_gpio_apb_clk_ctrl_rdata;
wire	demo_gpio_apb_clk_status_rd;
wire	[31:0]	demo_gpio_apb_clk_status_rdata;
wire	demo_i2c_core_clk_ea_wr;
wire	demo_i2c_core_clk_ctrl_rd;
wire	[31:0]	demo_i2c_core_clk_ctrl_rdata;
wire	demo_i2c_core_clk_status_rd;
wire	[31:0]	demo_i2c_core_clk_status_rdata;
wire	demo_i2c_apb_clk_ea_wr;
wire	demo_i2c_apb_clk_ctrl_rd;
wire	[31:0]	demo_i2c_apb_clk_ctrl_rdata;
wire	demo_i2c_apb_clk_status_rd;
wire	[31:0]	demo_i2c_apb_clk_status_rdata;
wire	demo_usim1_32k_clk_ea_wr;
wire	demo_usim1_32k_clk_ctrl_rd;
wire	[31:0]	demo_usim1_32k_clk_ctrl_rdata;
wire	demo_usim1_32k_clk_status_rd;
wire	[31:0]	demo_usim1_32k_clk_status_rdata;
wire	demo_usim1_apb_clk_ea_wr;
wire	demo_usim1_apb_clk_ctrl_rd;
wire	[31:0]	demo_usim1_apb_clk_ctrl_rdata;
wire	demo_usim1_apb_clk_status_rd;
wire	[31:0]	demo_usim1_apb_clk_status_rdata;
wire	demo_spi_core_clk_ea_wr;
wire	demo_spi_core_clk_ctrl_rd;
wire	[31:0]	demo_spi_core_clk_ctrl_rdata;
wire	demo_spi_core_clk_status_rd;
wire	[31:0]	demo_spi_core_clk_status_rdata;
wire	demo_spi_apb_clk_ea_wr;
wire	demo_spi_apb_clk_ctrl_rd;
wire	[31:0]	demo_spi_apb_clk_ctrl_rdata;
wire	demo_spi_apb_clk_status_rd;
wire	[31:0]	demo_spi_apb_clk_status_rdata;
wire	demo_pmu_32k_clk_ea_wr;
wire	demo_pmu_32k_clk_ctrl_rd;
wire	[31:0]	demo_pmu_32k_clk_ctrl_rdata;
wire	demo_pmu_32k_clk_status_rd;
wire	[31:0]	demo_pmu_32k_clk_status_rdata;
wire	demo_pmu_clk_ea_wr;
wire	demo_pmu_clk_ctrl_rd;
wire	[31:0]	demo_pmu_clk_ctrl_rdata;
wire	demo_pmu_clk_status_rd;
wire	[31:0]	demo_pmu_clk_status_rdata;
wire	demo_pmu_apb_clk_ea_wr;
wire	demo_pmu_apb_clk_ctrl_rd;
wire	[31:0]	demo_pmu_apb_clk_ctrl_rdata;
wire	demo_pmu_apb_clk_status_rd;
wire	[31:0]	demo_pmu_apb_clk_status_rdata;
wire	demo_drx_timer_32k_clk_ea_wr;
wire	demo_drx_timer_32k_clk_ctrl_rd;
wire	[31:0]	demo_drx_timer_32k_clk_ctrl_rdata;
wire	demo_drx_timer_32k_clk_status_rd;
wire	[31:0]	demo_drx_timer_32k_clk_status_rdata;
wire	demo_drx_timer_apb_clk_ea_wr;
wire	demo_drx_timer_apb_clk_ctrl_rd;
wire	[31:0]	demo_drx_timer_apb_clk_ctrl_rdata;
wire	demo_drx_timer_apb_clk_status_rd;
wire	[31:0]	demo_drx_timer_apb_clk_status_rdata;
wire	demo_rtc_apb_clk_ea_wr;
wire	demo_rtc_apb_clk_ctrl_rd;
wire	[31:0]	demo_rtc_apb_clk_ctrl_rdata;
wire	demo_rtc_apb_clk_status_rd;
wire	[31:0]	demo_rtc_apb_clk_status_rdata;
wire	demo_rtc_core_clk_ea_wr;
wire	demo_rtc_core_clk_ctrl_rd;
wire	[31:0]	demo_rtc_core_clk_ctrl_rdata;
wire	demo_rtc_core_clk_status_rd;
wire	[31:0]	demo_rtc_core_clk_status_rdata;
wire	demo_wdt_apb_clk_ea_wr;
wire	demo_wdt_apb_clk_ctrl_rd;
wire	[31:0]	demo_wdt_apb_clk_ctrl_rdata;
wire	demo_wdt_apb_clk_status_rd;
wire	[31:0]	demo_wdt_apb_clk_status_rdata;
wire	demo_wdt_clk_ea_wr;
wire	demo_wdt_clk_ctrl_rd;
wire	[31:0]	demo_wdt_clk_ctrl_rdata;
wire	demo_wdt_clk_status_rd;
wire	[31:0]	demo_wdt_clk_status_rdata;
wire	demo_timer_apb_clk_ea_wr;
wire	demo_timer_apb_clk_sel_wr;
wire	demo_timer_apb_clk_ctrl_rd;
wire	[31:0]	demo_timer_apb_clk_ctrl_rdata;
wire	demo_timer_apb_clk_status_rd;
wire	[31:0]	demo_timer_apb_clk_status_rdata;
wire	demo_timer_cnt_clk_ea_wr;
wire	demo_timer_cnt_clk_ctrl_rd;
wire	[31:0]	demo_timer_cnt_clk_ctrl_rdata;
wire	demo_timer_cnt_clk_status_rd;
wire	[31:0]	demo_timer_cnt_clk_status_rdata;
wire	demo_sc_apb_clk_ea_wr;
wire	demo_sc_apb_clk_ctrl_rd;
wire	[31:0]	demo_sc_apb_clk_ctrl_rdata;
wire	demo_sc_apb_clk_status_rd;
wire	[31:0]	demo_sc_apb_clk_status_rdata;
wire	demo_rom_ahb_clk_ea_wr;
wire	demo_rom_ahb_clk_ctrl_rd;
wire	[31:0]	demo_rom_ahb_clk_ctrl_rdata;
wire	demo_rom_ahb_clk_status_rd;
wire	[31:0]	demo_rom_ahb_clk_status_rdata;
wire	demo_rdc_ahb_clk_ea_wr;
wire	demo_rdc_ahb_clk_ctrl_rd;
wire	[31:0]	demo_rdc_ahb_clk_ctrl_rdata;
wire	demo_rdc_ahb_clk_status_rd;
wire	[31:0]	demo_rdc_ahb_clk_status_rdata;
wire	demo_rdc_clk_ea_wr;
wire	demo_rdc_clk_ctrl_rd;
wire	[31:0]	demo_rdc_clk_ctrl_rdata;
wire	demo_rdc_clk_status_rd;
wire	[31:0]	demo_rdc_clk_status_rdata;
wire	demo_cipher_sec_core_clk_ea_wr;
wire	demo_cipher_sec_core_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_core_clk_ctrl_rdata;
wire	demo_cipher_sec_core_clk_status_rd;
wire	[31:0]	demo_cipher_sec_core_clk_status_rdata;
wire	demo_cipher_sec_aes_clk_ea_wr;
wire	demo_cipher_sec_aes_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_aes_clk_ctrl_rdata;
wire	demo_cipher_sec_aes_clk_status_rd;
wire	[31:0]	demo_cipher_sec_aes_clk_status_rdata;
wire	demo_cipher_sec_hash_clk_ea_wr;
wire	demo_cipher_sec_hash_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_hash_clk_ctrl_rdata;
wire	demo_cipher_sec_hash_clk_status_rd;
wire	[31:0]	demo_cipher_sec_hash_clk_status_rdata;
wire	demo_cipher_sec_sm4_clk_ea_wr;
wire	demo_cipher_sec_sm4_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_sm4_clk_ctrl_rdata;
wire	demo_cipher_sec_sm4_clk_status_rd;
wire	[31:0]	demo_cipher_sec_sm4_clk_status_rdata;
wire	demo_cipher_sec_pk_clk_ea_wr;
wire	demo_cipher_sec_pk_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_pk_clk_ctrl_rdata;
wire	demo_cipher_sec_pk_clk_status_rd;
wire	[31:0]	demo_cipher_sec_pk_clk_status_rdata;
wire	demo_cipher_sec_pkdiv2_clk_ea_wr;
wire	demo_cipher_sec_pkdiv2_clk_divider_ea_req_wr;
wire	demo_cipher_sec_pkdiv2_clk_ctrl_rd;
wire	[31:0]	demo_cipher_sec_pkdiv2_clk_ctrl_rdata;
wire	demo_cipher_sec_pkdiv2_clk_divider_wr;
wire	demo_cipher_sec_pkdiv2_clk_divider_rd;
wire	[31:0]	demo_cipher_sec_pkdiv2_clk_divider_rdata;
wire	demo_cipher_sec_pkdiv2_clk_status_rd;
wire	[31:0]	demo_cipher_sec_pkdiv2_clk_status_rdata;
wire	demo_efuse_ctrl_ahb_clk_ea_wr;
wire	demo_efuse_ctrl_ahb_clk_ctrl_rd;
wire	[31:0]	demo_efuse_ctrl_ahb_clk_ctrl_rdata;
wire	demo_efuse_ctrl_ahb_clk_status_rd;
wire	[31:0]	demo_efuse_ctrl_ahb_clk_status_rdata;
wire	demo_sec_ctrl0_clk_ea_wr;
wire	demo_sec_ctrl0_clk_ctrl_rd;
wire	[31:0]	demo_sec_ctrl0_clk_ctrl_rdata;
wire	demo_sec_ctrl0_clk_status_rd;
wire	[31:0]	demo_sec_ctrl0_clk_status_rdata;
wire	demo_sec_ctrl1_clk_ea_wr;
wire	demo_sec_ctrl1_clk_ctrl_rd;
wire	[31:0]	demo_sec_ctrl1_clk_ctrl_rdata;
wire	demo_sec_ctrl1_clk_status_rd;
wire	[31:0]	demo_sec_ctrl1_clk_status_rdata;
wire	demo_sec_ctrl2_clk_ea_wr;
wire	demo_sec_ctrl2_clk_ctrl_rd;
wire	[31:0]	demo_sec_ctrl2_clk_ctrl_rdata;
wire	demo_sec_ctrl2_clk_status_rd;
wire	[31:0]	demo_sec_ctrl2_clk_status_rdata;
wire	demo_io_apb_clk_ea_wr;
wire	demo_io_apb_clk_ctrl_rd;
wire	[31:0]	demo_io_apb_clk_ctrl_rdata;
wire	demo_io_apb_clk_status_rd;
wire	[31:0]	demo_io_apb_clk_status_rdata;
wire	misc_ahb_clk_ea_wr;
wire	misc_ahb_clk_ctrl_rd;
wire	[31:0]	misc_ahb_clk_ctrl_rdata;
wire	misc_ahb_clk_status_rd;
wire	[31:0]	misc_ahb_clk_status_rdata;
wire	dtss_dt_clk_ea_wr;
wire	dtss_dt_clk_ctrl_rd;
wire	[31:0]	dtss_dt_clk_ctrl_rdata;
wire	dtss_dt_clk_status_rd;
wire	[31:0]	dtss_dt_clk_status_rdata;
wire	demo_ocmem_ahb_clk_ea_wr;
wire	demo_ocmem_ahb_clk_ctrl_rd;
wire	[31:0]	demo_ocmem_ahb_clk_ctrl_rdata;
wire	demo_ocmem_ahb_clk_status_rd;
wire	[31:0]	demo_ocmem_ahb_clk_status_rdata;
wire	demo_timer64_ahb_clk_ea_wr;
wire	demo_timer64_ahb_clk_ctrl_rd;
wire	[31:0]	demo_timer64_ahb_clk_ctrl_rdata;
wire	demo_timer64_ahb_clk_status_rd;
wire	[31:0]	demo_timer64_ahb_clk_status_rdata;
wire	demo_timer64_clk_ea_wr;
wire	demo_timer64_clk_ctrl_rd;
wire	[31:0]	demo_timer64_clk_ctrl_rdata;
wire	demo_timer64_clk_status_rd;
wire	[31:0]	demo_timer64_clk_status_rdata;
wire	demo_pwm_apb_clk_ea_wr;
wire	demo_pwm_apb_clk_ctrl_rd;
wire	[31:0]	demo_pwm_apb_clk_ctrl_rdata;
wire	demo_pwm_apb_clk_status_rd;
wire	[31:0]	demo_pwm_apb_clk_status_rdata;
wire	demo_pwm_core_clk_ea_wr;
wire	demo_pwm_core_clk_sel_wr;
wire	demo_pwm_core_clk_ctrl_rd;
wire	[31:0]	demo_pwm_core_clk_ctrl_rdata;
wire	demo_pwm_core_clk_status_rd;
wire	[31:0]	demo_pwm_core_clk_status_rdata;
wire	demo_sc_ref_clk_ea_wr;
wire	demo_sc_ref_clk_ctrl_rd;
wire	[31:0]	demo_sc_ref_clk_ctrl_rdata;
wire	demo_sc_ref_clk_status_rd;
wire	[31:0]	demo_sc_ref_clk_status_rdata;
wire	demo_lp_core_rst_n_sftrstn_wr;
wire	demo_lp_core_demo_por_rst_n_sftrstn_wr;
wire	demo_lp_core_rst_ctrl_rd;
wire	[31:0]	demo_lp_core_rst_ctrl_rdata;
wire	demo_uart_apb_rst_n_sftrstn_wr;
wire	demo_uart_rst_ctrl_rd;
wire	[31:0]	demo_uart_rst_ctrl_rdata;
wire	demo_usim0_32k_rst_n_sftrstn_wr;
wire	demo_usim0_rst_ctrl_rd;
wire	[31:0]	demo_usim0_rst_ctrl_rdata;
wire	demo_gpio_apb_rst_n_sftrstn_wr;
wire	demo_gpio_rst_ctrl_rd;
wire	[31:0]	demo_gpio_rst_ctrl_rdata;
wire	demo_i2c_core_rst_n_sftrstn_wr;
wire	demo_i2c0_rst_ctrl_rd;
wire	[31:0]	demo_i2c0_rst_ctrl_rdata;
wire	demo_usim1_32k_rst_n_sftrstn_wr;
wire	demo_usim1_rst_ctrl_rd;
wire	[31:0]	demo_usim1_rst_ctrl_rdata;
wire	demo_spi_core_rst_n_sftrstn_wr;
wire	demo_spi_rst_ctrl_rd;
wire	[31:0]	demo_spi_rst_ctrl_rdata;
wire	demo_drx_timer_32k_rst_n_sftrstn_wr;
wire	demo_drx_timer_rst_ctrl_rd;
wire	[31:0]	demo_drx_timer_rst_ctrl_rdata;
wire	demo_rtc_apb_rst_n_sftrstn_wr;
wire	demo_rtc_rst_ctrl_rd;
wire	[31:0]	demo_rtc_rst_ctrl_rdata;
wire	demo_wdt_apb_rst_n_sftrstn_wr;
wire	demo_wdt_rst_ctrl_rd;
wire	[31:0]	demo_wdt_rst_ctrl_rdata;
wire	demo_timer_apb_rst_n_sftrstn_wr;
wire	demo_timer0_rst_ctrl_rd;
wire	[31:0]	demo_timer0_rst_ctrl_rdata;
wire	demo_sc_apb_rst_n_sftrstn_wr;
wire	demo_sc_rst_ctrl_rd;
wire	[31:0]	demo_sc_rst_ctrl_rdata;
wire	demo_rom_ahb_rst_n_sftrstn_wr;
wire	demo_rom_ahb_rst_ctrl_rd;
wire	[31:0]	demo_rom_ahb_rst_ctrl_rdata;
wire	demo_rdc_ahb_rst_n_sftrstn_wr;
wire	demo_rdc_ahb_rst_ctrl_rd;
wire	[31:0]	demo_rdc_ahb_rst_ctrl_rdata;
wire	demo_rdc_rst_n_sftrstn_wr;
wire	demo_rdc_rst_ctrl_rd;
wire	[31:0]	demo_rdc_rst_ctrl_rdata;
wire	demo_cipher_sec_core_rst_n_sftrstn_wr;
wire	demo_cipher_sec_core_rst_ctrl_rd;
wire	[31:0]	demo_cipher_sec_core_rst_ctrl_rdata;
wire	demo_efuse_ctrl_logic_rst_n_sftrstn_wr;
wire	demo_efuse_ctrl_rst_ctrl_rd;
wire	[31:0]	demo_efuse_ctrl_rst_ctrl_rdata;
wire	demo_sec_ctrl0_rst_n_sftrstn_wr;
wire	demo_sec_ctrl0_rst_ctrl_rd;
wire	[31:0]	demo_sec_ctrl0_rst_ctrl_rdata;
wire	demo_io_apb_rst_n_sftrstn_wr;
wire	demo_io_rst_ctrl_rd;
wire	[31:0]	demo_io_rst_ctrl_rdata;
wire	misc_ahb_rst_n_sftrstn_wr;
wire	misc_ahb_rst_ctrl_rd;
wire	[31:0]	misc_ahb_rst_ctrl_rdata;
wire	dtss_dt_rst_n_sftrstn_wr;
wire	dtss_dt_rst_ctrl_rd;
wire	[31:0]	dtss_dt_rst_ctrl_rdata;
wire	demo_ocmem_ahb_rst_n_sftrstn_wr;
wire	demo_ocmem_ahb_rst_ctrl_rd;
wire	[31:0]	demo_ocmem_ahb_rst_ctrl_rdata;
wire	demo_timer64_ahb_rst_n_sftrstn_wr;
wire	demo_timer64_rst_ctrl_rd;
wire	[31:0]	demo_timer64_rst_ctrl_rdata;
wire	demo_pwm_apb_rst_n_sftrstn_wr;
wire	demo_pwm_rst_ctrl_rd;
wire	[31:0]	demo_pwm_rst_ctrl_rdata;
wire	demo_timer_cnt_rst_n_sftrstn_wr;
wire	demo_timer_cnt_rst_ctrl_rd;
wire	[31:0]	demo_timer_cnt_rst_ctrl_rdata;
wire	demo_top_lp_bus_rst_n_sftrstn_wr;
wire	demo_lp_bus_rst_ctrl_rd;
wire	[31:0]	demo_lp_bus_rst_ctrl_rdata;
wire	demo_lp_core_rst_ctrl_status_rd;
wire	[31:0]	demo_lp_core_rst_ctrl_status_rdata;
wire	demo_uart_rst_ctrl_status_rd;
wire	[31:0]	demo_uart_rst_ctrl_status_rdata;
wire	demo_usim0_rst_ctrl_status_rd;
wire	[31:0]	demo_usim0_rst_ctrl_status_rdata;
wire	demo_gpio_rst_ctrl_status_rd;
wire	[31:0]	demo_gpio_rst_ctrl_status_rdata;
wire	demo_i2c0_rst_ctrl_status_rd;
wire	[31:0]	demo_i2c0_rst_ctrl_status_rdata;
wire	demo_usim1_rst_ctrl_status_rd;
wire	[31:0]	demo_usim1_rst_ctrl_status_rdata;
wire	demo_spi_rst_ctrl_status_rd;
wire	[31:0]	demo_spi_rst_ctrl_status_rdata;
wire	demo_drx_timer_rst_ctrl_status_rd;
wire	[31:0]	demo_drx_timer_rst_ctrl_status_rdata;
wire	demo_rtc_rst_ctrl_status_rd;
wire	[31:0]	demo_rtc_rst_ctrl_status_rdata;
wire	demo_wdt_rst_ctrl_status_rd;
wire	[31:0]	demo_wdt_rst_ctrl_status_rdata;
wire	demo_timer0_rst_ctrl_status_rd;
wire	[31:0]	demo_timer0_rst_ctrl_status_rdata;
wire	demo_sc_rst_ctrl_status_rd;
wire	[31:0]	demo_sc_rst_ctrl_status_rdata;
wire	demo_rom_ahb_rst_ctrl_status_rd;
wire	[31:0]	demo_rom_ahb_rst_ctrl_status_rdata;
wire	demo_rdc_ahb_rst_ctrl_status_rd;
wire	[31:0]	demo_rdc_ahb_rst_ctrl_status_rdata;
wire	demo_rdc_rst_ctrl_status_rd;
wire	[31:0]	demo_rdc_rst_ctrl_status_rdata;
wire	demo_cipher_sec_core_rst_ctrl_status_rd;
wire	[31:0]	demo_cipher_sec_core_rst_ctrl_status_rdata;
wire	demo_efuse_ctrl_rst_ctrl_status_rd;
wire	[31:0]	demo_efuse_ctrl_rst_ctrl_status_rdata;
wire	demo_sec_ctrl0_rst_ctrl_status_rd;
wire	[31:0]	demo_sec_ctrl0_rst_ctrl_status_rdata;
wire	demo_io_rst_ctrl_status_rd;
wire	[31:0]	demo_io_rst_ctrl_status_rdata;
wire	misc_ahb_rst_ctrl_status_rd;
wire	[31:0]	misc_ahb_rst_ctrl_status_rdata;
wire	dtss_dt_rst_ctrl_status_rd;
wire	[31:0]	dtss_dt_rst_ctrl_status_rdata;
wire	demo_ocmem_ahb_rst_ctrl_status_rd;
wire	[31:0]	demo_ocmem_ahb_rst_ctrl_status_rdata;
wire	demo_timer64_rst_ctrl_status_rd;
wire	[31:0]	demo_timer64_rst_ctrl_status_rdata;
wire	demo_pwm_rst_ctrl_status_rd;
wire	[31:0]	demo_pwm_rst_ctrl_status_rdata;
wire	demo_timer_cnt_rst_ctrl_status_rd;
wire	[31:0]	demo_timer_cnt_rst_ctrl_status_rdata;
wire	demo_lp_bus_rst_ctrl_status_rd;
wire	[31:0]	demo_lp_bus_rst_ctrl_status_rdata;
wire	demo_rst_wr;
wire	soc_soft_rst_n_wr;
wire	soft_sw_soc_rst_n_rd;
wire	[31:0]	soft_sw_soc_rst_n_rdata;
wire	mdm_rst_n_wr;
wire	mdm_rst_ctrl_rd;
wire	[31:0]	mdm_rst_ctrl_rdata;
wire	full_chip_sw_rst_wr;
wire	soft_demo_hw_rst_n_wr;
wire	soft_hw_rst_ctrl_rd;
wire	[31:0]	soft_hw_rst_ctrl_rdata;
wire	demo_top_soft_rst_n_wr;
wire	demo_top_soc_rst_ctrl_rd;
wire	[31:0]	demo_top_soc_rst_ctrl_rdata;
wire	demo_crg_rst_n_status_rd;
wire	[31:0]	demo_crg_rst_n_status_rdata;
wire	demo_lp_cpu_rst_ijtag_ctrl_wr;
wire	demo_lp_cpu_rst_ijtag_ctrl_rd;
wire	[31:0]	demo_lp_cpu_rst_ijtag_ctrl_rdata;
wire	wr_en;
wire	rd_en;
reg 	[31:0]	apb_rdata_pre;

assign	apb_ready = 1'b1;
assign	apb_slverr = 1'b0;

assign	wr_en = apb_write & !apb_enable & apb_sel;
assign	rd_en = !apb_write & !apb_enable & apb_sel;

assign	rt32k_muxed0_clk_sel_wr = (apb_addr[31:0] == 32'h0) & wr_en;
assign	rt32k_muxed0_clk_ctrl_rd = (apb_addr[31:0] == 32'h0) & rd_en;
assign	rt32k_muxed0_clk_status_rd = (apb_addr[31:0] == 32'h4) & rd_en;
assign	demo_main_muxed_clk_sel_wr = (apb_addr[31:0] == 32'h8) & wr_en;
assign	demo_main_muxed_clk_ctrl_rd = (apb_addr[31:0] == 32'h8) & rd_en;
assign	demo_main_muxed_clk_status_rd = (apb_addr[31:0] == 32'hc) & rd_en;
assign	demo_lp_core_clk_ea_wr = (apb_addr[31:0] == 32'h10) & wr_en;
assign	demo_lp_core_clk_ctrl_rd = (apb_addr[31:0] == 32'h10) & rd_en;
assign	demo_lp_core_clk_status_rd = (apb_addr[31:0] == 32'h14) & rd_en;
assign	demo_lp_mtime_clk_ea_wr = (apb_addr[31:0] == 32'h18) & wr_en;
assign	demo_lp_mtime_clk_ctrl_rd = (apb_addr[31:0] == 32'h18) & rd_en;
assign	demo_lp_mtime_clk_status_rd = (apb_addr[31:0] == 32'h1c) & rd_en;
assign	demo_uart_apb_clk_ea_wr = (apb_addr[31:0] == 32'h20) & wr_en;
assign	demo_uart_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h20) & rd_en;
assign	demo_uart_apb_clk_status_rd = (apb_addr[31:0] == 32'h24) & rd_en;
assign	demo_uart_core_clk_ea_wr = (apb_addr[31:0] == 32'h28) & wr_en;
assign	demo_uart_core_clk_ctrl_rd = (apb_addr[31:0] == 32'h28) & rd_en;
assign	demo_uart_core_clk_status_rd = (apb_addr[31:0] == 32'h2c) & rd_en;
assign	demo_usim0_32k_clk_ea_wr = (apb_addr[31:0] == 32'h30) & wr_en;
assign	demo_usim0_32k_clk_ctrl_rd = (apb_addr[31:0] == 32'h30) & rd_en;
assign	demo_usim0_32k_clk_status_rd = (apb_addr[31:0] == 32'h34) & rd_en;
assign	demo_usim0_apb_clk_ea_wr = (apb_addr[31:0] == 32'h38) & wr_en;
assign	demo_usim0_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h38) & rd_en;
assign	demo_usim0_apb_clk_status_rd = (apb_addr[31:0] == 32'h3c) & rd_en;
assign	demo_gpio_apb_clk_ea_wr = (apb_addr[31:0] == 32'h40) & wr_en;
assign	demo_gpio_apb_clk_sel_wr = (apb_addr[31:0] == 32'h40) & wr_en;
assign	demo_gpio_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h40) & rd_en;
assign	demo_gpio_apb_clk_status_rd = (apb_addr[31:0] == 32'h44) & rd_en;
assign	demo_i2c_core_clk_ea_wr = (apb_addr[31:0] == 32'h48) & wr_en;
assign	demo_i2c_core_clk_ctrl_rd = (apb_addr[31:0] == 32'h48) & rd_en;
assign	demo_i2c_core_clk_status_rd = (apb_addr[31:0] == 32'h4c) & rd_en;
assign	demo_i2c_apb_clk_ea_wr = (apb_addr[31:0] == 32'h50) & wr_en;
assign	demo_i2c_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h50) & rd_en;
assign	demo_i2c_apb_clk_status_rd = (apb_addr[31:0] == 32'h54) & rd_en;
assign	demo_usim1_32k_clk_ea_wr = (apb_addr[31:0] == 32'h58) & wr_en;
assign	demo_usim1_32k_clk_ctrl_rd = (apb_addr[31:0] == 32'h58) & rd_en;
assign	demo_usim1_32k_clk_status_rd = (apb_addr[31:0] == 32'h5c) & rd_en;
assign	demo_usim1_apb_clk_ea_wr = (apb_addr[31:0] == 32'h60) & wr_en;
assign	demo_usim1_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h60) & rd_en;
assign	demo_usim1_apb_clk_status_rd = (apb_addr[31:0] == 32'h64) & rd_en;
assign	demo_spi_core_clk_ea_wr = (apb_addr[31:0] == 32'h68) & wr_en;
assign	demo_spi_core_clk_ctrl_rd = (apb_addr[31:0] == 32'h68) & rd_en;
assign	demo_spi_core_clk_status_rd = (apb_addr[31:0] == 32'h6c) & rd_en;
assign	demo_spi_apb_clk_ea_wr = (apb_addr[31:0] == 32'h70) & wr_en;
assign	demo_spi_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h70) & rd_en;
assign	demo_spi_apb_clk_status_rd = (apb_addr[31:0] == 32'h74) & rd_en;
assign	demo_pmu_32k_clk_ea_wr = (apb_addr[31:0] == 32'h78) & wr_en;
assign	demo_pmu_32k_clk_ctrl_rd = (apb_addr[31:0] == 32'h78) & rd_en;
assign	demo_pmu_32k_clk_status_rd = (apb_addr[31:0] == 32'h7c) & rd_en;
assign	demo_pmu_clk_ea_wr = (apb_addr[31:0] == 32'h80) & wr_en;
assign	demo_pmu_clk_ctrl_rd = (apb_addr[31:0] == 32'h80) & rd_en;
assign	demo_pmu_clk_status_rd = (apb_addr[31:0] == 32'h84) & rd_en;
assign	demo_pmu_apb_clk_ea_wr = (apb_addr[31:0] == 32'h88) & wr_en;
assign	demo_pmu_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h88) & rd_en;
assign	demo_pmu_apb_clk_status_rd = (apb_addr[31:0] == 32'h8c) & rd_en;
assign	demo_drx_timer_32k_clk_ea_wr = (apb_addr[31:0] == 32'h90) & wr_en;
assign	demo_drx_timer_32k_clk_ctrl_rd = (apb_addr[31:0] == 32'h90) & rd_en;
assign	demo_drx_timer_32k_clk_status_rd = (apb_addr[31:0] == 32'h94) & rd_en;
assign	demo_drx_timer_apb_clk_ea_wr = (apb_addr[31:0] == 32'h98) & wr_en;
assign	demo_drx_timer_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h98) & rd_en;
assign	demo_drx_timer_apb_clk_status_rd = (apb_addr[31:0] == 32'h9c) & rd_en;
assign	demo_rtc_apb_clk_ea_wr = (apb_addr[31:0] == 32'ha0) & wr_en;
assign	demo_rtc_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'ha0) & rd_en;
assign	demo_rtc_apb_clk_status_rd = (apb_addr[31:0] == 32'ha4) & rd_en;
assign	demo_rtc_core_clk_ea_wr = (apb_addr[31:0] == 32'ha8) & wr_en;
assign	demo_rtc_core_clk_ctrl_rd = (apb_addr[31:0] == 32'ha8) & rd_en;
assign	demo_rtc_core_clk_status_rd = (apb_addr[31:0] == 32'hac) & rd_en;
assign	demo_wdt_apb_clk_ea_wr = (apb_addr[31:0] == 32'hb0) & wr_en;
assign	demo_wdt_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'hb0) & rd_en;
assign	demo_wdt_apb_clk_status_rd = (apb_addr[31:0] == 32'hb4) & rd_en;
assign	demo_wdt_clk_ea_wr = (apb_addr[31:0] == 32'hb8) & wr_en;
assign	demo_wdt_clk_ctrl_rd = (apb_addr[31:0] == 32'hb8) & rd_en;
assign	demo_wdt_clk_status_rd = (apb_addr[31:0] == 32'hbc) & rd_en;
assign	demo_timer_apb_clk_ea_wr = (apb_addr[31:0] == 32'hc0) & wr_en;
assign	demo_timer_apb_clk_sel_wr = (apb_addr[31:0] == 32'hc0) & wr_en;
assign	demo_timer_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'hc0) & rd_en;
assign	demo_timer_apb_clk_status_rd = (apb_addr[31:0] == 32'hc4) & rd_en;
assign	demo_timer_cnt_clk_ea_wr = (apb_addr[31:0] == 32'hc8) & wr_en;
assign	demo_timer_cnt_clk_ctrl_rd = (apb_addr[31:0] == 32'hc8) & rd_en;
assign	demo_timer_cnt_clk_status_rd = (apb_addr[31:0] == 32'hcc) & rd_en;
assign	demo_sc_apb_clk_ea_wr = (apb_addr[31:0] == 32'hd0) & wr_en;
assign	demo_sc_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'hd0) & rd_en;
assign	demo_sc_apb_clk_status_rd = (apb_addr[31:0] == 32'hd4) & rd_en;
assign	demo_rom_ahb_clk_ea_wr = (apb_addr[31:0] == 32'hd8) & wr_en;
assign	demo_rom_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'hd8) & rd_en;
assign	demo_rom_ahb_clk_status_rd = (apb_addr[31:0] == 32'hdc) & rd_en;
assign	demo_rdc_ahb_clk_ea_wr = (apb_addr[31:0] == 32'he0) & wr_en;
assign	demo_rdc_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'he0) & rd_en;
assign	demo_rdc_ahb_clk_status_rd = (apb_addr[31:0] == 32'he4) & rd_en;
assign	demo_rdc_clk_ea_wr = (apb_addr[31:0] == 32'he8) & wr_en;
assign	demo_rdc_clk_ctrl_rd = (apb_addr[31:0] == 32'he8) & rd_en;
assign	demo_rdc_clk_status_rd = (apb_addr[31:0] == 32'hec) & rd_en;
assign	demo_cipher_sec_core_clk_ea_wr = (apb_addr[31:0] == 32'hf0) & wr_en;
assign	demo_cipher_sec_core_clk_ctrl_rd = (apb_addr[31:0] == 32'hf0) & rd_en;
assign	demo_cipher_sec_core_clk_status_rd = (apb_addr[31:0] == 32'hf4) & rd_en;
assign	demo_cipher_sec_aes_clk_ea_wr = (apb_addr[31:0] == 32'hf8) & wr_en;
assign	demo_cipher_sec_aes_clk_ctrl_rd = (apb_addr[31:0] == 32'hf8) & rd_en;
assign	demo_cipher_sec_aes_clk_status_rd = (apb_addr[31:0] == 32'hfc) & rd_en;
assign	demo_cipher_sec_hash_clk_ea_wr = (apb_addr[31:0] == 32'h100) & wr_en;
assign	demo_cipher_sec_hash_clk_ctrl_rd = (apb_addr[31:0] == 32'h100) & rd_en;
assign	demo_cipher_sec_hash_clk_status_rd = (apb_addr[31:0] == 32'h104) & rd_en;
assign	demo_cipher_sec_sm4_clk_ea_wr = (apb_addr[31:0] == 32'h108) & wr_en;
assign	demo_cipher_sec_sm4_clk_ctrl_rd = (apb_addr[31:0] == 32'h108) & rd_en;
assign	demo_cipher_sec_sm4_clk_status_rd = (apb_addr[31:0] == 32'h10c) & rd_en;
assign	demo_cipher_sec_pk_clk_ea_wr = (apb_addr[31:0] == 32'h110) & wr_en;
assign	demo_cipher_sec_pk_clk_ctrl_rd = (apb_addr[31:0] == 32'h110) & rd_en;
assign	demo_cipher_sec_pk_clk_status_rd = (apb_addr[31:0] == 32'h114) & rd_en;
assign	demo_cipher_sec_pkdiv2_clk_ea_wr = (apb_addr[31:0] == 32'h118) & wr_en;
assign	demo_cipher_sec_pkdiv2_clk_divider_ea_req_wr = (apb_addr[31:0] == 32'h118) & wr_en;
assign	demo_cipher_sec_pkdiv2_clk_ctrl_rd = (apb_addr[31:0] == 32'h118) & rd_en;
assign	demo_cipher_sec_pkdiv2_clk_divider_wr = (apb_addr[31:0] == 32'h11c) & wr_en;
assign	demo_cipher_sec_pkdiv2_clk_divider_rd = (apb_addr[31:0] == 32'h11c) & rd_en;
assign	demo_cipher_sec_pkdiv2_clk_status_rd = (apb_addr[31:0] == 32'h120) & rd_en;
assign	demo_efuse_ctrl_ahb_clk_ea_wr = (apb_addr[31:0] == 32'h124) & wr_en;
assign	demo_efuse_ctrl_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'h124) & rd_en;
assign	demo_efuse_ctrl_ahb_clk_status_rd = (apb_addr[31:0] == 32'h128) & rd_en;
assign	demo_sec_ctrl0_clk_ea_wr = (apb_addr[31:0] == 32'h12c) & wr_en;
assign	demo_sec_ctrl0_clk_ctrl_rd = (apb_addr[31:0] == 32'h12c) & rd_en;
assign	demo_sec_ctrl0_clk_status_rd = (apb_addr[31:0] == 32'h130) & rd_en;
assign	demo_sec_ctrl1_clk_ea_wr = (apb_addr[31:0] == 32'h134) & wr_en;
assign	demo_sec_ctrl1_clk_ctrl_rd = (apb_addr[31:0] == 32'h134) & rd_en;
assign	demo_sec_ctrl1_clk_status_rd = (apb_addr[31:0] == 32'h138) & rd_en;
assign	demo_sec_ctrl2_clk_ea_wr = (apb_addr[31:0] == 32'h13c) & wr_en;
assign	demo_sec_ctrl2_clk_ctrl_rd = (apb_addr[31:0] == 32'h13c) & rd_en;
assign	demo_sec_ctrl2_clk_status_rd = (apb_addr[31:0] == 32'h140) & rd_en;
assign	demo_io_apb_clk_ea_wr = (apb_addr[31:0] == 32'h144) & wr_en;
assign	demo_io_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h144) & rd_en;
assign	demo_io_apb_clk_status_rd = (apb_addr[31:0] == 32'h148) & rd_en;
assign	misc_ahb_clk_ea_wr = (apb_addr[31:0] == 32'h14c) & wr_en;
assign	misc_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'h14c) & rd_en;
assign	misc_ahb_clk_status_rd = (apb_addr[31:0] == 32'h150) & rd_en;
assign	dtss_dt_clk_ea_wr = (apb_addr[31:0] == 32'h154) & wr_en;
assign	dtss_dt_clk_ctrl_rd = (apb_addr[31:0] == 32'h154) & rd_en;
assign	dtss_dt_clk_status_rd = (apb_addr[31:0] == 32'h158) & rd_en;
assign	demo_ocmem_ahb_clk_ea_wr = (apb_addr[31:0] == 32'h15c) & wr_en;
assign	demo_ocmem_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'h15c) & rd_en;
assign	demo_ocmem_ahb_clk_status_rd = (apb_addr[31:0] == 32'h160) & rd_en;
assign	demo_timer64_ahb_clk_ea_wr = (apb_addr[31:0] == 32'h164) & wr_en;
assign	demo_timer64_ahb_clk_ctrl_rd = (apb_addr[31:0] == 32'h164) & rd_en;
assign	demo_timer64_ahb_clk_status_rd = (apb_addr[31:0] == 32'h168) & rd_en;
assign	demo_timer64_clk_ea_wr = (apb_addr[31:0] == 32'h16c) & wr_en;
assign	demo_timer64_clk_ctrl_rd = (apb_addr[31:0] == 32'h16c) & rd_en;
assign	demo_timer64_clk_status_rd = (apb_addr[31:0] == 32'h170) & rd_en;
assign	demo_pwm_apb_clk_ea_wr = (apb_addr[31:0] == 32'h174) & wr_en;
assign	demo_pwm_apb_clk_ctrl_rd = (apb_addr[31:0] == 32'h174) & rd_en;
assign	demo_pwm_apb_clk_status_rd = (apb_addr[31:0] == 32'h178) & rd_en;
assign	demo_pwm_core_clk_ea_wr = (apb_addr[31:0] == 32'h17c) & wr_en;
assign	demo_pwm_core_clk_sel_wr = (apb_addr[31:0] == 32'h17c) & wr_en;
assign	demo_pwm_core_clk_ctrl_rd = (apb_addr[31:0] == 32'h17c) & rd_en;
assign	demo_pwm_core_clk_status_rd = (apb_addr[31:0] == 32'h180) & rd_en;
assign	demo_sc_ref_clk_ea_wr = (apb_addr[31:0] == 32'h184) & wr_en;
assign	demo_sc_ref_clk_ctrl_rd = (apb_addr[31:0] == 32'h184) & rd_en;
assign	demo_sc_ref_clk_status_rd = (apb_addr[31:0] == 32'h188) & rd_en;
assign	demo_lp_core_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h800) & wr_en;
assign	demo_lp_core_demo_por_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h800) & wr_en;
assign	demo_lp_core_rst_ctrl_rd = (apb_addr[31:0] == 32'h800) & rd_en;
assign	demo_uart_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h804) & wr_en;
assign	demo_uart_rst_ctrl_rd = (apb_addr[31:0] == 32'h804) & rd_en;
assign	demo_usim0_32k_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h808) & wr_en;
assign	demo_usim0_rst_ctrl_rd = (apb_addr[31:0] == 32'h808) & rd_en;
assign	demo_gpio_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h80c) & wr_en;
assign	demo_gpio_rst_ctrl_rd = (apb_addr[31:0] == 32'h80c) & rd_en;
assign	demo_i2c_core_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h810) & wr_en;
assign	demo_i2c0_rst_ctrl_rd = (apb_addr[31:0] == 32'h810) & rd_en;
assign	demo_usim1_32k_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h814) & wr_en;
assign	demo_usim1_rst_ctrl_rd = (apb_addr[31:0] == 32'h814) & rd_en;
assign	demo_spi_core_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h818) & wr_en;
assign	demo_spi_rst_ctrl_rd = (apb_addr[31:0] == 32'h818) & rd_en;
assign	demo_drx_timer_32k_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h81c) & wr_en;
assign	demo_drx_timer_rst_ctrl_rd = (apb_addr[31:0] == 32'h81c) & rd_en;
assign	demo_rtc_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h820) & wr_en;
assign	demo_rtc_rst_ctrl_rd = (apb_addr[31:0] == 32'h820) & rd_en;
assign	demo_wdt_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h824) & wr_en;
assign	demo_wdt_rst_ctrl_rd = (apb_addr[31:0] == 32'h824) & rd_en;
assign	demo_timer_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h828) & wr_en;
assign	demo_timer0_rst_ctrl_rd = (apb_addr[31:0] == 32'h828) & rd_en;
assign	demo_sc_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h82c) & wr_en;
assign	demo_sc_rst_ctrl_rd = (apb_addr[31:0] == 32'h82c) & rd_en;
assign	demo_rom_ahb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h830) & wr_en;
assign	demo_rom_ahb_rst_ctrl_rd = (apb_addr[31:0] == 32'h830) & rd_en;
assign	demo_rdc_ahb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h834) & wr_en;
assign	demo_rdc_ahb_rst_ctrl_rd = (apb_addr[31:0] == 32'h834) & rd_en;
assign	demo_rdc_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h838) & wr_en;
assign	demo_rdc_rst_ctrl_rd = (apb_addr[31:0] == 32'h838) & rd_en;
assign	demo_cipher_sec_core_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h83c) & wr_en;
assign	demo_cipher_sec_core_rst_ctrl_rd = (apb_addr[31:0] == 32'h83c) & rd_en;
assign	demo_efuse_ctrl_logic_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h840) & wr_en;
assign	demo_efuse_ctrl_rst_ctrl_rd = (apb_addr[31:0] == 32'h840) & rd_en;
assign	demo_sec_ctrl0_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h844) & wr_en;
assign	demo_sec_ctrl0_rst_ctrl_rd = (apb_addr[31:0] == 32'h844) & rd_en;
assign	demo_io_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h848) & wr_en;
assign	demo_io_rst_ctrl_rd = (apb_addr[31:0] == 32'h848) & rd_en;
assign	misc_ahb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h84c) & wr_en;
assign	misc_ahb_rst_ctrl_rd = (apb_addr[31:0] == 32'h84c) & rd_en;
assign	dtss_dt_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h850) & wr_en;
assign	dtss_dt_rst_ctrl_rd = (apb_addr[31:0] == 32'h850) & rd_en;
assign	demo_ocmem_ahb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h854) & wr_en;
assign	demo_ocmem_ahb_rst_ctrl_rd = (apb_addr[31:0] == 32'h854) & rd_en;
assign	demo_timer64_ahb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h858) & wr_en;
assign	demo_timer64_rst_ctrl_rd = (apb_addr[31:0] == 32'h858) & rd_en;
assign	demo_pwm_apb_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h85c) & wr_en;
assign	demo_pwm_rst_ctrl_rd = (apb_addr[31:0] == 32'h85c) & rd_en;
assign	demo_timer_cnt_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h860) & wr_en;
assign	demo_timer_cnt_rst_ctrl_rd = (apb_addr[31:0] == 32'h860) & rd_en;
assign	demo_top_lp_bus_rst_n_sftrstn_wr = (apb_addr[31:0] == 32'h864) & wr_en;
assign	demo_lp_bus_rst_ctrl_rd = (apb_addr[31:0] == 32'h864) & rd_en;
assign	demo_lp_core_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1000) & rd_en;
assign	demo_uart_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1004) & rd_en;
assign	demo_usim0_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1008) & rd_en;
assign	demo_gpio_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h100c) & rd_en;
assign	demo_i2c0_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1010) & rd_en;
assign	demo_usim1_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1014) & rd_en;
assign	demo_spi_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1018) & rd_en;
assign	demo_drx_timer_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h101c) & rd_en;
assign	demo_rtc_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1020) & rd_en;
assign	demo_wdt_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1024) & rd_en;
assign	demo_timer0_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1028) & rd_en;
assign	demo_sc_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h102c) & rd_en;
assign	demo_rom_ahb_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1030) & rd_en;
assign	demo_rdc_ahb_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1034) & rd_en;
assign	demo_rdc_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1038) & rd_en;
assign	demo_cipher_sec_core_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h103c) & rd_en;
assign	demo_efuse_ctrl_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1040) & rd_en;
assign	demo_sec_ctrl0_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1044) & rd_en;
assign	demo_io_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1048) & rd_en;
assign	misc_ahb_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h104c) & rd_en;
assign	dtss_dt_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1050) & rd_en;
assign	demo_ocmem_ahb_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1054) & rd_en;
assign	demo_timer64_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1058) & rd_en;
assign	demo_pwm_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h105c) & rd_en;
assign	demo_timer_cnt_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1060) & rd_en;
assign	demo_lp_bus_rst_ctrl_status_rd = (apb_addr[31:0] == 32'h1064) & rd_en;
assign	demo_rst_wr = (apb_addr[31:0] == 32'h1600) & wr_en;
assign	soc_soft_rst_n_wr = (apb_addr[31:0] == 32'h1604) & wr_en;
assign	soft_sw_soc_rst_n_rd = (apb_addr[31:0] == 32'h1604) & rd_en;
assign	mdm_rst_n_wr = (apb_addr[31:0] == 32'h1608) & wr_en;
assign	mdm_rst_ctrl_rd = (apb_addr[31:0] == 32'h1608) & rd_en;
assign	full_chip_sw_rst_wr = (apb_addr[31:0] == 32'h160c) & wr_en;
assign	soft_demo_hw_rst_n_wr = (apb_addr[31:0] == 32'h1610) & wr_en;
assign	soft_hw_rst_ctrl_rd = (apb_addr[31:0] == 32'h1610) & rd_en;
assign	demo_top_soft_rst_n_wr = (apb_addr[31:0] == 32'h1614) & wr_en;
assign	demo_top_soc_rst_ctrl_rd = (apb_addr[31:0] == 32'h1614) & rd_en;
assign	demo_crg_rst_n_status_rd = (apb_addr[31:0] == 32'h1618) & rd_en;
assign	demo_lp_cpu_rst_ijtag_ctrl_wr = (apb_addr[31:0] == 32'h162c) & wr_en;
assign	demo_lp_cpu_rst_ijtag_ctrl_rd = (apb_addr[31:0] == 32'h162c) & rd_en;

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		rt32k_muxed0_clk_sel <= 1'h0;
	else if (rt32k_muxed0_clk_sel_wr == 1'b1)
		rt32k_muxed0_clk_sel <= apb_wdata[8:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_main_muxed_clk_sel <= 1'h0;
	else if (demo_main_muxed_clk_sel_wr == 1'b1)
		demo_main_muxed_clk_sel <= apb_wdata[8:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_lp_core_clk_ea <= 1'h1;
	else if (demo_lp_core_clk_ea_wr == 1'b1)
		demo_lp_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_lp_mtime_clk_ea <= 1'h1;
	else if (demo_lp_mtime_clk_ea_wr == 1'b1)
		demo_lp_mtime_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_uart_apb_clk_ea <= 1'h0;
	else if (demo_uart_apb_clk_ea_wr == 1'b1)
		demo_uart_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_uart_core_clk_ea <= 1'h0;
	else if (demo_uart_core_clk_ea_wr == 1'b1)
		demo_uart_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim0_32k_clk_ea <= 1'h0;
	else if (demo_usim0_32k_clk_ea_wr == 1'b1)
		demo_usim0_32k_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim0_apb_clk_ea <= 1'h0;
	else if (demo_usim0_apb_clk_ea_wr == 1'b1)
		demo_usim0_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_gpio_apb_clk_ea <= 1'h0;
	else if (demo_gpio_apb_clk_ea_wr == 1'b1)
		demo_gpio_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_gpio_apb_clk_sel <= 1'h0;
	else if (demo_gpio_apb_clk_sel_wr == 1'b1)
		demo_gpio_apb_clk_sel <= apb_wdata[8:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_i2c_core_clk_ea <= 1'h0;
	else if (demo_i2c_core_clk_ea_wr == 1'b1)
		demo_i2c_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_i2c_apb_clk_ea <= 1'h0;
	else if (demo_i2c_apb_clk_ea_wr == 1'b1)
		demo_i2c_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim1_32k_clk_ea <= 1'h0;
	else if (demo_usim1_32k_clk_ea_wr == 1'b1)
		demo_usim1_32k_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim1_apb_clk_ea <= 1'h0;
	else if (demo_usim1_apb_clk_ea_wr == 1'b1)
		demo_usim1_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_spi_core_clk_ea <= 1'h0;
	else if (demo_spi_core_clk_ea_wr == 1'b1)
		demo_spi_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_spi_apb_clk_ea <= 1'h0;
	else if (demo_spi_apb_clk_ea_wr == 1'b1)
		demo_spi_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pmu_32k_clk_ea <= 1'h1;
	else if (demo_pmu_32k_clk_ea_wr == 1'b1)
		demo_pmu_32k_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pmu_clk_ea <= 1'h1;
	else if (demo_pmu_clk_ea_wr == 1'b1)
		demo_pmu_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pmu_apb_clk_ea <= 1'h1;
	else if (demo_pmu_apb_clk_ea_wr == 1'b1)
		demo_pmu_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_drx_timer_32k_clk_ea <= 1'h0;
	else if (demo_drx_timer_32k_clk_ea_wr == 1'b1)
		demo_drx_timer_32k_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_drx_timer_apb_clk_ea <= 1'h0;
	else if (demo_drx_timer_apb_clk_ea_wr == 1'b1)
		demo_drx_timer_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rtc_apb_clk_ea <= 1'h0;
	else if (demo_rtc_apb_clk_ea_wr == 1'b1)
		demo_rtc_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rtc_core_clk_ea <= 1'h0;
	else if (demo_rtc_core_clk_ea_wr == 1'b1)
		demo_rtc_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_wdt_apb_clk_ea <= 1'h0;
	else if (demo_wdt_apb_clk_ea_wr == 1'b1)
		demo_wdt_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_wdt_clk_ea <= 1'h0;
	else if (demo_wdt_clk_ea_wr == 1'b1)
		demo_wdt_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer_apb_clk_ea <= 1'h0;
	else if (demo_timer_apb_clk_ea_wr == 1'b1)
		demo_timer_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer_apb_clk_sel <= 1'h0;
	else if (demo_timer_apb_clk_sel_wr == 1'b1)
		demo_timer_apb_clk_sel <= apb_wdata[8:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer_cnt_clk_ea <= 1'h0;
	else if (demo_timer_cnt_clk_ea_wr == 1'b1)
		demo_timer_cnt_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sc_apb_clk_ea <= 1'h1;
	else if (demo_sc_apb_clk_ea_wr == 1'b1)
		demo_sc_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rom_ahb_clk_ea <= 1'h1;
	else if (demo_rom_ahb_clk_ea_wr == 1'b1)
		demo_rom_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rdc_ahb_clk_ea <= 1'h1;
	else if (demo_rdc_ahb_clk_ea_wr == 1'b1)
		demo_rdc_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rdc_clk_ea <= 1'h1;
	else if (demo_rdc_clk_ea_wr == 1'b1)
		demo_rdc_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_core_clk_ea <= 1'h0;
	else if (demo_cipher_sec_core_clk_ea_wr == 1'b1)
		demo_cipher_sec_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_aes_clk_ea <= 1'h0;
	else if (demo_cipher_sec_aes_clk_ea_wr == 1'b1)
		demo_cipher_sec_aes_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_hash_clk_ea <= 1'h0;
	else if (demo_cipher_sec_hash_clk_ea_wr == 1'b1)
		demo_cipher_sec_hash_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_sm4_clk_ea <= 1'h0;
	else if (demo_cipher_sec_sm4_clk_ea_wr == 1'b1)
		demo_cipher_sec_sm4_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_pk_clk_ea <= 1'h0;
	else if (demo_cipher_sec_pk_clk_ea_wr == 1'b1)
		demo_cipher_sec_pk_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_pkdiv2_clk_ea <= 1'h0;
	else if (demo_cipher_sec_pkdiv2_clk_ea_wr == 1'b1)
		demo_cipher_sec_pkdiv2_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_pkdiv2_clk_divider_ea_req <= 1'h0;
	else if (demo_cipher_sec_pkdiv2_clk_divider_ea_req_wr == 1'b1)
		demo_cipher_sec_pkdiv2_clk_divider_ea_req <= apb_wdata[4:4];
	else
		demo_cipher_sec_pkdiv2_clk_divider_ea_req <= 1'h0;
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_pkdiv2_clk_divider <= 3'h2;
	else if (demo_cipher_sec_pkdiv2_clk_divider_wr == 1'b1)
		demo_cipher_sec_pkdiv2_clk_divider <= apb_wdata[2:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_efuse_ctrl_ahb_clk_ea <= 1'h1;
	else if (demo_efuse_ctrl_ahb_clk_ea_wr == 1'b1)
		demo_efuse_ctrl_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sec_ctrl0_clk_ea <= 1'h1;
	else if (demo_sec_ctrl0_clk_ea_wr == 1'b1)
		demo_sec_ctrl0_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sec_ctrl1_clk_ea <= 1'h1;
	else if (demo_sec_ctrl1_clk_ea_wr == 1'b1)
		demo_sec_ctrl1_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sec_ctrl2_clk_ea <= 1'h1;
	else if (demo_sec_ctrl2_clk_ea_wr == 1'b1)
		demo_sec_ctrl2_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_io_apb_clk_ea <= 1'h1;
	else if (demo_io_apb_clk_ea_wr == 1'b1)
		demo_io_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		misc_ahb_clk_ea <= 1'h1;
	else if (misc_ahb_clk_ea_wr == 1'b1)
		misc_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		dtss_dt_clk_ea <= 1'h1;
	else if (dtss_dt_clk_ea_wr == 1'b1)
		dtss_dt_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_ocmem_ahb_clk_ea <= 1'h1;
	else if (demo_ocmem_ahb_clk_ea_wr == 1'b1)
		demo_ocmem_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer64_ahb_clk_ea <= 1'h1;
	else if (demo_timer64_ahb_clk_ea_wr == 1'b1)
		demo_timer64_ahb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer64_clk_ea <= 1'h0;
	else if (demo_timer64_clk_ea_wr == 1'b1)
		demo_timer64_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pwm_apb_clk_ea <= 1'h0;
	else if (demo_pwm_apb_clk_ea_wr == 1'b1)
		demo_pwm_apb_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pwm_core_clk_ea <= 1'h0;
	else if (demo_pwm_core_clk_ea_wr == 1'b1)
		demo_pwm_core_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pwm_core_clk_sel <= 1'h0;
	else if (demo_pwm_core_clk_sel_wr == 1'b1)
		demo_pwm_core_clk_sel <= apb_wdata[8:8];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sc_ref_clk_ea <= 1'h1;
	else if (demo_sc_ref_clk_ea_wr == 1'b1)
		demo_sc_ref_clk_ea <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_lp_core_rst_n_sftrstn <= 1'h1;
	else if (demo_lp_core_rst_n_sftrstn_wr == 1'b1)
		demo_lp_core_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_lp_core_demo_por_rst_n_sftrstn <= 1'h1;
	else if (demo_lp_core_demo_por_rst_n_sftrstn_wr == 1'b1)
		demo_lp_core_demo_por_rst_n_sftrstn <= apb_wdata[1:1];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_uart_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_uart_apb_rst_n_sftrstn_wr == 1'b1)
		demo_uart_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim0_32k_rst_n_sftrstn <= 1'h0;
	else if (demo_usim0_32k_rst_n_sftrstn_wr == 1'b1)
		demo_usim0_32k_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_gpio_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_gpio_apb_rst_n_sftrstn_wr == 1'b1)
		demo_gpio_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_i2c_core_rst_n_sftrstn <= 1'h0;
	else if (demo_i2c_core_rst_n_sftrstn_wr == 1'b1)
		demo_i2c_core_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_usim1_32k_rst_n_sftrstn <= 1'h0;
	else if (demo_usim1_32k_rst_n_sftrstn_wr == 1'b1)
		demo_usim1_32k_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_spi_core_rst_n_sftrstn <= 1'h0;
	else if (demo_spi_core_rst_n_sftrstn_wr == 1'b1)
		demo_spi_core_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_drx_timer_32k_rst_n_sftrstn <= 1'h0;
	else if (demo_drx_timer_32k_rst_n_sftrstn_wr == 1'b1)
		demo_drx_timer_32k_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rtc_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_rtc_apb_rst_n_sftrstn_wr == 1'b1)
		demo_rtc_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_wdt_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_wdt_apb_rst_n_sftrstn_wr == 1'b1)
		demo_wdt_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_timer_apb_rst_n_sftrstn_wr == 1'b1)
		demo_timer_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sc_apb_rst_n_sftrstn <= 1'h1;
	else if (demo_sc_apb_rst_n_sftrstn_wr == 1'b1)
		demo_sc_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rom_ahb_rst_n_sftrstn <= 1'h1;
	else if (demo_rom_ahb_rst_n_sftrstn_wr == 1'b1)
		demo_rom_ahb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rdc_ahb_rst_n_sftrstn <= 1'h1;
	else if (demo_rdc_ahb_rst_n_sftrstn_wr == 1'b1)
		demo_rdc_ahb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rdc_rst_n_sftrstn <= 1'h1;
	else if (demo_rdc_rst_n_sftrstn_wr == 1'b1)
		demo_rdc_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_cipher_sec_core_rst_n_sftrstn <= 1'h0;
	else if (demo_cipher_sec_core_rst_n_sftrstn_wr == 1'b1)
		demo_cipher_sec_core_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_efuse_ctrl_logic_rst_n_sftrstn <= 1'h1;
	else if (demo_efuse_ctrl_logic_rst_n_sftrstn_wr == 1'b1)
		demo_efuse_ctrl_logic_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_sec_ctrl0_rst_n_sftrstn <= 1'h1;
	else if (demo_sec_ctrl0_rst_n_sftrstn_wr == 1'b1)
		demo_sec_ctrl0_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_io_apb_rst_n_sftrstn <= 1'h1;
	else if (demo_io_apb_rst_n_sftrstn_wr == 1'b1)
		demo_io_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		misc_ahb_rst_n_sftrstn <= 1'h1;
	else if (misc_ahb_rst_n_sftrstn_wr == 1'b1)
		misc_ahb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		dtss_dt_rst_n_sftrstn <= 1'h1;
	else if (dtss_dt_rst_n_sftrstn_wr == 1'b1)
		dtss_dt_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_ocmem_ahb_rst_n_sftrstn <= 1'h1;
	else if (demo_ocmem_ahb_rst_n_sftrstn_wr == 1'b1)
		demo_ocmem_ahb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer64_ahb_rst_n_sftrstn <= 1'h0;
	else if (demo_timer64_ahb_rst_n_sftrstn_wr == 1'b1)
		demo_timer64_ahb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_pwm_apb_rst_n_sftrstn <= 1'h0;
	else if (demo_pwm_apb_rst_n_sftrstn_wr == 1'b1)
		demo_pwm_apb_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_timer_cnt_rst_n_sftrstn <= 1'h0;
	else if (demo_timer_cnt_rst_n_sftrstn_wr == 1'b1)
		demo_timer_cnt_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_top_lp_bus_rst_n_sftrstn <= 1'h0;
	else if (demo_top_lp_bus_rst_n_sftrstn_wr == 1'b1)
		demo_top_lp_bus_rst_n_sftrstn <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_rst <= 1'h0;
	else if (demo_rst_wr == 1'b1)
		demo_rst <= apb_wdata[0:0];
	else
		demo_rst <= 1'h0;
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		soc_soft_rst_n <= 1'h1;
	else if (soc_soft_rst_n_wr == 1'b1)
		soc_soft_rst_n <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		mdm_rst_n <= 1'h1;
	else if (mdm_rst_n_wr == 1'b1)
		mdm_rst_n <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		full_chip_sw_rst <= 1'h0;
	else if (full_chip_sw_rst_wr == 1'b1)
		full_chip_sw_rst <= apb_wdata[0:0];
	else
		full_chip_sw_rst <= 1'h0;
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		soft_demo_hw_rst_n <= 1'h1;
	else if (soft_demo_hw_rst_n_wr == 1'b1)
		soft_demo_hw_rst_n <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_top_soft_rst_n <= 1'h1;
	else if (demo_top_soft_rst_n_wr == 1'b1)
		demo_top_soft_rst_n <= apb_wdata[0:0];
end

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		demo_lp_cpu_rst_ijtag_ctrl <= 1'h0;
	else if (demo_lp_cpu_rst_ijtag_ctrl_wr == 1'b1)
		demo_lp_cpu_rst_ijtag_ctrl <= apb_wdata[0:0];
end

assign	rt32k_muxed0_clk_ctrl_rdata[8:8] = rt32k_muxed0_clk_sel;
assign	rt32k_muxed0_clk_ctrl_rdata[7:0] = 8'b0;
assign	rt32k_muxed0_clk_ctrl_rdata[31:9] = 23'b0;
assign	rt32k_muxed0_clk_status_rdata[8:8] = rt32k_muxed0_clk_sel_clk0_sel;
assign	rt32k_muxed0_clk_status_rdata[9:9] = rt32k_muxed0_clk_sel_clk1_sel;
assign	rt32k_muxed0_clk_status_rdata[10:10] = rt32k_muxed0_clk_sel_done;
assign	rt32k_muxed0_clk_status_rdata[7:0] = 8'b0;
assign	rt32k_muxed0_clk_status_rdata[31:11] = 21'b0;
assign	demo_main_muxed_clk_ctrl_rdata[8:8] = demo_main_muxed_clk_sel;
assign	demo_main_muxed_clk_ctrl_rdata[7:0] = 8'b0;
assign	demo_main_muxed_clk_ctrl_rdata[31:9] = 23'b0;
assign	demo_main_muxed_clk_status_rdata[8:8] = demo_main_muxed_clk_sel_clk0_sel;
assign	demo_main_muxed_clk_status_rdata[9:9] = demo_main_muxed_clk_sel_clk1_sel;
assign	demo_main_muxed_clk_status_rdata[10:10] = demo_main_muxed_clk_sel_done;
assign	demo_main_muxed_clk_status_rdata[7:0] = 8'b0;
assign	demo_main_muxed_clk_status_rdata[31:11] = 21'b0;
assign	demo_lp_core_clk_ctrl_rdata[0:0] = demo_lp_core_clk_ea;
assign	demo_lp_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_lp_core_clk_status_rdata[0:0] = demo_lp_core_clk_ea_status;
assign	demo_lp_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_lp_mtime_clk_ctrl_rdata[0:0] = demo_lp_mtime_clk_ea;
assign	demo_lp_mtime_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_lp_mtime_clk_status_rdata[0:0] = demo_lp_mtime_clk_ea_status;
assign	demo_lp_mtime_clk_status_rdata[31:1] = 31'b0;
assign	demo_uart_apb_clk_ctrl_rdata[0:0] = demo_uart_apb_clk_ea;
assign	demo_uart_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_uart_apb_clk_status_rdata[0:0] = demo_uart_apb_clk_ea_status;
assign	demo_uart_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_uart_core_clk_ctrl_rdata[0:0] = demo_uart_core_clk_ea;
assign	demo_uart_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_uart_core_clk_status_rdata[0:0] = demo_uart_core_clk_ea_status;
assign	demo_uart_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_usim0_32k_clk_ctrl_rdata[0:0] = demo_usim0_32k_clk_ea;
assign	demo_usim0_32k_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim0_32k_clk_status_rdata[0:0] = demo_usim0_32k_clk_ea_status;
assign	demo_usim0_32k_clk_status_rdata[31:1] = 31'b0;
assign	demo_usim0_apb_clk_ctrl_rdata[0:0] = demo_usim0_apb_clk_ea;
assign	demo_usim0_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim0_apb_clk_status_rdata[0:0] = demo_usim0_apb_clk_ea_status;
assign	demo_usim0_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_gpio_apb_clk_ctrl_rdata[0:0] = demo_gpio_apb_clk_ea;
assign	demo_gpio_apb_clk_ctrl_rdata[8:8] = demo_gpio_apb_clk_sel;
assign	demo_gpio_apb_clk_ctrl_rdata[7:1] = 7'b0;
assign	demo_gpio_apb_clk_ctrl_rdata[31:9] = 23'b0;
assign	demo_gpio_apb_clk_status_rdata[0:0] = demo_gpio_apb_clk_ea_status;
assign	demo_gpio_apb_clk_status_rdata[8:8] = demo_gpio_apb_clk_sel_clk0_sel;
assign	demo_gpio_apb_clk_status_rdata[9:9] = demo_gpio_apb_clk_sel_clk1_sel;
assign	demo_gpio_apb_clk_status_rdata[10:10] = demo_gpio_apb_clk_sel_done;
assign	demo_gpio_apb_clk_status_rdata[7:1] = 7'b0;
assign	demo_gpio_apb_clk_status_rdata[31:11] = 21'b0;
assign	demo_i2c_core_clk_ctrl_rdata[0:0] = demo_i2c_core_clk_ea;
assign	demo_i2c_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_i2c_core_clk_status_rdata[0:0] = demo_i2c_core_clk_ea_status;
assign	demo_i2c_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_i2c_apb_clk_ctrl_rdata[0:0] = demo_i2c_apb_clk_ea;
assign	demo_i2c_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_i2c_apb_clk_status_rdata[0:0] = demo_i2c_apb_clk_ea_status;
assign	demo_i2c_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_usim1_32k_clk_ctrl_rdata[0:0] = demo_usim1_32k_clk_ea;
assign	demo_usim1_32k_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim1_32k_clk_status_rdata[0:0] = demo_usim1_32k_clk_ea_status;
assign	demo_usim1_32k_clk_status_rdata[31:1] = 31'b0;
assign	demo_usim1_apb_clk_ctrl_rdata[0:0] = demo_usim1_apb_clk_ea;
assign	demo_usim1_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim1_apb_clk_status_rdata[0:0] = demo_usim1_apb_clk_ea_status;
assign	demo_usim1_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_spi_core_clk_ctrl_rdata[0:0] = demo_spi_core_clk_ea;
assign	demo_spi_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_spi_core_clk_status_rdata[0:0] = demo_spi_core_clk_ea_status;
assign	demo_spi_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_spi_apb_clk_ctrl_rdata[0:0] = demo_spi_apb_clk_ea;
assign	demo_spi_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_spi_apb_clk_status_rdata[0:0] = demo_spi_apb_clk_ea_status;
assign	demo_spi_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_pmu_32k_clk_ctrl_rdata[0:0] = demo_pmu_32k_clk_ea;
assign	demo_pmu_32k_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_pmu_32k_clk_status_rdata[0:0] = demo_pmu_32k_clk_ea_status;
assign	demo_pmu_32k_clk_status_rdata[31:1] = 31'b0;
assign	demo_pmu_clk_ctrl_rdata[0:0] = demo_pmu_clk_ea;
assign	demo_pmu_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_pmu_clk_status_rdata[0:0] = demo_pmu_clk_ea_status;
assign	demo_pmu_clk_status_rdata[31:1] = 31'b0;
assign	demo_pmu_apb_clk_ctrl_rdata[0:0] = demo_pmu_apb_clk_ea;
assign	demo_pmu_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_pmu_apb_clk_status_rdata[0:0] = demo_pmu_apb_clk_ea_status;
assign	demo_pmu_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_drx_timer_32k_clk_ctrl_rdata[0:0] = demo_drx_timer_32k_clk_ea;
assign	demo_drx_timer_32k_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_drx_timer_32k_clk_status_rdata[0:0] = demo_drx_timer_32k_clk_ea_status;
assign	demo_drx_timer_32k_clk_status_rdata[31:1] = 31'b0;
assign	demo_drx_timer_apb_clk_ctrl_rdata[0:0] = demo_drx_timer_apb_clk_ea;
assign	demo_drx_timer_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_drx_timer_apb_clk_status_rdata[0:0] = demo_drx_timer_apb_clk_ea_status;
assign	demo_drx_timer_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_rtc_apb_clk_ctrl_rdata[0:0] = demo_rtc_apb_clk_ea;
assign	demo_rtc_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_rtc_apb_clk_status_rdata[0:0] = demo_rtc_apb_clk_ea_status;
assign	demo_rtc_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_rtc_core_clk_ctrl_rdata[0:0] = demo_rtc_core_clk_ea;
assign	demo_rtc_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_rtc_core_clk_status_rdata[0:0] = demo_rtc_core_clk_ea_status;
assign	demo_rtc_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_wdt_apb_clk_ctrl_rdata[0:0] = demo_wdt_apb_clk_ea;
assign	demo_wdt_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_wdt_apb_clk_status_rdata[0:0] = demo_wdt_apb_clk_ea_status;
assign	demo_wdt_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_wdt_clk_ctrl_rdata[0:0] = demo_wdt_clk_ea;
assign	demo_wdt_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_wdt_clk_status_rdata[0:0] = demo_wdt_clk_ea_status;
assign	demo_wdt_clk_status_rdata[31:1] = 31'b0;
assign	demo_timer_apb_clk_ctrl_rdata[0:0] = demo_timer_apb_clk_ea;
assign	demo_timer_apb_clk_ctrl_rdata[8:8] = demo_timer_apb_clk_sel;
assign	demo_timer_apb_clk_ctrl_rdata[7:1] = 7'b0;
assign	demo_timer_apb_clk_ctrl_rdata[31:9] = 23'b0;
assign	demo_timer_apb_clk_status_rdata[0:0] = demo_timer_apb_clk_ea_status;
assign	demo_timer_apb_clk_status_rdata[8:8] = demo_timer_apb_clk_sel_clk0_sel;
assign	demo_timer_apb_clk_status_rdata[9:9] = demo_timer_apb_clk_sel_clk1_sel;
assign	demo_timer_apb_clk_status_rdata[10:10] = demo_timer_apb_clk_sel_done;
assign	demo_timer_apb_clk_status_rdata[7:1] = 7'b0;
assign	demo_timer_apb_clk_status_rdata[31:11] = 21'b0;
assign	demo_timer_cnt_clk_ctrl_rdata[0:0] = demo_timer_cnt_clk_ea;
assign	demo_timer_cnt_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer_cnt_clk_status_rdata[0:0] = demo_timer_cnt_clk_ea_status;
assign	demo_timer_cnt_clk_status_rdata[31:1] = 31'b0;
assign	demo_sc_apb_clk_ctrl_rdata[0:0] = demo_sc_apb_clk_ea;
assign	demo_sc_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_sc_apb_clk_status_rdata[0:0] = demo_sc_apb_clk_ea_status;
assign	demo_sc_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_rom_ahb_clk_ctrl_rdata[0:0] = demo_rom_ahb_clk_ea;
assign	demo_rom_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_rom_ahb_clk_status_rdata[0:0] = demo_rom_ahb_clk_ea_status;
assign	demo_rom_ahb_clk_status_rdata[31:1] = 31'b0;
assign	demo_rdc_ahb_clk_ctrl_rdata[0:0] = demo_rdc_ahb_clk_ea;
assign	demo_rdc_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_rdc_ahb_clk_status_rdata[0:0] = demo_rdc_ahb_clk_ea_status;
assign	demo_rdc_ahb_clk_status_rdata[31:1] = 31'b0;
assign	demo_rdc_clk_ctrl_rdata[0:0] = demo_rdc_clk_ea;
assign	demo_rdc_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_rdc_clk_status_rdata[0:0] = demo_rdc_clk_ea_status;
assign	demo_rdc_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_core_clk_ctrl_rdata[0:0] = demo_cipher_sec_core_clk_ea;
assign	demo_cipher_sec_core_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_core_clk_status_rdata[0:0] = demo_cipher_sec_core_clk_ea_status;
assign	demo_cipher_sec_core_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_aes_clk_ctrl_rdata[0:0] = demo_cipher_sec_aes_clk_ea;
assign	demo_cipher_sec_aes_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_aes_clk_status_rdata[0:0] = demo_cipher_sec_aes_clk_ea_status;
assign	demo_cipher_sec_aes_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_hash_clk_ctrl_rdata[0:0] = demo_cipher_sec_hash_clk_ea;
assign	demo_cipher_sec_hash_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_hash_clk_status_rdata[0:0] = demo_cipher_sec_hash_clk_ea_status;
assign	demo_cipher_sec_hash_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_sm4_clk_ctrl_rdata[0:0] = demo_cipher_sec_sm4_clk_ea;
assign	demo_cipher_sec_sm4_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_sm4_clk_status_rdata[0:0] = demo_cipher_sec_sm4_clk_ea_status;
assign	demo_cipher_sec_sm4_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_pk_clk_ctrl_rdata[0:0] = demo_cipher_sec_pk_clk_ea;
assign	demo_cipher_sec_pk_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_pk_clk_status_rdata[0:0] = demo_cipher_sec_pk_clk_ea_status;
assign	demo_cipher_sec_pk_clk_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_pkdiv2_clk_ctrl_rdata[0:0] = demo_cipher_sec_pkdiv2_clk_ea;
assign	demo_cipher_sec_pkdiv2_clk_ctrl_rdata[3:1] = 3'b0;
assign	demo_cipher_sec_pkdiv2_clk_ctrl_rdata[31:5] = 27'b0;
assign	demo_cipher_sec_pkdiv2_clk_divider_rdata[2:0] = demo_cipher_sec_pkdiv2_clk_divider;
assign	demo_cipher_sec_pkdiv2_clk_divider_rdata[31:3] = 29'b0;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[0:0] = demo_cipher_sec_pkdiv2_clk_ea_status;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[12:12] = demo_cipher_sec_pkdiv2_clk_divider_done;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[18:16] = demo_cipher_sec_pkdiv2_clk_divider_status;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[11:1] = 11'b0;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[15:13] = 3'b0;
assign	demo_cipher_sec_pkdiv2_clk_status_rdata[31:19] = 13'b0;
assign	demo_efuse_ctrl_ahb_clk_ctrl_rdata[0:0] = demo_efuse_ctrl_ahb_clk_ea;
assign	demo_efuse_ctrl_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_efuse_ctrl_ahb_clk_status_rdata[0:0] = demo_efuse_ctrl_ahb_clk_ea_status;
assign	demo_efuse_ctrl_ahb_clk_status_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl0_clk_ctrl_rdata[0:0] = demo_sec_ctrl0_clk_ea;
assign	demo_sec_ctrl0_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl0_clk_status_rdata[0:0] = demo_sec_ctrl0_clk_ea_status;
assign	demo_sec_ctrl0_clk_status_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl1_clk_ctrl_rdata[0:0] = demo_sec_ctrl1_clk_ea;
assign	demo_sec_ctrl1_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl1_clk_status_rdata[0:0] = demo_sec_ctrl1_clk_ea_status;
assign	demo_sec_ctrl1_clk_status_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl2_clk_ctrl_rdata[0:0] = demo_sec_ctrl2_clk_ea;
assign	demo_sec_ctrl2_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl2_clk_status_rdata[0:0] = demo_sec_ctrl2_clk_ea_status;
assign	demo_sec_ctrl2_clk_status_rdata[31:1] = 31'b0;
assign	demo_io_apb_clk_ctrl_rdata[0:0] = demo_io_apb_clk_ea;
assign	demo_io_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_io_apb_clk_status_rdata[0:0] = demo_io_apb_clk_ea_status;
assign	demo_io_apb_clk_status_rdata[31:1] = 31'b0;
assign	misc_ahb_clk_ctrl_rdata[0:0] = misc_ahb_clk_ea;
assign	misc_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	misc_ahb_clk_status_rdata[0:0] = misc_ahb_clk_ea_status;
assign	misc_ahb_clk_status_rdata[31:1] = 31'b0;
assign	dtss_dt_clk_ctrl_rdata[0:0] = dtss_dt_clk_ea;
assign	dtss_dt_clk_ctrl_rdata[31:1] = 31'b0;
assign	dtss_dt_clk_status_rdata[0:0] = dtss_dt_clk_ea_status;
assign	dtss_dt_clk_status_rdata[31:1] = 31'b0;
assign	demo_ocmem_ahb_clk_ctrl_rdata[0:0] = demo_ocmem_ahb_clk_ea;
assign	demo_ocmem_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_ocmem_ahb_clk_status_rdata[0:0] = demo_ocmem_ahb_clk_ea_status;
assign	demo_ocmem_ahb_clk_status_rdata[31:1] = 31'b0;
assign	demo_timer64_ahb_clk_ctrl_rdata[0:0] = demo_timer64_ahb_clk_ea;
assign	demo_timer64_ahb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer64_ahb_clk_status_rdata[0:0] = demo_timer64_ahb_clk_ea_status;
assign	demo_timer64_ahb_clk_status_rdata[31:1] = 31'b0;
assign	demo_timer64_clk_ctrl_rdata[0:0] = demo_timer64_clk_ea;
assign	demo_timer64_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer64_clk_status_rdata[0:0] = demo_timer64_clk_ea_status;
assign	demo_timer64_clk_status_rdata[31:1] = 31'b0;
assign	demo_pwm_apb_clk_ctrl_rdata[0:0] = demo_pwm_apb_clk_ea;
assign	demo_pwm_apb_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_pwm_apb_clk_status_rdata[0:0] = demo_pwm_apb_clk_ea_status;
assign	demo_pwm_apb_clk_status_rdata[31:1] = 31'b0;
assign	demo_pwm_core_clk_ctrl_rdata[0:0] = demo_pwm_core_clk_ea;
assign	demo_pwm_core_clk_ctrl_rdata[8:8] = demo_pwm_core_clk_sel;
assign	demo_pwm_core_clk_ctrl_rdata[7:1] = 7'b0;
assign	demo_pwm_core_clk_ctrl_rdata[31:9] = 23'b0;
assign	demo_pwm_core_clk_status_rdata[0:0] = demo_pwm_core_clk_ea_status;
assign	demo_pwm_core_clk_status_rdata[8:8] = demo_pwm_core_clk_sel_clk0_sel;
assign	demo_pwm_core_clk_status_rdata[9:9] = demo_pwm_core_clk_sel_clk1_sel;
assign	demo_pwm_core_clk_status_rdata[10:10] = demo_pwm_core_clk_sel_done;
assign	demo_pwm_core_clk_status_rdata[7:1] = 7'b0;
assign	demo_pwm_core_clk_status_rdata[31:11] = 21'b0;
assign	demo_sc_ref_clk_ctrl_rdata[0:0] = demo_sc_ref_clk_ea;
assign	demo_sc_ref_clk_ctrl_rdata[31:1] = 31'b0;
assign	demo_sc_ref_clk_status_rdata[0:0] = demo_sc_ref_clk_ea_status;
assign	demo_sc_ref_clk_status_rdata[31:1] = 31'b0;
assign	demo_lp_core_rst_ctrl_rdata[0:0] = demo_lp_core_rst_n_sftrstn;
assign	demo_lp_core_rst_ctrl_rdata[1:1] = demo_lp_core_demo_por_rst_n_sftrstn;
assign	demo_lp_core_rst_ctrl_rdata[31:2] = 30'b0;
assign	demo_uart_rst_ctrl_rdata[0:0] = demo_uart_apb_rst_n_sftrstn;
assign	demo_uart_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim0_rst_ctrl_rdata[0:0] = demo_usim0_32k_rst_n_sftrstn;
assign	demo_usim0_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_gpio_rst_ctrl_rdata[0:0] = demo_gpio_apb_rst_n_sftrstn;
assign	demo_gpio_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_i2c0_rst_ctrl_rdata[0:0] = demo_i2c_core_rst_n_sftrstn;
assign	demo_i2c0_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_usim1_rst_ctrl_rdata[0:0] = demo_usim1_32k_rst_n_sftrstn;
assign	demo_usim1_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_spi_rst_ctrl_rdata[0:0] = demo_spi_core_rst_n_sftrstn;
assign	demo_spi_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_drx_timer_rst_ctrl_rdata[0:0] = demo_drx_timer_32k_rst_n_sftrstn;
assign	demo_drx_timer_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_rtc_rst_ctrl_rdata[0:0] = demo_rtc_apb_rst_n_sftrstn;
assign	demo_rtc_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_wdt_rst_ctrl_rdata[0:0] = demo_wdt_apb_rst_n_sftrstn;
assign	demo_wdt_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer0_rst_ctrl_rdata[0:0] = demo_timer_apb_rst_n_sftrstn;
assign	demo_timer0_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_sc_rst_ctrl_rdata[0:0] = demo_sc_apb_rst_n_sftrstn;
assign	demo_sc_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_rom_ahb_rst_ctrl_rdata[0:0] = demo_rom_ahb_rst_n_sftrstn;
assign	demo_rom_ahb_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_rdc_ahb_rst_ctrl_rdata[0:0] = demo_rdc_ahb_rst_n_sftrstn;
assign	demo_rdc_ahb_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_rdc_rst_ctrl_rdata[0:0] = demo_rdc_rst_n_sftrstn;
assign	demo_rdc_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_core_rst_ctrl_rdata[0:0] = demo_cipher_sec_core_rst_n_sftrstn;
assign	demo_cipher_sec_core_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_efuse_ctrl_rst_ctrl_rdata[0:0] = demo_efuse_ctrl_logic_rst_n_sftrstn;
assign	demo_efuse_ctrl_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl0_rst_ctrl_rdata[0:0] = demo_sec_ctrl0_rst_n_sftrstn;
assign	demo_sec_ctrl0_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_io_rst_ctrl_rdata[0:0] = demo_io_apb_rst_n_sftrstn;
assign	demo_io_rst_ctrl_rdata[31:1] = 31'b0;
assign	misc_ahb_rst_ctrl_rdata[0:0] = misc_ahb_rst_n_sftrstn;
assign	misc_ahb_rst_ctrl_rdata[31:1] = 31'b0;
assign	dtss_dt_rst_ctrl_rdata[0:0] = dtss_dt_rst_n_sftrstn;
assign	dtss_dt_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_ocmem_ahb_rst_ctrl_rdata[0:0] = demo_ocmem_ahb_rst_n_sftrstn;
assign	demo_ocmem_ahb_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer64_rst_ctrl_rdata[0:0] = demo_timer64_ahb_rst_n_sftrstn;
assign	demo_timer64_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_pwm_rst_ctrl_rdata[0:0] = demo_pwm_apb_rst_n_sftrstn;
assign	demo_pwm_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_timer_cnt_rst_ctrl_rdata[0:0] = demo_timer_cnt_rst_n_sftrstn;
assign	demo_timer_cnt_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_lp_bus_rst_ctrl_rdata[0:0] = demo_top_lp_bus_rst_n_sftrstn;
assign	demo_lp_bus_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_lp_core_rst_ctrl_status_rdata[0:0] = demo_lp_core_rst_n_status;
assign	demo_lp_core_rst_ctrl_status_rdata[1:1] = demo_lp_core_demo_por_rst_n_status;
assign	demo_lp_core_rst_ctrl_status_rdata[31:2] = 30'b0;
assign	demo_uart_rst_ctrl_status_rdata[0:0] = demo_uart_apb_rst_n_status;
assign	demo_uart_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_usim0_rst_ctrl_status_rdata[0:0] = demo_usim0_32k_rst_n_status;
assign	demo_usim0_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_gpio_rst_ctrl_status_rdata[0:0] = demo_gpio_apb_rst_n_status;
assign	demo_gpio_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_i2c0_rst_ctrl_status_rdata[0:0] = demo_i2c_core_rst_n_status;
assign	demo_i2c0_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_usim1_rst_ctrl_status_rdata[0:0] = demo_usim1_32k_rst_n_status;
assign	demo_usim1_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_spi_rst_ctrl_status_rdata[0:0] = demo_spi_core_rst_n_status;
assign	demo_spi_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_drx_timer_rst_ctrl_status_rdata[0:0] = demo_drx_timer_32k_rst_n_status;
assign	demo_drx_timer_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_rtc_rst_ctrl_status_rdata[0:0] = demo_rtc_apb_rst_n_status;
assign	demo_rtc_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_wdt_rst_ctrl_status_rdata[0:0] = demo_wdt_apb_rst_n_status;
assign	demo_wdt_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_timer0_rst_ctrl_status_rdata[0:0] = demo_timer_apb_rst_n_status;
assign	demo_timer0_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_sc_rst_ctrl_status_rdata[0:0] = demo_sc_apb_rst_n_status;
assign	demo_sc_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_rom_ahb_rst_ctrl_status_rdata[0:0] = demo_rom_ahb_rst_n_status;
assign	demo_rom_ahb_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_rdc_ahb_rst_ctrl_status_rdata[0:0] = demo_rdc_ahb_rst_n_status;
assign	demo_rdc_ahb_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_rdc_rst_ctrl_status_rdata[0:0] = demo_rdc_rst_n_status;
assign	demo_rdc_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_cipher_sec_core_rst_ctrl_status_rdata[0:0] = demo_cipher_sec_core_rst_n_status;
assign	demo_cipher_sec_core_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_efuse_ctrl_rst_ctrl_status_rdata[0:0] = demo_efuse_ctrl_logic_rst_n_status;
assign	demo_efuse_ctrl_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_sec_ctrl0_rst_ctrl_status_rdata[0:0] = demo_sec_ctrl0_rst_n_status;
assign	demo_sec_ctrl0_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_io_rst_ctrl_status_rdata[0:0] = demo_io_apb_rst_n_status;
assign	demo_io_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	misc_ahb_rst_ctrl_status_rdata[0:0] = misc_ahb_rst_n_status;
assign	misc_ahb_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	dtss_dt_rst_ctrl_status_rdata[0:0] = dtss_dt_rst_n_status;
assign	dtss_dt_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_ocmem_ahb_rst_ctrl_status_rdata[0:0] = demo_ocmem_ahb_rst_n_status;
assign	demo_ocmem_ahb_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_timer64_rst_ctrl_status_rdata[0:0] = demo_timer64_ahb_rst_n_status;
assign	demo_timer64_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_pwm_rst_ctrl_status_rdata[0:0] = demo_pwm_apb_rst_n_status;
assign	demo_pwm_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_timer_cnt_rst_ctrl_status_rdata[0:0] = demo_timer_cnt_rst_n_status;
assign	demo_timer_cnt_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	demo_lp_bus_rst_ctrl_status_rdata[0:0] = demo_top_lp_bus_rst_n_status;
assign	demo_lp_bus_rst_ctrl_status_rdata[31:1] = 31'b0;
assign	soft_sw_soc_rst_n_rdata[0:0] = soc_soft_rst_n;
assign	soft_sw_soc_rst_n_rdata[31:1] = 31'b0;
assign	mdm_rst_ctrl_rdata[0:0] = mdm_rst_n;
assign	mdm_rst_ctrl_rdata[31:1] = 31'b0;
assign	soft_hw_rst_ctrl_rdata[0:0] = soft_demo_hw_rst_n;
assign	soft_hw_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_top_soc_rst_ctrl_rdata[0:0] = demo_top_soft_rst_n;
assign	demo_top_soc_rst_ctrl_rdata[31:1] = 31'b0;
assign	demo_crg_rst_n_status_rdata[0:0] = soc_async_rst_n_status;
assign	demo_crg_rst_n_status_rdata[1:1] = demo_lp_core_demo_por_rst_n_status;
assign	demo_crg_rst_n_status_rdata[2:2] = demo_lp_bus_rst_n_status;
assign	demo_crg_rst_n_status_rdata[3:3] = demo_efuse_ctrl_demo_por_rst_n_status;
assign	demo_crg_rst_n_status_rdata[4:4] = demo_pmu_rst_n_status;
assign	demo_crg_rst_n_status_rdata[5:5] = demo_pmu_apb_rst_n_status;
assign	demo_crg_rst_n_status_rdata[6:6] = demo_pmu_32k_rst_n_status;
assign	demo_crg_rst_n_status_rdata[7:7] = demo_pmu_demo_por_rst_n_status;
assign	demo_crg_rst_n_status_rdata[8:8] = demo_crg_apb_rst_n_status;
assign	demo_crg_rst_n_status_rdata[9:9] = demo_sc_demo_por_rst_n_status;
assign	demo_crg_rst_n_status_rdata[10:10] = soc_soft_rst_n_out_status;
assign	demo_crg_rst_n_status_rdata[11:11] = mdm_sys_rst_n_status;
assign	demo_crg_rst_n_status_rdata[31:12] = 20'b0;
assign	demo_lp_cpu_rst_ijtag_ctrl_rdata[0:0] = demo_lp_cpu_rst_ijtag_ctrl;
assign	demo_lp_cpu_rst_ijtag_ctrl_rdata[31:1] = 31'b0;

assign apb_rdata_pre[31:0] = 
	rt32k_muxed0_clk_ctrl_rd ? rt32k_muxed0_clk_ctrl_rdata[31:0] :
	rt32k_muxed0_clk_status_rd ? rt32k_muxed0_clk_status_rdata[31:0] :
	demo_main_muxed_clk_ctrl_rd ? demo_main_muxed_clk_ctrl_rdata[31:0] :
	demo_main_muxed_clk_status_rd ? demo_main_muxed_clk_status_rdata[31:0] :
	demo_lp_core_clk_ctrl_rd ? demo_lp_core_clk_ctrl_rdata[31:0] :
	demo_lp_core_clk_status_rd ? demo_lp_core_clk_status_rdata[31:0] :
	demo_lp_mtime_clk_ctrl_rd ? demo_lp_mtime_clk_ctrl_rdata[31:0] :
	demo_lp_mtime_clk_status_rd ? demo_lp_mtime_clk_status_rdata[31:0] :
	demo_uart_apb_clk_ctrl_rd ? demo_uart_apb_clk_ctrl_rdata[31:0] :
	demo_uart_apb_clk_status_rd ? demo_uart_apb_clk_status_rdata[31:0] :
	demo_uart_core_clk_ctrl_rd ? demo_uart_core_clk_ctrl_rdata[31:0] :
	demo_uart_core_clk_status_rd ? demo_uart_core_clk_status_rdata[31:0] :
	demo_usim0_32k_clk_ctrl_rd ? demo_usim0_32k_clk_ctrl_rdata[31:0] :
	demo_usim0_32k_clk_status_rd ? demo_usim0_32k_clk_status_rdata[31:0] :
	demo_usim0_apb_clk_ctrl_rd ? demo_usim0_apb_clk_ctrl_rdata[31:0] :
	demo_usim0_apb_clk_status_rd ? demo_usim0_apb_clk_status_rdata[31:0] :
	demo_gpio_apb_clk_ctrl_rd ? demo_gpio_apb_clk_ctrl_rdata[31:0] :
	demo_gpio_apb_clk_status_rd ? demo_gpio_apb_clk_status_rdata[31:0] :
	demo_i2c_core_clk_ctrl_rd ? demo_i2c_core_clk_ctrl_rdata[31:0] :
	demo_i2c_core_clk_status_rd ? demo_i2c_core_clk_status_rdata[31:0] :
	demo_i2c_apb_clk_ctrl_rd ? demo_i2c_apb_clk_ctrl_rdata[31:0] :
	demo_i2c_apb_clk_status_rd ? demo_i2c_apb_clk_status_rdata[31:0] :
	demo_usim1_32k_clk_ctrl_rd ? demo_usim1_32k_clk_ctrl_rdata[31:0] :
	demo_usim1_32k_clk_status_rd ? demo_usim1_32k_clk_status_rdata[31:0] :
	demo_usim1_apb_clk_ctrl_rd ? demo_usim1_apb_clk_ctrl_rdata[31:0] :
	demo_usim1_apb_clk_status_rd ? demo_usim1_apb_clk_status_rdata[31:0] :
	demo_spi_core_clk_ctrl_rd ? demo_spi_core_clk_ctrl_rdata[31:0] :
	demo_spi_core_clk_status_rd ? demo_spi_core_clk_status_rdata[31:0] :
	demo_spi_apb_clk_ctrl_rd ? demo_spi_apb_clk_ctrl_rdata[31:0] :
	demo_spi_apb_clk_status_rd ? demo_spi_apb_clk_status_rdata[31:0] :
	demo_pmu_32k_clk_ctrl_rd ? demo_pmu_32k_clk_ctrl_rdata[31:0] :
	demo_pmu_32k_clk_status_rd ? demo_pmu_32k_clk_status_rdata[31:0] :
	demo_pmu_clk_ctrl_rd ? demo_pmu_clk_ctrl_rdata[31:0] :
	demo_pmu_clk_status_rd ? demo_pmu_clk_status_rdata[31:0] :
	demo_pmu_apb_clk_ctrl_rd ? demo_pmu_apb_clk_ctrl_rdata[31:0] :
	demo_pmu_apb_clk_status_rd ? demo_pmu_apb_clk_status_rdata[31:0] :
	demo_drx_timer_32k_clk_ctrl_rd ? demo_drx_timer_32k_clk_ctrl_rdata[31:0] :
	demo_drx_timer_32k_clk_status_rd ? demo_drx_timer_32k_clk_status_rdata[31:0] :
	demo_drx_timer_apb_clk_ctrl_rd ? demo_drx_timer_apb_clk_ctrl_rdata[31:0] :
	demo_drx_timer_apb_clk_status_rd ? demo_drx_timer_apb_clk_status_rdata[31:0] :
	demo_rtc_apb_clk_ctrl_rd ? demo_rtc_apb_clk_ctrl_rdata[31:0] :
	demo_rtc_apb_clk_status_rd ? demo_rtc_apb_clk_status_rdata[31:0] :
	demo_rtc_core_clk_ctrl_rd ? demo_rtc_core_clk_ctrl_rdata[31:0] :
	demo_rtc_core_clk_status_rd ? demo_rtc_core_clk_status_rdata[31:0] :
	demo_wdt_apb_clk_ctrl_rd ? demo_wdt_apb_clk_ctrl_rdata[31:0] :
	demo_wdt_apb_clk_status_rd ? demo_wdt_apb_clk_status_rdata[31:0] :
	demo_wdt_clk_ctrl_rd ? demo_wdt_clk_ctrl_rdata[31:0] :
	demo_wdt_clk_status_rd ? demo_wdt_clk_status_rdata[31:0] :
	demo_timer_apb_clk_ctrl_rd ? demo_timer_apb_clk_ctrl_rdata[31:0] :
	demo_timer_apb_clk_status_rd ? demo_timer_apb_clk_status_rdata[31:0] :
	demo_timer_cnt_clk_ctrl_rd ? demo_timer_cnt_clk_ctrl_rdata[31:0] :
	demo_timer_cnt_clk_status_rd ? demo_timer_cnt_clk_status_rdata[31:0] :
	demo_sc_apb_clk_ctrl_rd ? demo_sc_apb_clk_ctrl_rdata[31:0] :
	demo_sc_apb_clk_status_rd ? demo_sc_apb_clk_status_rdata[31:0] :
	demo_rom_ahb_clk_ctrl_rd ? demo_rom_ahb_clk_ctrl_rdata[31:0] :
	demo_rom_ahb_clk_status_rd ? demo_rom_ahb_clk_status_rdata[31:0] :
	demo_rdc_ahb_clk_ctrl_rd ? demo_rdc_ahb_clk_ctrl_rdata[31:0] :
	demo_rdc_ahb_clk_status_rd ? demo_rdc_ahb_clk_status_rdata[31:0] :
	demo_rdc_clk_ctrl_rd ? demo_rdc_clk_ctrl_rdata[31:0] :
	demo_rdc_clk_status_rd ? demo_rdc_clk_status_rdata[31:0] :
	demo_cipher_sec_core_clk_ctrl_rd ? demo_cipher_sec_core_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_core_clk_status_rd ? demo_cipher_sec_core_clk_status_rdata[31:0] :
	demo_cipher_sec_aes_clk_ctrl_rd ? demo_cipher_sec_aes_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_aes_clk_status_rd ? demo_cipher_sec_aes_clk_status_rdata[31:0] :
	demo_cipher_sec_hash_clk_ctrl_rd ? demo_cipher_sec_hash_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_hash_clk_status_rd ? demo_cipher_sec_hash_clk_status_rdata[31:0] :
	demo_cipher_sec_sm4_clk_ctrl_rd ? demo_cipher_sec_sm4_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_sm4_clk_status_rd ? demo_cipher_sec_sm4_clk_status_rdata[31:0] :
	demo_cipher_sec_pk_clk_ctrl_rd ? demo_cipher_sec_pk_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_pk_clk_status_rd ? demo_cipher_sec_pk_clk_status_rdata[31:0] :
	demo_cipher_sec_pkdiv2_clk_ctrl_rd ? demo_cipher_sec_pkdiv2_clk_ctrl_rdata[31:0] :
	demo_cipher_sec_pkdiv2_clk_divider_rd ? demo_cipher_sec_pkdiv2_clk_divider_rdata[31:0] :
	demo_cipher_sec_pkdiv2_clk_status_rd ? demo_cipher_sec_pkdiv2_clk_status_rdata[31:0] :
	demo_efuse_ctrl_ahb_clk_ctrl_rd ? demo_efuse_ctrl_ahb_clk_ctrl_rdata[31:0] :
	demo_efuse_ctrl_ahb_clk_status_rd ? demo_efuse_ctrl_ahb_clk_status_rdata[31:0] :
	demo_sec_ctrl0_clk_ctrl_rd ? demo_sec_ctrl0_clk_ctrl_rdata[31:0] :
	demo_sec_ctrl0_clk_status_rd ? demo_sec_ctrl0_clk_status_rdata[31:0] :
	demo_sec_ctrl1_clk_ctrl_rd ? demo_sec_ctrl1_clk_ctrl_rdata[31:0] :
	demo_sec_ctrl1_clk_status_rd ? demo_sec_ctrl1_clk_status_rdata[31:0] :
	demo_sec_ctrl2_clk_ctrl_rd ? demo_sec_ctrl2_clk_ctrl_rdata[31:0] :
	demo_sec_ctrl2_clk_status_rd ? demo_sec_ctrl2_clk_status_rdata[31:0] :
	demo_io_apb_clk_ctrl_rd ? demo_io_apb_clk_ctrl_rdata[31:0] :
	demo_io_apb_clk_status_rd ? demo_io_apb_clk_status_rdata[31:0] :
	misc_ahb_clk_ctrl_rd ? misc_ahb_clk_ctrl_rdata[31:0] :
	misc_ahb_clk_status_rd ? misc_ahb_clk_status_rdata[31:0] :
	dtss_dt_clk_ctrl_rd ? dtss_dt_clk_ctrl_rdata[31:0] :
	dtss_dt_clk_status_rd ? dtss_dt_clk_status_rdata[31:0] :
	demo_ocmem_ahb_clk_ctrl_rd ? demo_ocmem_ahb_clk_ctrl_rdata[31:0] :
	demo_ocmem_ahb_clk_status_rd ? demo_ocmem_ahb_clk_status_rdata[31:0] :
	demo_timer64_ahb_clk_ctrl_rd ? demo_timer64_ahb_clk_ctrl_rdata[31:0] :
	demo_timer64_ahb_clk_status_rd ? demo_timer64_ahb_clk_status_rdata[31:0] :
	demo_timer64_clk_ctrl_rd ? demo_timer64_clk_ctrl_rdata[31:0] :
	demo_timer64_clk_status_rd ? demo_timer64_clk_status_rdata[31:0] :
	demo_pwm_apb_clk_ctrl_rd ? demo_pwm_apb_clk_ctrl_rdata[31:0] :
	demo_pwm_apb_clk_status_rd ? demo_pwm_apb_clk_status_rdata[31:0] :
	demo_pwm_core_clk_ctrl_rd ? demo_pwm_core_clk_ctrl_rdata[31:0] :
	demo_pwm_core_clk_status_rd ? demo_pwm_core_clk_status_rdata[31:0] :
	demo_sc_ref_clk_ctrl_rd ? demo_sc_ref_clk_ctrl_rdata[31:0] :
	demo_sc_ref_clk_status_rd ? demo_sc_ref_clk_status_rdata[31:0] :
	demo_lp_core_rst_ctrl_rd ? demo_lp_core_rst_ctrl_rdata[31:0] :
	demo_uart_rst_ctrl_rd ? demo_uart_rst_ctrl_rdata[31:0] :
	demo_usim0_rst_ctrl_rd ? demo_usim0_rst_ctrl_rdata[31:0] :
	demo_gpio_rst_ctrl_rd ? demo_gpio_rst_ctrl_rdata[31:0] :
	demo_i2c0_rst_ctrl_rd ? demo_i2c0_rst_ctrl_rdata[31:0] :
	demo_usim1_rst_ctrl_rd ? demo_usim1_rst_ctrl_rdata[31:0] :
	demo_spi_rst_ctrl_rd ? demo_spi_rst_ctrl_rdata[31:0] :
	demo_drx_timer_rst_ctrl_rd ? demo_drx_timer_rst_ctrl_rdata[31:0] :
	demo_rtc_rst_ctrl_rd ? demo_rtc_rst_ctrl_rdata[31:0] :
	demo_wdt_rst_ctrl_rd ? demo_wdt_rst_ctrl_rdata[31:0] :
	demo_timer0_rst_ctrl_rd ? demo_timer0_rst_ctrl_rdata[31:0] :
	demo_sc_rst_ctrl_rd ? demo_sc_rst_ctrl_rdata[31:0] :
	demo_rom_ahb_rst_ctrl_rd ? demo_rom_ahb_rst_ctrl_rdata[31:0] :
	demo_rdc_ahb_rst_ctrl_rd ? demo_rdc_ahb_rst_ctrl_rdata[31:0] :
	demo_rdc_rst_ctrl_rd ? demo_rdc_rst_ctrl_rdata[31:0] :
	demo_cipher_sec_core_rst_ctrl_rd ? demo_cipher_sec_core_rst_ctrl_rdata[31:0] :
	demo_efuse_ctrl_rst_ctrl_rd ? demo_efuse_ctrl_rst_ctrl_rdata[31:0] :
	demo_sec_ctrl0_rst_ctrl_rd ? demo_sec_ctrl0_rst_ctrl_rdata[31:0] :
	demo_io_rst_ctrl_rd ? demo_io_rst_ctrl_rdata[31:0] :
	misc_ahb_rst_ctrl_rd ? misc_ahb_rst_ctrl_rdata[31:0] :
	dtss_dt_rst_ctrl_rd ? dtss_dt_rst_ctrl_rdata[31:0] :
	demo_ocmem_ahb_rst_ctrl_rd ? demo_ocmem_ahb_rst_ctrl_rdata[31:0] :
	demo_timer64_rst_ctrl_rd ? demo_timer64_rst_ctrl_rdata[31:0] :
	demo_pwm_rst_ctrl_rd ? demo_pwm_rst_ctrl_rdata[31:0] :
	demo_timer_cnt_rst_ctrl_rd ? demo_timer_cnt_rst_ctrl_rdata[31:0] :
	demo_lp_bus_rst_ctrl_rd ? demo_lp_bus_rst_ctrl_rdata[31:0] :
	demo_lp_core_rst_ctrl_status_rd ? demo_lp_core_rst_ctrl_status_rdata[31:0] :
	demo_uart_rst_ctrl_status_rd ? demo_uart_rst_ctrl_status_rdata[31:0] :
	demo_usim0_rst_ctrl_status_rd ? demo_usim0_rst_ctrl_status_rdata[31:0] :
	demo_gpio_rst_ctrl_status_rd ? demo_gpio_rst_ctrl_status_rdata[31:0] :
	demo_i2c0_rst_ctrl_status_rd ? demo_i2c0_rst_ctrl_status_rdata[31:0] :
	demo_usim1_rst_ctrl_status_rd ? demo_usim1_rst_ctrl_status_rdata[31:0] :
	demo_spi_rst_ctrl_status_rd ? demo_spi_rst_ctrl_status_rdata[31:0] :
	demo_drx_timer_rst_ctrl_status_rd ? demo_drx_timer_rst_ctrl_status_rdata[31:0] :
	demo_rtc_rst_ctrl_status_rd ? demo_rtc_rst_ctrl_status_rdata[31:0] :
	demo_wdt_rst_ctrl_status_rd ? demo_wdt_rst_ctrl_status_rdata[31:0] :
	demo_timer0_rst_ctrl_status_rd ? demo_timer0_rst_ctrl_status_rdata[31:0] :
	demo_sc_rst_ctrl_status_rd ? demo_sc_rst_ctrl_status_rdata[31:0] :
	demo_rom_ahb_rst_ctrl_status_rd ? demo_rom_ahb_rst_ctrl_status_rdata[31:0] :
	demo_rdc_ahb_rst_ctrl_status_rd ? demo_rdc_ahb_rst_ctrl_status_rdata[31:0] :
	demo_rdc_rst_ctrl_status_rd ? demo_rdc_rst_ctrl_status_rdata[31:0] :
	demo_cipher_sec_core_rst_ctrl_status_rd ? demo_cipher_sec_core_rst_ctrl_status_rdata[31:0] :
	demo_efuse_ctrl_rst_ctrl_status_rd ? demo_efuse_ctrl_rst_ctrl_status_rdata[31:0] :
	demo_sec_ctrl0_rst_ctrl_status_rd ? demo_sec_ctrl0_rst_ctrl_status_rdata[31:0] :
	demo_io_rst_ctrl_status_rd ? demo_io_rst_ctrl_status_rdata[31:0] :
	misc_ahb_rst_ctrl_status_rd ? misc_ahb_rst_ctrl_status_rdata[31:0] :
	dtss_dt_rst_ctrl_status_rd ? dtss_dt_rst_ctrl_status_rdata[31:0] :
	demo_ocmem_ahb_rst_ctrl_status_rd ? demo_ocmem_ahb_rst_ctrl_status_rdata[31:0] :
	demo_timer64_rst_ctrl_status_rd ? demo_timer64_rst_ctrl_status_rdata[31:0] :
	demo_pwm_rst_ctrl_status_rd ? demo_pwm_rst_ctrl_status_rdata[31:0] :
	demo_timer_cnt_rst_ctrl_status_rd ? demo_timer_cnt_rst_ctrl_status_rdata[31:0] :
	demo_lp_bus_rst_ctrl_status_rd ? demo_lp_bus_rst_ctrl_status_rdata[31:0] :
	soft_sw_soc_rst_n_rd ? soft_sw_soc_rst_n_rdata[31:0] :
	mdm_rst_ctrl_rd ? mdm_rst_ctrl_rdata[31:0] :
	soft_hw_rst_ctrl_rd ? soft_hw_rst_ctrl_rdata[31:0] :
	demo_top_soc_rst_ctrl_rd ? demo_top_soc_rst_ctrl_rdata[31:0] :
	demo_crg_rst_n_status_rd ? demo_crg_rst_n_status_rdata[31:0] :
	demo_lp_cpu_rst_ijtag_ctrl_rd ? demo_lp_cpu_rst_ijtag_ctrl_rdata[31:0] :
	32'hdeadbeef;

always @(posedge apb_clk or negedge apb_rst_n)begin
	if(!apb_rst_n)
		apb_rdata[31:0] <= 32'h0;
	else
		apb_rdata[31:0] <= apb_rdata_pre[31:0];
end

endmodule
