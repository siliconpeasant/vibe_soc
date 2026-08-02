// =================================================================================================
// Copyright(C) 2020 - Cygnusemi Co.,Ltd. All rights reserved.                                    
// =================================================================================================
// Powered by Gang He, Shuwei Xuan, Cuiping Zhou, etc.
// =================================================================================================
// File Name    : demo_crg_top.v
// Module       : demo_crg_top
// Function     : demo_crg_top integration
// Type         : RTL
// -------------------------------------------------------------------------------------------------
// Update History :
// -------------------------------------------------------------------------------------------------
// Rev.Level    Date                  Coded by                Contents
// 1.0          2026-08-02 13:16:08       demo_user               Init
//
// =================================================================================================
// End Revision
// =================================================================================================

// =================================================================================================
// RTL Header
// =================================================================================================

module demo_crg_top(
	output soc_async_rst_n,
	input                                n205_sysresetreq,
	input                                pmu_alpwron_rdy,
	input                                efuse_ctrl_por_done,
	input  [1:0]                         boot_mode,
	output pmu_ao_clkgat_ack,
	input                                demo_wdt_rst,
	input                                demo_wdt_rst_mask,
	input                                jtag_rst_n,
	output mdm_sys_rst_n,
	output demo_por_rst_n_out,
	output demo_hw_rst_n_out,
	output soc_soft_rst_n_out,
	output lp_core_rst_n_out,
	input                                pmu_clk_switch_refto32K_req,
	output pmu_clk_switch_refto32K_ack,
	input                                t_sensor_ot_rst_n,
	input                                hw_por_rst_req_mode,
	input                                wake_time_out_rst_pulse_req,
	input                                dft_test_clock,
	input                                test_mode,
	input                                dft_div_rstn,
	input                                sysrstn_in,
	input                                apb_clk,
	input                                apb_rst_n,
	input                                demo_32k_sko,
	input                                demo_32k_clk,
	input                                ao_32k_clk_sel,
	input                                apb_sel,
	input                                apb_enable,
	input                                apb_write,
	input  [31:0]                        apb_addr,
	input  [31:0]                        apb_wdata,
	input                                dft_icg_mode_root,
	input                                demo_main_clk,
	input                                demo_ref_clk,
	input                                demo_bb_clk,
	input                                demo_clkgat_req,
	input                                demo_rom_gat_n,
	input                                test_rstn,
	input                                demo_lpcore_rst_n,
	input                                demo_soctop_rst_n,
	output [31:0]                        apb_rdata,
	output                               apb_ready,
	output                               apb_slverr,
	output                               demo_lp_core_rst_n,
	output                               demo_lp_core_demo_por_rst_n,
	output                               demo_uart_apb_rst_n,
	output                               demo_usim0_32k_rst_n,
	output                               demo_gpio_apb_rst_n,
	output                               demo_i2c_core_rst_n,
	output                               demo_usim1_32k_rst_n,
	output                               demo_spi_core_rst_n,
	output                               demo_drx_timer_32k_rst_n,
	output                               demo_rtc_apb_rst_n,
	output                               demo_wdt_apb_rst_n,
	output                               demo_timer_apb_rst_n,
	output                               demo_sc_apb_rst_n,
	output                               demo_rom_ahb_rst_n,
	output                               demo_rdc_ahb_rst_n,
	output                               demo_rdc_rst_n,
	output                               demo_cipher_sec_core_rst_n,
	output                               demo_efuse_ctrl_logic_rst_n,
	output                               demo_sec_ctrl0_rst_n,
	output                               demo_io_apb_rst_n,
	output                               misc_ahb_rst_n,
	output                               dtss_dt_rst_n,
	output                               demo_ocmem_ahb_rst_n,
	output                               demo_timer64_ahb_rst_n,
	output                               demo_pwm_apb_rst_n,
	output                               demo_timer_cnt_rst_n,
	output                               demo_top_lp_bus_rst_n,
	output                               demo_lp_core_clk,
	output                               demo_lp_mtime_clk,
	output                               demo_uart_apb_clk,
	output                               demo_uart_core_clk,
	output                               demo_usim0_32k_clk,
	output                               demo_usim0_apb_clk,
	output                               demo_gpio_apb_clk,
	output                               demo_i2c_core_clk,
	output                               demo_i2c_apb_clk,
	output                               demo_usim1_32k_clk,
	output                               demo_usim1_apb_clk,
	output                               demo_spi_core_clk,
	output                               demo_spi_apb_clk,
	output                               demo_pmu_32k_clk,
	output                               demo_pmu_clk,
	output                               demo_pmu_apb_clk,
	output                               demo_crg_apb_clk,
	output                               demo_drx_timer_32k_clk,
	output                               demo_drx_timer_phy_clk,
	output                               demo_drx_timer_apb_clk,
	output                               demo_rtc_apb_clk,
	output                               demo_rtc_core_clk,
	output                               demo_wdt_apb_clk,
	output                               demo_wdt_clk,
	output                               demo_timer_apb_clk,
	output                               demo_timer_cnt_clk,
	output                               demo_sc_apb_clk,
	output                               demo_rom_ahb_clk,
	output                               demo_rdc_ahb_clk,
	output                               demo_rdc_clk,
	output                               demo_cipher_sec_core_clk,
	output                               demo_cipher_sec_aes_clk,
	output                               demo_cipher_sec_hash_clk,
	output                               demo_cipher_sec_sm4_clk,
	output                               demo_cipher_sec_pk_clk,
	output                               demo_cipher_sec_pkdiv2_clk,
	output                               demo_efuse_ctrl_ahb_clk,
	output                               demo_sec_ctrl0_clk,
	output                               demo_sec_ctrl1_clk,
	output                               demo_sec_ctrl2_clk,
	output                               demo_io_apb_clk,
	output                               demo_lp_bus_clk,
	output                               soc_32k_clk,
	output                               misc_ahb_clk,
	output                               dtss_dt_clk,
	output                               demo_ocmem_ahb_clk,
	output                               demo_timer64_ahb_clk,
	output                               demo_timer64_clk,
	output                               demo_pwm_apb_clk,
	output                               demo_pwm_core_clk,
	output                               demo_sc_ref_clk,
	output                               demo_uart_core_rst_n,
	output                               demo_usim0_apb_rst_n,
	output                               demo_i2c_apb_rst_n,
	output                               demo_usim1_apb_rst_n,
	output                               demo_spi_apb_rst_n,
	output                               demo_pmu_rst_n,
	output                               demo_pmu_apb_rst_n,
	output                               demo_pmu_32k_rst_n,
	output                               demo_pmu_demo_por_rst_n,
	output                               demo_crg_apb_rst_n,
	output                               demo_drx_timer_phy_rst_n,
	output                               demo_drx_timer_apb_rst_n,
	output                               demo_rtc_core_rst_n,
	output                               demo_wdt_rst_n,
	output                               demo_sc_demo_por_rst_n,
	output                               demo_cipher_sec_pk_rst_n,
	output                               demo_efuse_ctrl_demo_por_rst_n,
	output                               demo_sec_ctrl1_rst_n,
	output                               demo_sec_ctrl2_rst_n,
	output                               demo_timer64_rst_n,
	output                               demo_pwm_core_rst_n,
	output                               demo_lp_bus_rst_n
);


// =================================================================================================
// Signals Declaration
// =================================================================================================
	wire                                          demo_cipher_sec_sm4_clk_demo_clkgat_req_sync;
	wire                                          demo_pwm_apb_clk_ea;
	wire                                          demo_uart_core_rst_n_sftrstn;
	wire                                          soc_async_rst_n_status;
	wire                                          misc_ahb_rst_n_sftrstn;
	wire                                          demo_rtc_core_clk_ea;
	wire                                          demo_drx_timer_32k_clk_ea;
	wire                                          rt32k_muxed1_clk;
	wire                                          demo_usim1_apb_clk_ea;
	wire                                          demo_cipher_sec_aes_clk_ea_status;
	wire                                          demo_sec_ctrl1_clk_ea;
	wire                                          demo_lp_cpu_rst_ijtag_ctrl;
	wire                                          demo_usim0_32k_clk_ea;
	wire                                          demo_main_muxed_clk_sel_clk1_sel;
	wire                                          demo_cipher_sec_aes_clk_demo_clkgat_req_sync;
	wire                                          demo_ocmem_ahb_clk_ea_status;
	wire                                          demo_rtc_apb_rst_n_sftrstn;
	wire                                          demo_cipher_sec_pk_rst_n_sftrstn;
	wire                                          demo_lp_mtime_clk_demo_clkgat_req_sync;
	wire                                          demo_timer64_ahb_clk_ea;
	wire                                          demo_pwm_core_clk_ea_status;
	wire                                          demo_por_rst_n;
	wire                                          demo_pwm_core_clk_sel;
	wire                                          demo_rom_ahb_rst_n_sftrstn;
	wire                                          demo_pmu_apb_clk_ea_status;
	wire                                          demo_cipher_sec_core_clk_demo_clkgat_req_sync;
	wire                                          cpuss_pll_lock_fail_out;
	wire                                          demo_gpio_apb_clk_sel_clk1_sel;
	wire                                          soft_demo_hw_rst_n;
	wire                                          demo_uart_apb_rst_n_sftrstn;
	wire                                          demo_timer64_clk_ea;
	wire                                          demo_lp_mtime_clk_ea_status;
	wire                                          demo_pmu_32k_rst_n_status;
	wire                                          demo_io_apb_rst_n_sftrstn;
	wire                                          demo_drx_timer_32k_clk_ea_status;
	wire                                          demo_usim_rst_n;
	wire                                          demo_main_muxed_clk_sel_clk0_sel;
	wire                                          demo_timer_apb_clk_ea;
	wire                                          demo_rom_ahb_clk_ea;
	wire                                          demo_rom_ahb_clk_demo_rom_gat_n_sync;
	wire                                          demo_sec_ctrl2_rst_n_sftrstn;
	wire                                          demo_spi_apb_clk_ea_status;
	wire                                          demo_usim1_32k_rst_n_sftrstn;
	wire                                          demo_lp_core_clk_ea;
	wire                                          demo_pwm_core_clk_ea;
	wire                                          demo_sec_ctrl0_clk_ea_status;
	wire                                          demo_pmu_clk_ea_status;
	wire                                          demo_ocmem_ahb_clk_ea;
	wire                                          demo_wdt_clk_ea;
	wire                                          demo_hw_rst_n;
	wire                                          demo_cipher_sec_pk_clk_ea;
	wire                                          misc_ahb_clk_ea_status;
	wire                                          demo_lp_core_rst_n_sftrstn;
	wire                                          demo_pwm_core_clk_sel_clk1_sel;
	wire                                          demo_rst;
	wire                                          demo_rtc_core_clk_ea_status;
	wire                                          demo_rom_ahb_clk_ea_status;
	wire                                          demo_lp_core_demo_por_rst_n_status;
	wire                                          soc_soft_rst_n_out_status;
	wire                                          demo_drx_timer_apb_rst_n_sftrstn;
	wire                                          demo_main_muxed_clk_sel;
	wire                                          demo_io_apb_clk_ea_status;
	wire [2:0]                                    demo_cipher_sec_pkdiv2_clk_divider_status;
	wire                                          demo_sc_ref_clk_ea;
	wire                                          misc_ahb_clk_ea;
	wire                                          demo_pwm_core_rst_n_sftrstn;
	wire                                          demo_rdc_clk_ea;
	wire                                          demo_cipher_sec_pkdiv2_clk_ea;
	wire                                          demo_sc_ref_clk_ea_status;
	wire                                          clk_gen_rst_n;
	wire                                          demo_timer_cnt_clk_ea_status;
	wire                                          mdm_rst_n;
	wire                                          demo_main_muxed_occ_clk;
	wire                                          demo_i2c_core_rst_n_sftrstn;
	wire                                          demo_crg_clk_gen_rst_n;
	wire                                          demo_hw_rst_n_bf_sync;
	wire                                          demo_efuse_ctrl_demo_por_rst_n_status;
	wire                                          demo_top_pll_lock_fail;
	wire                                          demo_usim0_32k_clk_ea_status;
	wire                                          demo_sec_ctrl2_clk_ea_status;
	wire                                          rt32k_muxed0_clk_sel;
	wire                                          demo_uart_core_clk_ea;
	wire                                          demo_efuse_ctrl_ahb_clk_ea_status;
	wire                                          demo_usim0_32k_rst_n_sftrstn;
	wire                                          demo_crg_clk_gen_demo_hw_rst_n;
	wire                                          demo_usim0_apb_clk_ea;
	wire                                          demo_spi_core_clk_ea_status;
	wire                                          demo_cipher_sec_hash_clk_ea_status;
	wire                                          demo_gpio_apb_clk_ea_status;
	wire                                          demo_cipher_sec_sm4_clk_ea;
	wire                                          dtss_dt_clk_ea;
	wire                                          demo_spi_apb_rst_n_sftrstn;
	wire                                          demo_pmu_rst_n_status;
	wire                                          demo_rtc_apb_clk_ea;
	wire                                          demo_lp_core_clk_ea_status;
	wire                                          demo_cipher_sec_hash_clk_ea;
	wire                                          demo_top_pll_lock_fail_out;
	wire                                          demo_cipher_sec_pk_clk_demo_clkgat_req_sync;
	wire                                          demo_uart_apb_clk_ea;
	wire                                          demo_pwm_apb_clk_ea_status;
	wire                                          demo_usim0_apb_rst_n_sftrstn;
	wire                                          demo_usim0_apb_clk_ea_status;
	wire                                          demo_cipher_sec_pkdiv2_clk_ea_status;
	wire                                          demo_timer64_ahb_clk_ea_status;
	wire                                          demo_lp_cpu_rst_n;
	wire                                          demo_sc_apb_clk_ea;
	wire                                          demo_pmu_32k_clk_ea_status;
	wire                                          demo_timer_apb_clk_sel_clk1_sel;
	wire                                          demo_top_soc_soft_rst_n;
	wire                                          demo_cipher_sec_core_clk_ea_status;
	wire                                          demo_timer_apb_rst_n_sftrstn;
	wire                                          pmu_clk_switch_refto32K_req_sel;
	wire                                          demo_timer_cnt_rst_n_sftrstn;
	wire                                          demo_timer64_rst_n_sftrstn;
	wire                                          demo_pmu_apb_clk_ea;
	wire                                          demo_timer_cnt_clk_ea;
	wire                                          full_chip_sw_async_rst;
	wire                                          demo_spi_core_clk_ea;
	wire                                          rt32k_muxed0_clk;
	wire                                          demo_drx_timer_apb_clk_ea_status;
	wire                                          demo_wdt_apb_clk_ea_status;
	wire                                          demo_async_rst;
	wire                                          demo_pwm_core_clk_sel_clk0_sel;
	wire                                          pad_demo_por_rst_n;
	wire                                          demo_io_apb_clk_ea;
	wire                                          demo_sec_ctrl0_rst_n_sftrstn;
	wire                                          demo_cipher_sec_pk_clk_ea_status;
	wire                                          demo_pwm_apb_rst_n_sftrstn;
	wire                                          demo_wdt_rst_n_sftrstn;
	wire                                          demo_rdc_ahb_rst_n_sftrstn;
	wire                                          demo_timer64_ahb_rst_n_sftrstn;
	wire                                          demo_timer_apb_clk_sel;
	wire                                          demo_usim1_apb_rst_n_sftrstn;
	wire                                          rt32k_muxed0_clk_sel_clk1_sel;
	wire                                          full_chip_sw_rst;
	wire                                          demo_i2c_apb_clk_ea;
	wire                                          demo_wdt_apb_clk_ea;
	wire                                          demo_cipher_sec_sm4_clk_ea_status;
	wire                                          demo_rdc_rst_n_sftrstn;
	wire                                          demo_rdc_ahb_clk_ea_status;
	wire                                          demo_rtc_apb_clk_ea_status;
	wire                                          demo_usim1_32k_clk_ea_status;
	wire                                          demo_gpio_apb_clk_sel_done;
	wire                                          demo_rst_n;
	wire                                          demo_i2c_core_clk_ea_status;
	wire                                          demo_cipher_sec_hash_clk_demo_clkgat_req_sync;
	wire                                          demo_i2c_apb_clk_ea_status;
	wire                                          mdm_sys_rst_n_status;
	wire                                          demo_cipher_sec_core_clk_ea;
	wire                                          demo_sc_demo_por_rst_n_status;
	wire                                          demo_cipher_sec_core_rst_n_sftrstn;
	wire                                          demo_pwm_core_clk_sel_done;
	wire                                          demo_uart_core_clk_ea_status;
	wire                                          demo_sc_apb_rst_n_sftrstn;
	wire                                          demo_rdc_ahb_clk_ea;
	wire                                          demo_drx_timer_32k_rst_n_sftrstn;
	wire                                          demo_ref_clk_test_clk;
	wire                                          demo_timer_apb_clk_ea_status;
	wire                                          demo_spi_core_rst_n_sftrstn;
	wire                                          dtss_dt_clk_ea_status;
	wire                                          demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync;
	wire                                          demo_cipher_sec_pkdiv2_clk_divider_done;
	wire                                          demo_crg_apb_rst_n_status;
	wire                                          demo_rdc_clk_ea_status;
	wire                                          rt32k_muxed0_clk_sel_clk0_sel;
	wire                                          demo_lp_bus_rst_n_status;
	wire                                          demo_drx_timer_apb_clk_ea;
	wire                                          demo_usim1_32k_clk_ea;
	wire                                          demo_uart_apb_clk_ea_status;
	wire                                          demo_gpio_apb_clk_ea;
	wire [2:0]                                    demo_cipher_sec_pkdiv2_clk_divider;
	wire                                          demo_usim1_apb_clk_ea_status;
	wire                                          demo_ocmem_ahb_rst_n_sftrstn;
	wire                                          demo_pmu_demo_por_rst_n_status;
	wire                                          demo_pmu_clk_ea;
	wire                                          dtss_dt_rst_n_sftrstn;
	wire                                          cpuss_pll_lock_fail;
	wire                                          demo_sec_ctrl2_clk_ea;
	wire                                          demo_drx_timer_phy_rst_n_sftrstn;
	wire                                          demo_i2c_core_clk_ea;
	wire                                          demo_lp_core_clk_demo_clkgat_req_sync;
	wire                                          demo_lp_mtime_clk_ea;
	wire                                          demo_top_lp_bus_rst_n_sftrstn;
	wire                                          demo_gpio_apb_clk_sel_clk0_sel;
	wire                                          demo_efuse_ctrl_logic_rst_n_sftrstn;
	wire                                          demo_spi_apb_clk_ea;
	wire                                          rtc32k_muxed_clk;
	wire                                          demo_main_muxed_clk_sel_done;
	wire                                          demo_gpio_apb_clk_sel;
	wire                                          demo_pmu_32k_clk_ea;
	wire                                          demo_sec_ctrl0_clk_ea;
	wire                                          demo_wdt_apb_rst_n_sftrstn;
	wire                                          demo_gpio_apb_rst_n_sftrstn;
	wire                                          por_flt_n;
	wire                                          demo_sec_ctrl1_clk_ea_status;
	wire                                          demo_timer_apb_clk_sel_clk0_sel;
	wire                                          demo_cipher_sec_aes_clk_ea;
	wire                                          demo_top_soft_rst_n;
	wire                                          demo_wdt_clk_ea_status;
	wire                                          demo_sc_apb_clk_ea_status;
	wire                                          demo_cipher_sec_pkdiv2_clk_divider_ea_req;
	wire                                          demo_efuse_ctrl_ahb_clk_ea;
	wire                                          demo_lp_core_demo_por_rst_n_sftrstn;
	wire                                          demo_pmu_apb_rst_n_status;
	wire                                          demo_rtc_core_rst_n_sftrstn;
	wire                                          rt32k_muxed0_clk_sel_done;
	wire                                          demo_timer_apb_clk_sel_done;
	wire                                          demo_i2c_apb_rst_n_sftrstn;
	wire                                          demo_timer64_clk_ea_status;
	wire                                          soc_soft_rst_n;
	wire                                          demo_top_rst_n;
assign demo_hw_rst_n_bf_sync = ((demo_wdt_rst_mask | (~demo_wdt_rst)) | (~hw_por_rst_req_mode)) & soft_demo_hw_rst_n & t_sensor_ot_rst_n & (~wake_time_out_rst_pulse_req);
assign soc_async_rst_n = demo_por_rst_n&demo_soctop_rst_n&demo_hw_rst_n&demo_top_soft_rst_n;
assign demo_lp_cpu_rst_n = ((boot_mode[1:0]==2'b11)? demo_lp_cpu_rst_ijtag_ctrl : (pmu_alpwron_rdy & efuse_ctrl_por_done)) & (~n205_sysresetreq) & demo_hw_rst_n;
assign mdm_sys_rst_n = mdm_rst_n;
assign demo_usim_rst_n = mdm_rst_n&demo_top_rst_n;
assign demo_top_rst_n = demo_hw_rst_n;
assign demo_por_rst_n_out = demo_por_rst_n;
assign demo_hw_rst_n_out = demo_hw_rst_n;
assign soc_soft_rst_n_out = soc_soft_rst_n & jtag_rst_n;
assign lp_core_rst_n_out = demo_lp_core_rst_n;
assign pmu_ao_clkgat_ack = demo_lp_core_clk_demo_clkgat_req_sync;
assign pmu_clk_switch_refto32K_req_sel = pmu_clk_switch_refto32K_req;
assign pmu_clk_switch_refto32K_ack = demo_timer_apb_clk_sel_clk1_sel & demo_gpio_apb_clk_sel_clk1_sel;
assign soc_async_rst_n_status = soc_async_rst_n;
assign demo_lp_core_demo_por_rst_n_status = demo_lp_core_demo_por_rst_n;
assign demo_lp_bus_rst_n_status = demo_lp_bus_rst_n;
assign demo_efuse_ctrl_demo_por_rst_n_status = demo_efuse_ctrl_demo_por_rst_n;
assign demo_pmu_rst_n_status = demo_pmu_rst_n;
assign demo_pmu_apb_rst_n_status = demo_pmu_apb_rst_n;
assign demo_pmu_32k_rst_n_status = demo_pmu_32k_rst_n;
assign demo_pmu_demo_por_rst_n_status = demo_pmu_demo_por_rst_n;
assign demo_crg_apb_rst_n_status = demo_crg_apb_rst_n;
assign demo_sc_demo_por_rst_n_status = demo_sc_demo_por_rst_n;
assign soc_soft_rst_n_out_status = soc_soft_rst_n_out;
assign mdm_sys_rst_n_status = mdm_sys_rst_n;
assign demo_crg_clk_gen_demo_hw_rst_n = demo_crg_clk_gen_rst_n & demo_hw_rst_n;
assign demo_top_soc_soft_rst_n = demo_top_rst_n & soc_soft_rst_n_out;


// =================================================================================================
// Interface Declaration
// =================================================================================================

// =================================================================================================
// Instance
// =================================================================================================

	std_cell_clk_mux	u_demo_32k_clk_mux(
		.clk_in0                                                     (rt32k_muxed0_clk                                            ), //u_demo_32k_clk_mux.input,
		.clk_in1                                                     (dft_test_clock                                              ), //u_demo_32k_clk_mux.input,
		.clk_sel                                                     (test_mode                                                   ), //u_demo_32k_clk_mux.input,
		.clk_out                                                     (rtc32k_muxed_clk                                            ) //u_demo_32k_clk_mux.output,
	);

	ss_rst_sequence	u_ss_rst_sequence(
		.clk_in                                                      (demo_ref_clk_test_clk                                       ), //u_ss_rst_sequence.input,
		.por_sys_n                                                   (demo_por_rst_n                                              ), //u_ss_rst_sequence.input,
		.sw_rst                                                      ({2'b0,demo_async_rst}                                       ), //u_ss_rst_sequence.input,
		.test_mode                                                   (test_mode                                                   ), //u_ss_rst_sequence.input,
		.test_rstn                                                   (dft_div_rstn                                                ), //u_ss_rst_sequence.input,
		.ss_pwr_rdy                                                  (1'b1                                                        ), //u_ss_rst_sequence.input,Tie constant
		.clk_gen_rst_n                                               (demo_crg_clk_gen_rst_n                                      ), //u_ss_rst_sequence.output,
		.ss_rst_n                                                    (demo_rst_n                                                  ) //u_ss_rst_sequence.output,
	);

	rstn_test_mux	u_clk_gen_rstn_test_mux(
		.test_md                                                     (test_mode                                                   ), //u_clk_gen_rstn_test_mux.input,
		.rstn_in                                                     (demo_crg_clk_gen_demo_hw_rst_n                              ), //u_clk_gen_rstn_test_mux.input,
		.test_rstn                                                   (dft_div_rstn                                                ), //u_clk_gen_rstn_test_mux.input,
		.rstn_out                                                    (clk_gen_rst_n                                               ) //u_clk_gen_rstn_test_mux.output,
	);

	rstn_test_mux	u_por_rstn_test_mux(
		.test_md                                                     (test_mode                                                   ), //u_por_rstn_test_mux.input,
		.rstn_in                                                     (sysrstn_in                                                  ), //u_por_rstn_test_mux.input,
		.test_rstn                                                   (dft_div_rstn                                                ), //u_por_rstn_test_mux.input,
		.rstn_out                                                    (pad_demo_por_rst_n                                          ) //u_por_rstn_test_mux.output,
	);

	xstar_por_sequence	u_xstar_por_sequence(
		.clk_38p4m                                                   (demo_ref_clk_test_clk                                       ), //u_xstar_por_sequence.input,
		.demo_32k_clk                                                (rt32k_muxed1_clk                                            ), //u_xstar_por_sequence.input,
		.pad_por_n                                                   (pad_demo_por_rst_n                                          ), //u_xstar_por_sequence.input,
		.sw_rst                                                      ({2'b0,full_chip_sw_async_rst}                               ), //u_xstar_por_sequence.input,
		.test_mode                                                   (test_mode                                                   ), //u_xstar_por_sequence.input,
		.test_rstn                                                   (dft_div_rstn                                                ), //u_xstar_por_sequence.input,
		.por_flt_n                                                   (por_flt_n                                                   ), //u_xstar_por_sequence.output,
		.por_sc_n                                                    (                                                            ), //u_xstar_por_sequence.output,  Floating
		.por_sys_n                                                   (demo_por_rst_n                                              ) //u_xstar_por_sequence.output,
	);

	pulse_sync_h2s	u_demo_sw_pulse_sync(
		.src_clk                                                     (apb_clk                                                     ), //u_demo_sw_pulse_sync.input,
		.src_rst_n                                                   (apb_rst_n                                                   ), //u_demo_sw_pulse_sync.input,
		.src_pulse                                                   (demo_rst                                                    ), //u_demo_sw_pulse_sync.input,
		.dst_clk                                                     (demo_ref_clk_test_clk                                       ), //u_demo_sw_pulse_sync.input,
		.dst_rst_n                                                   (demo_por_rst_n                                              ), //u_demo_sw_pulse_sync.input,
		.dst_pulse                                                   (demo_async_rst                                              ) //u_demo_sw_pulse_sync.output,
	);

	pulse_sync_h2s	u_fc_sw_pulse_sync(
		.src_clk                                                     (apb_clk                                                     ), //u_fc_sw_pulse_sync.input,
		.src_rst_n                                                   (apb_rst_n                                                   ), //u_fc_sw_pulse_sync.input,
		.src_pulse                                                   (full_chip_sw_rst                                            ), //u_fc_sw_pulse_sync.input,
		.dst_clk                                                     (demo_ref_clk_test_clk                                       ), //u_fc_sw_pulse_sync.input,
		.dst_rst_n                                                   (por_flt_n                                                   ), //u_fc_sw_pulse_sync.input,
		.dst_pulse                                                   (full_chip_sw_async_rst                                      ) //u_fc_sw_pulse_sync.output,
	);

	sync	#(
		.D_WIDTH                                 (1),
		.DATA_DEFAULT                            (1'b1)

)
	u_demo_hw_rst_n_sync(
		.clk_d                                                       (demo_ref_clk_test_clk                                       ), //u_demo_hw_rst_n_sync.input,
		.rst_d_n                                                     (demo_por_rst_n                                              ), //u_demo_hw_rst_n_sync.input,
		.data_s                                                      (demo_hw_rst_n_bf_sync                                       ), //u_demo_hw_rst_n_sync.input,
		.data_d                                                      (demo_hw_rst_n                                               ) //u_demo_hw_rst_n_sync.output,
	);

	std_cell_clk_mux	u_rt32k_muxed1_clk_mux(
		.clk_in0                                                     (demo_32k_sko                                                ), //u_rt32k_muxed1_clk_mux.input,
		.clk_in1                                                     (demo_32k_clk                                                ), //u_rt32k_muxed1_clk_mux.input,
		.clk_sel                                                     (ao_32k_clk_sel                                              ), //u_rt32k_muxed1_clk_mux.input,
		.clk_out                                                     (rt32k_muxed1_clk                                            ) //u_rt32k_muxed1_clk_mux.output,
	);

	DEMO_CRG_apb_reg	u_DEMO_CRG_apb_reg(
		.clk                                                         (apb_clk                                                     ), //u_DEMO_CRG_apb_reg.input,
		.rst_n                                                       (apb_rst_n                                                   ), //u_DEMO_CRG_apb_reg.input,
		.psel                                                        (apb_sel                                                     ), //u_DEMO_CRG_apb_reg.input,
		.penable                                                     (apb_enable                                                  ), //u_DEMO_CRG_apb_reg.input,
		.pwrite                                                      (apb_write                                                   ), //u_DEMO_CRG_apb_reg.input,
		.paddr                                                       (apb_addr[31:0]                                              ), //u_DEMO_CRG_apb_reg.input,
		.pwdata                                                      (apb_wdata[31:0]                                             ), //u_DEMO_CRG_apb_reg.input,
		.prdata                                                      (apb_rdata[31:0]                                             ), //u_DEMO_CRG_apb_reg.output,
		.pready                                                      (apb_ready                                                   ), //u_DEMO_CRG_apb_reg.output,
		.pslverr                                                     (apb_slverr                                                  ), //u_DEMO_CRG_apb_reg.output,
		.rt32k_muxed0_clk_ctrl_rt32k_muxed0_clk_sel                  (rt32k_muxed0_clk_sel                                        ), //u_DEMO_CRG_apb_reg.output,
		.rt32k_muxed0_clk_status_rt32k_muxed0_clk_sel_clk0_sel       (rt32k_muxed0_clk_sel_clk0_sel                               ), //u_DEMO_CRG_apb_reg.input,
		.rt32k_muxed0_clk_status_rt32k_muxed0_clk_sel_clk1_sel       (rt32k_muxed0_clk_sel_clk1_sel                               ), //u_DEMO_CRG_apb_reg.input,
		.rt32k_muxed0_clk_status_rt32k_muxed0_clk_sel_done           (rt32k_muxed0_clk_sel_done                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_main_muxed_clk_ctrl_demo_main_muxed_clk_sel            (demo_main_muxed_clk_sel                                     ), //u_DEMO_CRG_apb_reg.output,
		.demo_main_muxed_clk_status_demo_main_muxed_clk_sel_clk0_sel      (demo_main_muxed_clk_sel_clk0_sel                            ), //u_DEMO_CRG_apb_reg.input,
		.demo_main_muxed_clk_status_demo_main_muxed_clk_sel_clk1_sel      (demo_main_muxed_clk_sel_clk1_sel                            ), //u_DEMO_CRG_apb_reg.input,
		.demo_main_muxed_clk_status_demo_main_muxed_clk_sel_done          (demo_main_muxed_clk_sel_done                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_core_clk_ctrl_demo_lp_core_clk_ea                   (demo_lp_core_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_lp_core_clk_status_demo_lp_core_clk_ea_status          (demo_lp_core_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_mtime_clk_ctrl_demo_lp_mtime_clk_ea                 (demo_lp_mtime_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_lp_mtime_clk_status_demo_lp_mtime_clk_ea_status        (demo_lp_mtime_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_uart_apb_clk_ctrl_demo_uart_apb_clk_ea                 (demo_uart_apb_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_uart_apb_clk_status_demo_uart_apb_clk_ea_status        (demo_uart_apb_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_uart_core_clk_ctrl_demo_uart_core_clk_ea               (demo_uart_core_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_uart_core_clk_status_demo_uart_core_clk_ea_status      (demo_uart_core_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim0_32k_clk_ctrl_demo_usim0_32k_clk_ea               (demo_usim0_32k_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim0_32k_clk_status_demo_usim0_32k_clk_ea_status      (demo_usim0_32k_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim0_apb_clk_ctrl_demo_usim0_apb_clk_ea               (demo_usim0_apb_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim0_apb_clk_status_demo_usim0_apb_clk_ea_status      (demo_usim0_apb_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_gpio_apb_clk_ctrl_demo_gpio_apb_clk_ea                 (demo_gpio_apb_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_gpio_apb_clk_ctrl_demo_gpio_apb_clk_sel                (demo_gpio_apb_clk_sel                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_gpio_apb_clk_status_demo_gpio_apb_clk_ea_status        (demo_gpio_apb_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_gpio_apb_clk_status_demo_gpio_apb_clk_sel_clk0_sel      (demo_gpio_apb_clk_sel_clk0_sel                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_gpio_apb_clk_status_demo_gpio_apb_clk_sel_clk1_sel      (demo_gpio_apb_clk_sel_clk1_sel                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_gpio_apb_clk_status_demo_gpio_apb_clk_sel_done          (demo_gpio_apb_clk_sel_done                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_i2c_core_clk_ctrl_demo_i2c_core_clk_ea                 (demo_i2c_core_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_i2c_core_clk_status_demo_i2c_core_clk_ea_status        (demo_i2c_core_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_i2c_apb_clk_ctrl_demo_i2c_apb_clk_ea                   (demo_i2c_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_i2c_apb_clk_status_demo_i2c_apb_clk_ea_status          (demo_i2c_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim1_32k_clk_ctrl_demo_usim1_32k_clk_ea               (demo_usim1_32k_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim1_32k_clk_status_demo_usim1_32k_clk_ea_status      (demo_usim1_32k_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim1_apb_clk_ctrl_demo_usim1_apb_clk_ea               (demo_usim1_apb_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim1_apb_clk_status_demo_usim1_apb_clk_ea_status      (demo_usim1_apb_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_spi_core_clk_ctrl_demo_spi_core_clk_ea                 (demo_spi_core_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_spi_core_clk_status_demo_spi_core_clk_ea_status        (demo_spi_core_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_spi_apb_clk_ctrl_demo_spi_apb_clk_ea                   (demo_spi_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_spi_apb_clk_status_demo_spi_apb_clk_ea_status          (demo_spi_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_pmu_32k_clk_ctrl_demo_pmu_32k_clk_ea                   (demo_pmu_32k_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_pmu_32k_clk_status_demo_pmu_32k_clk_ea_status          (demo_pmu_32k_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_pmu_clk_ctrl_demo_pmu_clk_ea                           (demo_pmu_clk_ea                                             ), //u_DEMO_CRG_apb_reg.output,
		.demo_pmu_clk_status_demo_pmu_clk_ea_status                  (demo_pmu_clk_ea_status                                      ), //u_DEMO_CRG_apb_reg.input,
		.demo_pmu_apb_clk_ctrl_demo_pmu_apb_clk_ea                   (demo_pmu_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_pmu_apb_clk_status_demo_pmu_apb_clk_ea_status          (demo_pmu_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_drx_timer_32k_clk_ctrl_demo_drx_timer_32k_clk_ea          (demo_drx_timer_32k_clk_ea                                   ), //u_DEMO_CRG_apb_reg.output,
		.demo_drx_timer_32k_clk_status_demo_drx_timer_32k_clk_ea_status     (demo_drx_timer_32k_clk_ea_status                            ), //u_DEMO_CRG_apb_reg.input,
		.demo_drx_timer_apb_clk_ctrl_demo_drx_timer_apb_clk_ea          (demo_drx_timer_apb_clk_ea                                   ), //u_DEMO_CRG_apb_reg.output,
		.demo_drx_timer_apb_clk_status_demo_drx_timer_apb_clk_ea_status     (demo_drx_timer_apb_clk_ea_status                            ), //u_DEMO_CRG_apb_reg.input,
		.demo_rtc_apb_clk_ctrl_demo_rtc_apb_clk_ea                   (demo_rtc_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_rtc_apb_clk_status_demo_rtc_apb_clk_ea_status          (demo_rtc_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_rtc_core_clk_ctrl_demo_rtc_core_clk_ea                 (demo_rtc_core_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_rtc_core_clk_status_demo_rtc_core_clk_ea_status        (demo_rtc_core_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_wdt_apb_clk_ctrl_demo_wdt_apb_clk_ea                   (demo_wdt_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_wdt_apb_clk_status_demo_wdt_apb_clk_ea_status          (demo_wdt_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_wdt_clk_ctrl_demo_wdt_clk_ea                           (demo_wdt_clk_ea                                             ), //u_DEMO_CRG_apb_reg.output,
		.demo_wdt_clk_status_demo_wdt_clk_ea_status                  (demo_wdt_clk_ea_status                                      ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_apb_clk_ctrl_demo_timer_apb_clk_ea               (demo_timer_apb_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer_apb_clk_ctrl_demo_timer_apb_clk_sel              (demo_timer_apb_clk_sel                                      ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer_apb_clk_status_demo_timer_apb_clk_ea_status      (demo_timer_apb_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_apb_clk_status_demo_timer_apb_clk_sel_clk0_sel      (demo_timer_apb_clk_sel_clk0_sel                             ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_apb_clk_status_demo_timer_apb_clk_sel_clk1_sel      (demo_timer_apb_clk_sel_clk1_sel                             ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_apb_clk_status_demo_timer_apb_clk_sel_done          (demo_timer_apb_clk_sel_done                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_cnt_clk_ctrl_demo_timer_cnt_clk_ea               (demo_timer_cnt_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer_cnt_clk_status_demo_timer_cnt_clk_ea_status      (demo_timer_cnt_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_sc_apb_clk_ctrl_demo_sc_apb_clk_ea                     (demo_sc_apb_clk_ea                                          ), //u_DEMO_CRG_apb_reg.output,
		.demo_sc_apb_clk_status_demo_sc_apb_clk_ea_status            (demo_sc_apb_clk_ea_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_rom_ahb_clk_ctrl_demo_rom_ahb_clk_ea                   (demo_rom_ahb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_rom_ahb_clk_status_demo_rom_ahb_clk_ea_status          (demo_rom_ahb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_rdc_ahb_clk_ctrl_demo_rdc_ahb_clk_ea                   (demo_rdc_ahb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_rdc_ahb_clk_status_demo_rdc_ahb_clk_ea_status          (demo_rdc_ahb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_rdc_clk_ctrl_demo_rdc_clk_ea                           (demo_rdc_clk_ea                                             ), //u_DEMO_CRG_apb_reg.output,
		.demo_rdc_clk_status_demo_rdc_clk_ea_status                  (demo_rdc_clk_ea_status                                      ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_core_clk_ctrl_demo_cipher_sec_core_clk_ea          (demo_cipher_sec_core_clk_ea                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_core_clk_status_demo_cipher_sec_core_clk_ea_status     (demo_cipher_sec_core_clk_ea_status                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_aes_clk_ctrl_demo_cipher_sec_aes_clk_ea          (demo_cipher_sec_aes_clk_ea                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_aes_clk_status_demo_cipher_sec_aes_clk_ea_status     (demo_cipher_sec_aes_clk_ea_status                           ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_hash_clk_ctrl_demo_cipher_sec_hash_clk_ea          (demo_cipher_sec_hash_clk_ea                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_hash_clk_status_demo_cipher_sec_hash_clk_ea_status     (demo_cipher_sec_hash_clk_ea_status                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_sm4_clk_ctrl_demo_cipher_sec_sm4_clk_ea          (demo_cipher_sec_sm4_clk_ea                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_sm4_clk_status_demo_cipher_sec_sm4_clk_ea_status     (demo_cipher_sec_sm4_clk_ea_status                           ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_pk_clk_ctrl_demo_cipher_sec_pk_clk_ea          (demo_cipher_sec_pk_clk_ea                                   ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_pk_clk_status_demo_cipher_sec_pk_clk_ea_status     (demo_cipher_sec_pk_clk_ea_status                            ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_pkdiv2_clk_ctrl_demo_cipher_sec_pkdiv2_clk_ea          (demo_cipher_sec_pkdiv2_clk_ea                               ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_pkdiv2_clk_ctrl_demo_cipher_sec_pkdiv2_clk_divider_ea_req    (demo_cipher_sec_pkdiv2_clk_divider_ea_req                   ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_pkdiv2_clk_divider_demo_cipher_sec_pkdiv2_clk_divider     (demo_cipher_sec_pkdiv2_clk_divider[2:0]                     ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_pkdiv2_clk_status_demo_cipher_sec_pkdiv2_clk_ea_status     (demo_cipher_sec_pkdiv2_clk_ea_status                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_pkdiv2_clk_status_demo_cipher_sec_pkdiv2_clk_divider_status    (demo_cipher_sec_pkdiv2_clk_divider_status[2:0]              ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_pkdiv2_clk_status_demo_cipher_sec_pkdiv2_clk_divider_done      (demo_cipher_sec_pkdiv2_clk_divider_done                     ), //u_DEMO_CRG_apb_reg.input,
		.demo_efuse_ctrl_ahb_clk_ctrl_demo_efuse_ctrl_ahb_clk_ea          (demo_efuse_ctrl_ahb_clk_ea                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_efuse_ctrl_ahb_clk_status_demo_efuse_ctrl_ahb_clk_ea_status     (demo_efuse_ctrl_ahb_clk_ea_status                           ), //u_DEMO_CRG_apb_reg.input,
		.demo_sec_ctrl0_clk_ctrl_demo_sec_ctrl0_clk_ea               (demo_sec_ctrl0_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_sec_ctrl0_clk_status_demo_sec_ctrl0_clk_ea_status      (demo_sec_ctrl0_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_sec_ctrl1_clk_ctrl_demo_sec_ctrl1_clk_ea               (demo_sec_ctrl1_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_sec_ctrl1_clk_status_demo_sec_ctrl1_clk_ea_status      (demo_sec_ctrl1_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_sec_ctrl2_clk_ctrl_demo_sec_ctrl2_clk_ea               (demo_sec_ctrl2_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_sec_ctrl2_clk_status_demo_sec_ctrl2_clk_ea_status      (demo_sec_ctrl2_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_io_apb_clk_ctrl_demo_io_apb_clk_ea                     (demo_io_apb_clk_ea                                          ), //u_DEMO_CRG_apb_reg.output,
		.demo_io_apb_clk_status_demo_io_apb_clk_ea_status            (demo_io_apb_clk_ea_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.misc_ahb_clk_ctrl_misc_ahb_clk_ea                           (misc_ahb_clk_ea                                             ), //u_DEMO_CRG_apb_reg.output,
		.misc_ahb_clk_status_misc_ahb_clk_ea_status                  (misc_ahb_clk_ea_status                                      ), //u_DEMO_CRG_apb_reg.input,
		.dtss_dt_clk_ctrl_dtss_dt_clk_ea                             (dtss_dt_clk_ea                                              ), //u_DEMO_CRG_apb_reg.output,
		.dtss_dt_clk_status_dtss_dt_clk_ea_status                    (dtss_dt_clk_ea_status                                       ), //u_DEMO_CRG_apb_reg.input,
		.demo_ocmem_ahb_clk_ctrl_demo_ocmem_ahb_clk_ea               (demo_ocmem_ahb_clk_ea                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_ocmem_ahb_clk_status_demo_ocmem_ahb_clk_ea_status      (demo_ocmem_ahb_clk_ea_status                                ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer64_ahb_clk_ctrl_demo_timer64_ahb_clk_ea           (demo_timer64_ahb_clk_ea                                     ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer64_ahb_clk_status_demo_timer64_ahb_clk_ea_status     (demo_timer64_ahb_clk_ea_status                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer64_clk_ctrl_demo_timer64_clk_ea                   (demo_timer64_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer64_clk_status_demo_timer64_clk_ea_status          (demo_timer64_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_apb_clk_ctrl_demo_pwm_apb_clk_ea                   (demo_pwm_apb_clk_ea                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_pwm_apb_clk_status_demo_pwm_apb_clk_ea_status          (demo_pwm_apb_clk_ea_status                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_core_clk_ctrl_demo_pwm_core_clk_ea                 (demo_pwm_core_clk_ea                                        ), //u_DEMO_CRG_apb_reg.output,
		.demo_pwm_core_clk_ctrl_demo_pwm_core_clk_sel                (demo_pwm_core_clk_sel                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_pwm_core_clk_status_demo_pwm_core_clk_ea_status        (demo_pwm_core_clk_ea_status                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_core_clk_status_demo_pwm_core_clk_sel_clk0_sel      (demo_pwm_core_clk_sel_clk0_sel                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_core_clk_status_demo_pwm_core_clk_sel_clk1_sel      (demo_pwm_core_clk_sel_clk1_sel                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_core_clk_status_demo_pwm_core_clk_sel_done          (demo_pwm_core_clk_sel_done                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_sc_ref_clk_ctrl_demo_sc_ref_clk_ea                     (demo_sc_ref_clk_ea                                          ), //u_DEMO_CRG_apb_reg.output,
		.demo_sc_ref_clk_status_demo_sc_ref_clk_ea_status            (demo_sc_ref_clk_ea_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_core_rst_ctrl_demo_lp_core_rst_n_sftrstn            (demo_lp_core_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_lp_core_rst_ctrl_demo_lp_core_demo_por_rst_n_sftrstn      (demo_lp_core_demo_por_rst_n_sftrstn                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_uart_rst_ctrl_demo_uart_apb_rst_n_sftrstn              (demo_uart_apb_rst_n_sftrstn                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim0_rst_ctrl_demo_usim0_32k_rst_n_sftrstn            (demo_usim0_32k_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_gpio_rst_ctrl_demo_gpio_apb_rst_n_sftrstn              (demo_gpio_apb_rst_n_sftrstn                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_i2c0_rst_ctrl_demo_i2c_core_rst_n_sftrstn              (demo_i2c_core_rst_n_sftrstn                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_usim1_rst_ctrl_demo_usim1_32k_rst_n_sftrstn            (demo_usim1_32k_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_spi_rst_ctrl_demo_spi_core_rst_n_sftrstn               (demo_spi_core_rst_n_sftrstn                                 ), //u_DEMO_CRG_apb_reg.output,
		.demo_drx_timer_rst_ctrl_demo_drx_timer_32k_rst_n_sftrstn      (demo_drx_timer_32k_rst_n_sftrstn                            ), //u_DEMO_CRG_apb_reg.output,
		.demo_rtc_rst_ctrl_demo_rtc_apb_rst_n_sftrstn                (demo_rtc_apb_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_wdt_rst_ctrl_demo_wdt_apb_rst_n_sftrstn                (demo_wdt_apb_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer0_rst_ctrl_demo_timer_apb_rst_n_sftrstn           (demo_timer_apb_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_sc_rst_ctrl_demo_sc_apb_rst_n_sftrstn                  (demo_sc_apb_rst_n_sftrstn                                   ), //u_DEMO_CRG_apb_reg.output,
		.demo_rom_ahb_rst_ctrl_demo_rom_ahb_rst_n_sftrstn            (demo_rom_ahb_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_rdc_ahb_rst_ctrl_demo_rdc_ahb_rst_n_sftrstn            (demo_rdc_ahb_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_rdc_rst_ctrl_demo_rdc_rst_n_sftrstn                    (demo_rdc_rst_n_sftrstn                                      ), //u_DEMO_CRG_apb_reg.output,
		.demo_cipher_sec_core_rst_ctrl_demo_cipher_sec_core_rst_n_sftrstn      (demo_cipher_sec_core_rst_n_sftrstn                          ), //u_DEMO_CRG_apb_reg.output,
		.demo_efuse_ctrl_rst_ctrl_demo_efuse_ctrl_logic_rst_n_sftrstn      (demo_efuse_ctrl_logic_rst_n_sftrstn                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_sec_ctrl0_rst_ctrl_demo_sec_ctrl0_rst_n_sftrstn        (demo_sec_ctrl0_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_io_rst_ctrl_demo_io_apb_rst_n_sftrstn                  (demo_io_apb_rst_n_sftrstn                                   ), //u_DEMO_CRG_apb_reg.output,
		.misc_ahb_rst_ctrl_misc_ahb_rst_n_sftrstn                    (misc_ahb_rst_n_sftrstn                                      ), //u_DEMO_CRG_apb_reg.output,
		.dtss_dt_rst_ctrl_dtss_dt_rst_n_sftrstn                      (dtss_dt_rst_n_sftrstn                                       ), //u_DEMO_CRG_apb_reg.output,
		.demo_ocmem_ahb_rst_ctrl_demo_ocmem_ahb_rst_n_sftrstn        (demo_ocmem_ahb_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer64_rst_ctrl_demo_timer64_ahb_rst_n_sftrstn        (demo_timer64_ahb_rst_n_sftrstn                              ), //u_DEMO_CRG_apb_reg.output,
		.demo_pwm_rst_ctrl_demo_pwm_apb_rst_n_sftrstn                (demo_pwm_apb_rst_n_sftrstn                                  ), //u_DEMO_CRG_apb_reg.output,
		.demo_timer_cnt_rst_ctrl_demo_timer_cnt_rst_n_sftrstn        (demo_timer_cnt_rst_n_sftrstn                                ), //u_DEMO_CRG_apb_reg.output,
		.demo_lp_bus_rst_ctrl_demo_top_lp_bus_rst_n_sftrstn          (demo_top_lp_bus_rst_n_sftrstn                               ), //u_DEMO_CRG_apb_reg.output,
		.demo_lp_core_rst_ctrl_status_demo_lp_core_rst_n_status      (demo_lp_core_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_core_rst_ctrl_status_demo_lp_core_demo_por_rst_n_status      (demo_lp_core_demo_por_rst_n                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_uart_rst_ctrl_status_demo_uart_apb_rst_n_status        (demo_uart_apb_rst_n                                         ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim0_rst_ctrl_status_demo_usim0_32k_rst_n_status      (demo_usim0_32k_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_gpio_rst_ctrl_status_demo_gpio_apb_rst_n_status        (demo_gpio_apb_rst_n                                         ), //u_DEMO_CRG_apb_reg.input,
		.demo_i2c0_rst_ctrl_status_demo_i2c_core_rst_n_status        (demo_i2c_core_rst_n                                         ), //u_DEMO_CRG_apb_reg.input,
		.demo_usim1_rst_ctrl_status_demo_usim1_32k_rst_n_status      (demo_usim1_32k_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_spi_rst_ctrl_status_demo_spi_core_rst_n_status         (demo_spi_core_rst_n                                         ), //u_DEMO_CRG_apb_reg.input,
		.demo_drx_timer_rst_ctrl_status_demo_drx_timer_32k_rst_n_status      (demo_drx_timer_32k_rst_n                                    ), //u_DEMO_CRG_apb_reg.input,
		.demo_rtc_rst_ctrl_status_demo_rtc_apb_rst_n_status          (demo_rtc_apb_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_wdt_rst_ctrl_status_demo_wdt_apb_rst_n_status          (demo_wdt_apb_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer0_rst_ctrl_status_demo_timer_apb_rst_n_status      (demo_timer_apb_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_sc_rst_ctrl_status_demo_sc_apb_rst_n_status            (demo_sc_apb_rst_n                                           ), //u_DEMO_CRG_apb_reg.input,
		.demo_rom_ahb_rst_ctrl_status_demo_rom_ahb_rst_n_status      (demo_rom_ahb_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_rdc_ahb_rst_ctrl_status_demo_rdc_ahb_rst_n_status      (demo_rdc_ahb_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_rdc_rst_ctrl_status_demo_rdc_rst_n_status              (demo_rdc_rst_n                                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_cipher_sec_core_rst_ctrl_status_demo_cipher_sec_core_rst_n_status      (demo_cipher_sec_core_rst_n                                  ), //u_DEMO_CRG_apb_reg.input,
		.demo_efuse_ctrl_rst_ctrl_status_demo_efuse_ctrl_logic_rst_n_status      (demo_efuse_ctrl_logic_rst_n                                 ), //u_DEMO_CRG_apb_reg.input,
		.demo_sec_ctrl0_rst_ctrl_status_demo_sec_ctrl0_rst_n_status      (demo_sec_ctrl0_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_io_rst_ctrl_status_demo_io_apb_rst_n_status            (demo_io_apb_rst_n                                           ), //u_DEMO_CRG_apb_reg.input,
		.misc_ahb_rst_ctrl_status_misc_ahb_rst_n_status              (misc_ahb_rst_n                                              ), //u_DEMO_CRG_apb_reg.input,
		.dtss_dt_rst_ctrl_status_dtss_dt_rst_n_status                (dtss_dt_rst_n                                               ), //u_DEMO_CRG_apb_reg.input,
		.demo_ocmem_ahb_rst_ctrl_status_demo_ocmem_ahb_rst_n_status      (demo_ocmem_ahb_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer64_rst_ctrl_status_demo_timer64_ahb_rst_n_status      (demo_timer64_ahb_rst_n                                      ), //u_DEMO_CRG_apb_reg.input,
		.demo_pwm_rst_ctrl_status_demo_pwm_apb_rst_n_status          (demo_pwm_apb_rst_n                                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_timer_cnt_rst_ctrl_status_demo_timer_cnt_rst_n_status      (demo_timer_cnt_rst_n                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_bus_rst_ctrl_status_demo_top_lp_bus_rst_n_status      (demo_top_lp_bus_rst_n                                       ), //u_DEMO_CRG_apb_reg.input,
		.demo_rst_demo_rst                                           (demo_rst                                                    ), //u_DEMO_CRG_apb_reg.output,
		.soft_sw_soc_rst_n_soc_soft_rst_n                            (soc_soft_rst_n                                              ), //u_DEMO_CRG_apb_reg.output,
		.mdm_rst_ctrl_mdm_rst_n                                      (mdm_rst_n                                                   ), //u_DEMO_CRG_apb_reg.output,
		.full_chip_rst_ctrl_full_chip_sw_rst                         (full_chip_sw_rst                                            ), //u_DEMO_CRG_apb_reg.output,
		.soft_hw_rst_ctrl_soft_demo_hw_rst_n                         (soft_demo_hw_rst_n                                          ), //u_DEMO_CRG_apb_reg.output,
		.demo_top_soc_rst_ctrl_demo_top_soft_rst_n                   (demo_top_soft_rst_n                                         ), //u_DEMO_CRG_apb_reg.output,
		.demo_crg_rst_n_status_soc_async_rst_n_status                (soc_async_rst_n_status                                      ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_lp_core_demo_por_rst_n_status     (demo_lp_core_demo_por_rst_n_status                          ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_lp_bus_rst_n_status              (demo_lp_bus_rst_n_status                                    ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_efuse_ctrl_demo_por_rst_n_status     (demo_efuse_ctrl_demo_por_rst_n_status                       ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_pmu_rst_n_status                 (demo_pmu_rst_n_status                                       ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_pmu_apb_rst_n_status             (demo_pmu_apb_rst_n_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_pmu_32k_rst_n_status             (demo_pmu_32k_rst_n_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_pmu_demo_por_rst_n_status        (demo_pmu_demo_por_rst_n_status                              ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_crg_apb_rst_n_status             (demo_crg_apb_rst_n_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_demo_sc_demo_por_rst_n_status         (demo_sc_demo_por_rst_n_status                               ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_soc_soft_rst_n_out_status             (soc_soft_rst_n_out_status                                   ), //u_DEMO_CRG_apb_reg.input,
		.demo_crg_rst_n_status_mdm_sys_rst_n_status                  (mdm_sys_rst_n_status                                        ), //u_DEMO_CRG_apb_reg.input,
		.demo_lp_cpu_rst_ijtag_ctrl_demo_lp_cpu_rst_ijtag_ctrl       (demo_lp_cpu_rst_ijtag_ctrl                                  ), //u_DEMO_CRG_apb_reg.output,
		.cpuss_pll_lock_fail_out                                     (cpuss_pll_lock_fail_out                                     ), //u_DEMO_CRG_apb_reg.output,    noload
		.cpuss_pll_lock_fail_cpuss_pll_lock_fail                     (cpuss_pll_lock_fail                                         ), //u_DEMO_CRG_apb_reg.input,undrive --- fixme
		.demo_top_pll_lock_fail_out                                  (demo_top_pll_lock_fail_out                                  ), //u_DEMO_CRG_apb_reg.output,    noload
		.demo_top_pll_lock_fail_demo_top_pll_lock_fail               (demo_top_pll_lock_fail                                      ) //u_DEMO_CRG_apb_reg.input,undrive --- fixme
	);

	demo_crg_clk_gen	u_demo_crg_clk_gen(
		.apb_clk                                                     (apb_clk                                                     ), //u_demo_crg_clk_gen.input,
		.apb_rst_n                                                   (apb_rst_n                                                   ), //u_demo_crg_clk_gen.input,
		.dft_icg_mode_root                                           (dft_icg_mode_root                                           ), //u_demo_crg_clk_gen.input,
		.test_mode                                                   (test_mode                                                   ), //u_demo_crg_clk_gen.input,
		.demo_main_clk                                               (demo_main_clk                                               ), //u_demo_crg_clk_gen.input,
		.clk_gen_rst_n                                               (clk_gen_rst_n                                               ), //u_demo_crg_clk_gen.input,
		.demo_ref_clk                                                (demo_ref_clk                                                ), //u_demo_crg_clk_gen.input,
		.rtc32k_muxed_clk                                            (rtc32k_muxed_clk                                            ), //u_demo_crg_clk_gen.input,
		.demo_32k_clk                                                (demo_32k_clk                                                ), //u_demo_crg_clk_gen.input,
		.demo_32k_sko                                                (demo_32k_sko                                                ), //u_demo_crg_clk_gen.input,
		.rt32k_muxed1_clk                                            (rt32k_muxed1_clk                                            ), //u_demo_crg_clk_gen.input,
		.demo_bb_clk                                                 (demo_bb_clk                                                 ), //u_demo_crg_clk_gen.input,
		.rt32k_muxed0_clk_sel                                        (rt32k_muxed0_clk_sel                                        ), //u_demo_crg_clk_gen.input,
		.rt32k_muxed0_clk_sel_clk0_sel                               (rt32k_muxed0_clk_sel_clk0_sel                               ), //u_demo_crg_clk_gen.output,
		.rt32k_muxed0_clk_sel_clk1_sel                               (rt32k_muxed0_clk_sel_clk1_sel                               ), //u_demo_crg_clk_gen.output,
		.rt32k_muxed0_clk_sel_done                                   (rt32k_muxed0_clk_sel_done                                   ), //u_demo_crg_clk_gen.output,
		.rt32k_muxed0_clk                                            (rt32k_muxed0_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_ref_clk_test_clk                                       (demo_ref_clk_test_clk                                       ), //u_demo_crg_clk_gen.output,
		.demo_main_muxed_clk_sel                                     (demo_main_muxed_clk_sel                                     ), //u_demo_crg_clk_gen.input,
		.demo_main_muxed_clk_sel_clk0_sel                            (demo_main_muxed_clk_sel_clk0_sel                            ), //u_demo_crg_clk_gen.output,
		.demo_main_muxed_clk_sel_clk1_sel                            (demo_main_muxed_clk_sel_clk1_sel                            ), //u_demo_crg_clk_gen.output,
		.demo_main_muxed_clk_sel_done                                (demo_main_muxed_clk_sel_done                                ), //u_demo_crg_clk_gen.output,
		.demo_main_muxed_occ_clk                                     (demo_main_muxed_occ_clk                                     ), //u_demo_crg_clk_gen.output,    noload
		.demo_lp_core_clk_ea                                         (demo_lp_core_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_lp_core_clk_ea_status                                  (demo_lp_core_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_clkgat_req                                             (demo_clkgat_req                                             ), //u_demo_crg_clk_gen.input,
		.demo_lp_core_clk_demo_clkgat_req_sync                       (demo_lp_core_clk_demo_clkgat_req_sync                       ), //u_demo_crg_clk_gen.output,
		.demo_lp_core_clk                                            (demo_lp_core_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_lp_mtime_clk_ea                                        (demo_lp_mtime_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_lp_mtime_clk_ea_status                                 (demo_lp_mtime_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_lp_mtime_clk_demo_clkgat_req_sync                      (demo_lp_mtime_clk_demo_clkgat_req_sync                      ), //u_demo_crg_clk_gen.output,    noload
		.demo_lp_mtime_clk                                           (demo_lp_mtime_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_uart_apb_clk_ea                                        (demo_uart_apb_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_uart_apb_clk_ea_status                                 (demo_uart_apb_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_uart_apb_clk                                           (demo_uart_apb_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_uart_core_clk_ea                                       (demo_uart_core_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_uart_core_clk_ea_status                                (demo_uart_core_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_uart_core_clk                                          (demo_uart_core_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_usim0_32k_clk_ea                                       (demo_usim0_32k_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_usim0_32k_clk_ea_status                                (demo_usim0_32k_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_usim0_32k_clk                                          (demo_usim0_32k_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_usim0_apb_clk_ea                                       (demo_usim0_apb_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_usim0_apb_clk_ea_status                                (demo_usim0_apb_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_usim0_apb_clk                                          (demo_usim0_apb_clk                                          ), //u_demo_crg_clk_gen.output,
		.pmu_clk_switch_refto32K_req_sel                             (pmu_clk_switch_refto32K_req_sel                             ), //u_demo_crg_clk_gen.input,
		.demo_gpio_apb_clk_sel                                       (demo_gpio_apb_clk_sel                                       ), //u_demo_crg_clk_gen.input,
		.demo_gpio_apb_clk_sel_clk0_sel                              (demo_gpio_apb_clk_sel_clk0_sel                              ), //u_demo_crg_clk_gen.output,
		.demo_gpio_apb_clk_sel_clk1_sel                              (demo_gpio_apb_clk_sel_clk1_sel                              ), //u_demo_crg_clk_gen.output,
		.demo_gpio_apb_clk_sel_done                                  (demo_gpio_apb_clk_sel_done                                  ), //u_demo_crg_clk_gen.output,
		.demo_gpio_apb_clk_ea                                        (demo_gpio_apb_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_gpio_apb_clk_ea_status                                 (demo_gpio_apb_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_gpio_apb_clk                                           (demo_gpio_apb_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_i2c_core_clk_ea                                        (demo_i2c_core_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_i2c_core_clk_ea_status                                 (demo_i2c_core_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_i2c_core_clk                                           (demo_i2c_core_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_i2c_apb_clk_ea                                         (demo_i2c_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_i2c_apb_clk_ea_status                                  (demo_i2c_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_i2c_apb_clk                                            (demo_i2c_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_usim1_32k_clk_ea                                       (demo_usim1_32k_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_usim1_32k_clk_ea_status                                (demo_usim1_32k_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_usim1_32k_clk                                          (demo_usim1_32k_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_usim1_apb_clk_ea                                       (demo_usim1_apb_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_usim1_apb_clk_ea_status                                (demo_usim1_apb_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_usim1_apb_clk                                          (demo_usim1_apb_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_spi_core_clk_ea                                        (demo_spi_core_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_spi_core_clk_ea_status                                 (demo_spi_core_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_spi_core_clk                                           (demo_spi_core_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_spi_apb_clk_ea                                         (demo_spi_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_spi_apb_clk_ea_status                                  (demo_spi_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_spi_apb_clk                                            (demo_spi_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_pmu_32k_clk_ea                                         (demo_pmu_32k_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_pmu_32k_clk_ea_status                                  (demo_pmu_32k_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_pmu_32k_clk                                            (demo_pmu_32k_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_pmu_clk_ea                                             (demo_pmu_clk_ea                                             ), //u_demo_crg_clk_gen.input,
		.demo_pmu_clk_ea_status                                      (demo_pmu_clk_ea_status                                      ), //u_demo_crg_clk_gen.output,
		.demo_pmu_clk                                                (demo_pmu_clk                                                ), //u_demo_crg_clk_gen.output,
		.demo_pmu_apb_clk_ea                                         (demo_pmu_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_pmu_apb_clk_ea_status                                  (demo_pmu_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_pmu_apb_clk                                            (demo_pmu_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_crg_apb_clk                                            (demo_crg_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_drx_timer_32k_clk_ea                                   (demo_drx_timer_32k_clk_ea                                   ), //u_demo_crg_clk_gen.input,
		.demo_drx_timer_32k_clk_ea_status                            (demo_drx_timer_32k_clk_ea_status                            ), //u_demo_crg_clk_gen.output,
		.demo_drx_timer_32k_clk                                      (demo_drx_timer_32k_clk                                      ), //u_demo_crg_clk_gen.output,
		.demo_drx_timer_phy_clk                                      (demo_drx_timer_phy_clk                                      ), //u_demo_crg_clk_gen.output,
		.demo_drx_timer_apb_clk_ea                                   (demo_drx_timer_apb_clk_ea                                   ), //u_demo_crg_clk_gen.input,
		.demo_drx_timer_apb_clk_ea_status                            (demo_drx_timer_apb_clk_ea_status                            ), //u_demo_crg_clk_gen.output,
		.demo_drx_timer_apb_clk                                      (demo_drx_timer_apb_clk                                      ), //u_demo_crg_clk_gen.output,
		.demo_rtc_apb_clk_ea                                         (demo_rtc_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_rtc_apb_clk_ea_status                                  (demo_rtc_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_rtc_apb_clk                                            (demo_rtc_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_rtc_core_clk_ea                                        (demo_rtc_core_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_rtc_core_clk_ea_status                                 (demo_rtc_core_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_rtc_core_clk                                           (demo_rtc_core_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_wdt_apb_clk_ea                                         (demo_wdt_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_wdt_apb_clk_ea_status                                  (demo_wdt_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_wdt_apb_clk                                            (demo_wdt_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_wdt_clk_ea                                             (demo_wdt_clk_ea                                             ), //u_demo_crg_clk_gen.input,
		.demo_wdt_clk_ea_status                                      (demo_wdt_clk_ea_status                                      ), //u_demo_crg_clk_gen.output,
		.demo_wdt_clk                                                (demo_wdt_clk                                                ), //u_demo_crg_clk_gen.output,
		.demo_timer_apb_clk_sel                                      (demo_timer_apb_clk_sel                                      ), //u_demo_crg_clk_gen.input,
		.demo_timer_apb_clk_sel_clk0_sel                             (demo_timer_apb_clk_sel_clk0_sel                             ), //u_demo_crg_clk_gen.output,
		.demo_timer_apb_clk_sel_clk1_sel                             (demo_timer_apb_clk_sel_clk1_sel                             ), //u_demo_crg_clk_gen.output,
		.demo_timer_apb_clk_sel_done                                 (demo_timer_apb_clk_sel_done                                 ), //u_demo_crg_clk_gen.output,
		.demo_timer_apb_clk_ea                                       (demo_timer_apb_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_timer_apb_clk_ea_status                                (demo_timer_apb_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_timer_apb_clk                                          (demo_timer_apb_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_timer_cnt_clk_ea                                       (demo_timer_cnt_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_timer_cnt_clk_ea_status                                (demo_timer_cnt_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_timer_cnt_clk                                          (demo_timer_cnt_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_sc_apb_clk_ea                                          (demo_sc_apb_clk_ea                                          ), //u_demo_crg_clk_gen.input,
		.demo_sc_apb_clk_ea_status                                   (demo_sc_apb_clk_ea_status                                   ), //u_demo_crg_clk_gen.output,
		.demo_sc_apb_clk                                             (demo_sc_apb_clk                                             ), //u_demo_crg_clk_gen.output,
		.demo_rom_ahb_clk_ea                                         (demo_rom_ahb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_rom_ahb_clk_ea_status                                  (demo_rom_ahb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_rom_gat_n                                              (demo_rom_gat_n                                              ), //u_demo_crg_clk_gen.input,
		.demo_rom_ahb_clk_demo_rom_gat_n_sync                        (demo_rom_ahb_clk_demo_rom_gat_n_sync                        ), //u_demo_crg_clk_gen.output,    noload
		.demo_rom_ahb_clk                                            (demo_rom_ahb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_rdc_ahb_clk_ea                                         (demo_rdc_ahb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_rdc_ahb_clk_ea_status                                  (demo_rdc_ahb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_rdc_ahb_clk                                            (demo_rdc_ahb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_rdc_clk_ea                                             (demo_rdc_clk_ea                                             ), //u_demo_crg_clk_gen.input,
		.demo_rdc_clk_ea_status                                      (demo_rdc_clk_ea_status                                      ), //u_demo_crg_clk_gen.output,
		.demo_rdc_clk                                                (demo_rdc_clk                                                ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_core_clk_ea                                 (demo_cipher_sec_core_clk_ea                                 ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_core_clk_ea_status                          (demo_cipher_sec_core_clk_ea_status                          ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_core_clk_demo_clkgat_req_sync               (demo_cipher_sec_core_clk_demo_clkgat_req_sync               ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_core_clk                                    (demo_cipher_sec_core_clk                                    ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_aes_clk_ea                                  (demo_cipher_sec_aes_clk_ea                                  ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_aes_clk_ea_status                           (demo_cipher_sec_aes_clk_ea_status                           ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_aes_clk_demo_clkgat_req_sync                (demo_cipher_sec_aes_clk_demo_clkgat_req_sync                ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_aes_clk                                     (demo_cipher_sec_aes_clk                                     ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_hash_clk_ea                                 (demo_cipher_sec_hash_clk_ea                                 ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_hash_clk_ea_status                          (demo_cipher_sec_hash_clk_ea_status                          ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_hash_clk_demo_clkgat_req_sync               (demo_cipher_sec_hash_clk_demo_clkgat_req_sync               ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_hash_clk                                    (demo_cipher_sec_hash_clk                                    ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_sm4_clk_ea                                  (demo_cipher_sec_sm4_clk_ea                                  ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_sm4_clk_ea_status                           (demo_cipher_sec_sm4_clk_ea_status                           ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_sm4_clk_demo_clkgat_req_sync                (demo_cipher_sec_sm4_clk_demo_clkgat_req_sync                ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_sm4_clk                                     (demo_cipher_sec_sm4_clk                                     ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pk_clk_ea                                   (demo_cipher_sec_pk_clk_ea                                   ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_pk_clk_ea_status                            (demo_cipher_sec_pk_clk_ea_status                            ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pk_clk_demo_clkgat_req_sync                 (demo_cipher_sec_pk_clk_demo_clkgat_req_sync                 ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_pk_clk                                      (demo_cipher_sec_pk_clk                                      ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pkdiv2_clk_divider                          (demo_cipher_sec_pkdiv2_clk_divider[2:0]                     ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_pkdiv2_clk_divider_ea_req                   (demo_cipher_sec_pkdiv2_clk_divider_ea_req                   ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_pkdiv2_clk_divider_status                   (demo_cipher_sec_pkdiv2_clk_divider_status[2:0]              ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pkdiv2_clk_divider_done                     (demo_cipher_sec_pkdiv2_clk_divider_done                     ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pkdiv2_clk_ea                               (demo_cipher_sec_pkdiv2_clk_ea                               ), //u_demo_crg_clk_gen.input,
		.demo_cipher_sec_pkdiv2_clk_ea_status                        (demo_cipher_sec_pkdiv2_clk_ea_status                        ), //u_demo_crg_clk_gen.output,
		.demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync             (demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync             ), //u_demo_crg_clk_gen.output,    noload
		.demo_cipher_sec_pkdiv2_clk                                  (demo_cipher_sec_pkdiv2_clk                                  ), //u_demo_crg_clk_gen.output,
		.demo_efuse_ctrl_ahb_clk_ea                                  (demo_efuse_ctrl_ahb_clk_ea                                  ), //u_demo_crg_clk_gen.input,
		.demo_efuse_ctrl_ahb_clk_ea_status                           (demo_efuse_ctrl_ahb_clk_ea_status                           ), //u_demo_crg_clk_gen.output,
		.demo_efuse_ctrl_ahb_clk                                     (demo_efuse_ctrl_ahb_clk                                     ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl0_clk_ea                                       (demo_sec_ctrl0_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_sec_ctrl0_clk_ea_status                                (demo_sec_ctrl0_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl0_clk                                          (demo_sec_ctrl0_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl1_clk_ea                                       (demo_sec_ctrl1_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_sec_ctrl1_clk_ea_status                                (demo_sec_ctrl1_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl1_clk                                          (demo_sec_ctrl1_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl2_clk_ea                                       (demo_sec_ctrl2_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_sec_ctrl2_clk_ea_status                                (demo_sec_ctrl2_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_sec_ctrl2_clk                                          (demo_sec_ctrl2_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_io_apb_clk_ea                                          (demo_io_apb_clk_ea                                          ), //u_demo_crg_clk_gen.input,
		.demo_io_apb_clk_ea_status                                   (demo_io_apb_clk_ea_status                                   ), //u_demo_crg_clk_gen.output,
		.demo_io_apb_clk                                             (demo_io_apb_clk                                             ), //u_demo_crg_clk_gen.output,
		.demo_lp_bus_clk                                             (demo_lp_bus_clk                                             ), //u_demo_crg_clk_gen.output,
		.soc_32k_clk                                                 (soc_32k_clk                                                 ), //u_demo_crg_clk_gen.output,
		.misc_ahb_clk_ea                                             (misc_ahb_clk_ea                                             ), //u_demo_crg_clk_gen.input,
		.misc_ahb_clk_ea_status                                      (misc_ahb_clk_ea_status                                      ), //u_demo_crg_clk_gen.output,
		.misc_ahb_clk                                                (misc_ahb_clk                                                ), //u_demo_crg_clk_gen.output,
		.dtss_dt_clk_ea                                              (dtss_dt_clk_ea                                              ), //u_demo_crg_clk_gen.input,
		.dtss_dt_clk_ea_status                                       (dtss_dt_clk_ea_status                                       ), //u_demo_crg_clk_gen.output,
		.dtss_dt_clk                                                 (dtss_dt_clk                                                 ), //u_demo_crg_clk_gen.output,
		.demo_ocmem_ahb_clk_ea                                       (demo_ocmem_ahb_clk_ea                                       ), //u_demo_crg_clk_gen.input,
		.demo_ocmem_ahb_clk_ea_status                                (demo_ocmem_ahb_clk_ea_status                                ), //u_demo_crg_clk_gen.output,
		.demo_ocmem_ahb_clk                                          (demo_ocmem_ahb_clk                                          ), //u_demo_crg_clk_gen.output,
		.demo_timer64_ahb_clk_ea                                     (demo_timer64_ahb_clk_ea                                     ), //u_demo_crg_clk_gen.input,
		.demo_timer64_ahb_clk_ea_status                              (demo_timer64_ahb_clk_ea_status                              ), //u_demo_crg_clk_gen.output,
		.demo_timer64_ahb_clk                                        (demo_timer64_ahb_clk                                        ), //u_demo_crg_clk_gen.output,
		.demo_timer64_clk_ea                                         (demo_timer64_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_timer64_clk_ea_status                                  (demo_timer64_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_timer64_clk                                            (demo_timer64_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_pwm_apb_clk_ea                                         (demo_pwm_apb_clk_ea                                         ), //u_demo_crg_clk_gen.input,
		.demo_pwm_apb_clk_ea_status                                  (demo_pwm_apb_clk_ea_status                                  ), //u_demo_crg_clk_gen.output,
		.demo_pwm_apb_clk                                            (demo_pwm_apb_clk                                            ), //u_demo_crg_clk_gen.output,
		.demo_pwm_core_clk_sel                                       (demo_pwm_core_clk_sel                                       ), //u_demo_crg_clk_gen.input,
		.demo_pwm_core_clk_sel_clk0_sel                              (demo_pwm_core_clk_sel_clk0_sel                              ), //u_demo_crg_clk_gen.output,
		.demo_pwm_core_clk_sel_clk1_sel                              (demo_pwm_core_clk_sel_clk1_sel                              ), //u_demo_crg_clk_gen.output,
		.demo_pwm_core_clk_sel_done                                  (demo_pwm_core_clk_sel_done                                  ), //u_demo_crg_clk_gen.output,
		.demo_pwm_core_clk_ea                                        (demo_pwm_core_clk_ea                                        ), //u_demo_crg_clk_gen.input,
		.demo_pwm_core_clk_ea_status                                 (demo_pwm_core_clk_ea_status                                 ), //u_demo_crg_clk_gen.output,
		.demo_pwm_core_clk                                           (demo_pwm_core_clk                                           ), //u_demo_crg_clk_gen.output,
		.demo_sc_ref_clk_ea                                          (demo_sc_ref_clk_ea                                          ), //u_demo_crg_clk_gen.input,
		.demo_sc_ref_clk_ea_status                                   (demo_sc_ref_clk_ea_status                                   ), //u_demo_crg_clk_gen.output,
		.demo_sc_ref_clk                                             (demo_sc_ref_clk                                             ) //u_demo_crg_clk_gen.output,
	);

	demo_crg_rst_gen	u_demo_crg_rst_gen(
		.demo_rst_n                                                  (demo_rst_n                                                  ), //u_demo_crg_rst_gen.input,
		.demo_por_rst_n                                              (demo_por_rst_n                                              ), //u_demo_crg_rst_gen.input,
		.test_rstn                                                   (test_rstn                                                   ), //u_demo_crg_rst_gen.input,
		.test_mode                                                   (test_mode                                                   ), //u_demo_crg_rst_gen.input,
		.demo_lp_core_rst_n_sftrstn                                  (demo_lp_core_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_lp_core_rst_n                                          (demo_lp_core_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_lpcore_rst_n                                           (demo_lpcore_rst_n                                           ), //u_demo_crg_rst_gen.input,
		.demo_lp_cpu_rst_n                                           (demo_lp_cpu_rst_n                                           ), //u_demo_crg_rst_gen.input,
		.demo_lp_core_demo_por_rst_n_sftrstn                         (demo_lp_core_demo_por_rst_n_sftrstn                         ), //u_demo_crg_rst_gen.input,
		.demo_lp_core_demo_por_rst_n                                 (demo_lp_core_demo_por_rst_n                                 ), //u_demo_crg_rst_gen.output,
		.demo_hw_rst_n                                               (demo_hw_rst_n                                               ), //u_demo_crg_rst_gen.input,
		.demo_uart_apb_rst_n_sftrstn                                 (demo_uart_apb_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,
		.demo_uart_apb_rst_n                                         (demo_uart_apb_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_top_rst_n                                              (demo_top_rst_n                                              ), //u_demo_crg_rst_gen.input,
		.demo_uart_core_rst_n_sftrstn                                (demo_uart_core_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_uart_core_rst_n                                        (demo_uart_core_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_usim0_32k_rst_n_sftrstn                                (demo_usim0_32k_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_usim0_32k_rst_n                                        (demo_usim0_32k_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_usim_rst_n                                             (demo_usim_rst_n                                             ), //u_demo_crg_rst_gen.input,
		.demo_usim0_apb_rst_n_sftrstn                                (demo_usim0_apb_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_usim0_apb_rst_n                                        (demo_usim0_apb_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_gpio_apb_rst_n_sftrstn                                 (demo_gpio_apb_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,
		.demo_gpio_apb_rst_n                                         (demo_gpio_apb_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_i2c_core_rst_n_sftrstn                                 (demo_i2c_core_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,
		.demo_i2c_core_rst_n                                         (demo_i2c_core_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_i2c_apb_rst_n_sftrstn                                  (demo_i2c_apb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_i2c_apb_rst_n                                          (demo_i2c_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_usim1_32k_rst_n_sftrstn                                (demo_usim1_32k_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_usim1_32k_rst_n                                        (demo_usim1_32k_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_usim1_apb_rst_n_sftrstn                                (demo_usim1_apb_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_usim1_apb_rst_n                                        (demo_usim1_apb_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_spi_core_rst_n_sftrstn                                 (demo_spi_core_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,
		.demo_spi_core_rst_n                                         (demo_spi_core_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_spi_apb_rst_n_sftrstn                                  (demo_spi_apb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_spi_apb_rst_n                                          (demo_spi_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_pmu_rst_n                                              (demo_pmu_rst_n                                              ), //u_demo_crg_rst_gen.output,
		.demo_pmu_apb_rst_n                                          (demo_pmu_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_pmu_32k_rst_n                                          (demo_pmu_32k_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_pmu_demo_por_rst_n                                     (demo_pmu_demo_por_rst_n                                     ), //u_demo_crg_rst_gen.output,
		.demo_crg_apb_rst_n                                          (demo_crg_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_drx_timer_32k_rst_n_sftrstn                            (demo_drx_timer_32k_rst_n_sftrstn                            ), //u_demo_crg_rst_gen.input,
		.demo_drx_timer_32k_rst_n                                    (demo_drx_timer_32k_rst_n                                    ), //u_demo_crg_rst_gen.output,
		.demo_drx_timer_phy_rst_n_sftrstn                            (demo_drx_timer_phy_rst_n_sftrstn                            ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_drx_timer_phy_rst_n                                    (demo_drx_timer_phy_rst_n                                    ), //u_demo_crg_rst_gen.output,
		.demo_drx_timer_apb_rst_n_sftrstn                            (demo_drx_timer_apb_rst_n_sftrstn                            ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_drx_timer_apb_rst_n                                    (demo_drx_timer_apb_rst_n                                    ), //u_demo_crg_rst_gen.output,
		.demo_rtc_apb_rst_n_sftrstn                                  (demo_rtc_apb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_rtc_apb_rst_n                                          (demo_rtc_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_rtc_core_rst_n_sftrstn                                 (demo_rtc_core_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_rtc_core_rst_n                                         (demo_rtc_core_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_wdt_apb_rst_n_sftrstn                                  (demo_wdt_apb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_wdt_apb_rst_n                                          (demo_wdt_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_wdt_rst_n_sftrstn                                      (demo_wdt_rst_n_sftrstn                                      ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_wdt_rst_n                                              (demo_wdt_rst_n                                              ), //u_demo_crg_rst_gen.output,
		.demo_timer_apb_rst_n_sftrstn                                (demo_timer_apb_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_timer_apb_rst_n                                        (demo_timer_apb_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_sc_apb_rst_n_sftrstn                                   (demo_sc_apb_rst_n_sftrstn                                   ), //u_demo_crg_rst_gen.input,
		.demo_sc_apb_rst_n                                           (demo_sc_apb_rst_n                                           ), //u_demo_crg_rst_gen.output,
		.demo_sc_demo_por_rst_n                                      (demo_sc_demo_por_rst_n                                      ), //u_demo_crg_rst_gen.output,
		.demo_rom_ahb_rst_n_sftrstn                                  (demo_rom_ahb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_rom_ahb_rst_n                                          (demo_rom_ahb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_rdc_ahb_rst_n_sftrstn                                  (demo_rdc_ahb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_rdc_ahb_rst_n                                          (demo_rdc_ahb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_rdc_rst_n_sftrstn                                      (demo_rdc_rst_n_sftrstn                                      ), //u_demo_crg_rst_gen.input,
		.demo_rdc_rst_n                                              (demo_rdc_rst_n                                              ), //u_demo_crg_rst_gen.output,
		.demo_cipher_sec_core_rst_n_sftrstn                          (demo_cipher_sec_core_rst_n_sftrstn                          ), //u_demo_crg_rst_gen.input,
		.demo_cipher_sec_core_rst_n                                  (demo_cipher_sec_core_rst_n                                  ), //u_demo_crg_rst_gen.output,
		.demo_cipher_sec_pk_rst_n_sftrstn                            (demo_cipher_sec_pk_rst_n_sftrstn                            ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_cipher_sec_pk_rst_n                                    (demo_cipher_sec_pk_rst_n                                    ), //u_demo_crg_rst_gen.output,
		.demo_efuse_ctrl_logic_rst_n_sftrstn                         (demo_efuse_ctrl_logic_rst_n_sftrstn                         ), //u_demo_crg_rst_gen.input,
		.demo_efuse_ctrl_logic_rst_n                                 (demo_efuse_ctrl_logic_rst_n                                 ), //u_demo_crg_rst_gen.output,
		.demo_efuse_ctrl_demo_por_rst_n                              (demo_efuse_ctrl_demo_por_rst_n                              ), //u_demo_crg_rst_gen.output,
		.demo_sec_ctrl0_rst_n_sftrstn                                (demo_sec_ctrl0_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_sec_ctrl0_rst_n                                        (demo_sec_ctrl0_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_sec_ctrl1_rst_n                                        (demo_sec_ctrl1_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_sec_ctrl2_rst_n_sftrstn                                (demo_sec_ctrl2_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_sec_ctrl2_rst_n                                        (demo_sec_ctrl2_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_io_apb_rst_n_sftrstn                                   (demo_io_apb_rst_n_sftrstn                                   ), //u_demo_crg_rst_gen.input,
		.demo_io_apb_rst_n                                           (demo_io_apb_rst_n                                           ), //u_demo_crg_rst_gen.output,
		.misc_ahb_rst_n_sftrstn                                      (misc_ahb_rst_n_sftrstn                                      ), //u_demo_crg_rst_gen.input,
		.misc_ahb_rst_n                                              (misc_ahb_rst_n                                              ), //u_demo_crg_rst_gen.output,
		.demo_soctop_rst_n                                           (demo_soctop_rst_n                                           ), //u_demo_crg_rst_gen.input,
		.dtss_dt_rst_n_sftrstn                                       (dtss_dt_rst_n_sftrstn                                       ), //u_demo_crg_rst_gen.input,
		.dtss_dt_rst_n                                               (dtss_dt_rst_n                                               ), //u_demo_crg_rst_gen.output,
		.demo_ocmem_ahb_rst_n_sftrstn                                (demo_ocmem_ahb_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_ocmem_ahb_rst_n                                        (demo_ocmem_ahb_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_timer64_ahb_rst_n_sftrstn                              (demo_timer64_ahb_rst_n_sftrstn                              ), //u_demo_crg_rst_gen.input,
		.demo_timer64_ahb_rst_n                                      (demo_timer64_ahb_rst_n                                      ), //u_demo_crg_rst_gen.output,
		.demo_timer64_rst_n_sftrstn                                  (demo_timer64_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_timer64_rst_n                                          (demo_timer64_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_pwm_apb_rst_n_sftrstn                                  (demo_pwm_apb_rst_n_sftrstn                                  ), //u_demo_crg_rst_gen.input,
		.demo_pwm_apb_rst_n                                          (demo_pwm_apb_rst_n                                          ), //u_demo_crg_rst_gen.output,
		.demo_pwm_core_rst_n_sftrstn                                 (demo_pwm_core_rst_n_sftrstn                                 ), //u_demo_crg_rst_gen.input,undrive --- fixme
		.demo_pwm_core_rst_n                                         (demo_pwm_core_rst_n                                         ), //u_demo_crg_rst_gen.output,
		.demo_timer_cnt_rst_n_sftrstn                                (demo_timer_cnt_rst_n_sftrstn                                ), //u_demo_crg_rst_gen.input,
		.demo_timer_cnt_rst_n                                        (demo_timer_cnt_rst_n                                        ), //u_demo_crg_rst_gen.output,
		.demo_lp_bus_rst_n                                           (demo_lp_bus_rst_n                                           ), //u_demo_crg_rst_gen.output,
		.demo_top_lp_bus_rst_n_sftrstn                               (demo_top_lp_bus_rst_n_sftrstn                               ), //u_demo_crg_rst_gen.input,
		.demo_top_lp_bus_rst_n                                       (demo_top_lp_bus_rst_n                                       ), //u_demo_crg_rst_gen.output,
		.demo_top_soc_soft_rst_n                                     (demo_top_soc_soft_rst_n                                     ) //u_demo_crg_rst_gen.input,
	);

endmodule

