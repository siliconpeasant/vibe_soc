// ============================================================================
// File Name    : demo_crg_clk_gen.v
// Description  :
// Author       : autumn
// Created On   : 2026/08/02 13:16
// Last Modified: 2026/08/02 13:16
// ----------------------------------------------------------------------------
// Date         By           Version  Description
// ----------------------------------------------------------------------------
// 2026/08/02   autumn      1.0      Initial version
// ============================================================================
module demo_crg_clk_gen(
	input           apb_clk,
	input           apb_rst_n,
    input           dft_icg_mode_root,
	input           test_mode,
	input           demo_main_clk,
	input           clk_gen_rst_n,
	input           demo_ref_clk,
	input           rtc32k_muxed_clk,
	input           demo_32k_clk,
	input           demo_32k_sko,
	input           rt32k_muxed1_clk,
	input           demo_bb_clk,
	// rt32k_muxed0_clk
	input           rt32k_muxed0_clk_sel,
	output          rt32k_muxed0_clk_sel_clk0_sel,
	output          rt32k_muxed0_clk_sel_clk1_sel,
	output          rt32k_muxed0_clk_sel_done,
	output          rt32k_muxed0_clk,
	// demo_ref_clk_test_clk
	output          demo_ref_clk_test_clk,
	// demo_main_muxed_clk
	input           demo_main_muxed_clk_sel,
	output          demo_main_muxed_clk_sel_clk0_sel,
	output          demo_main_muxed_clk_sel_clk1_sel,
	output          demo_main_muxed_clk_sel_done,
	// demo_main_muxed_occ_clk
	output          demo_main_muxed_occ_clk,
	// demo_lp_core_clk
	input           demo_lp_core_clk_ea,
	output          demo_lp_core_clk_ea_status,
	input              demo_clkgat_req,
	output             demo_lp_core_clk_demo_clkgat_req_sync,
	output          demo_lp_core_clk,
	// demo_lp_mtime_clk
	input           demo_lp_mtime_clk_ea,
	output          demo_lp_mtime_clk_ea_status,
	output             demo_lp_mtime_clk_demo_clkgat_req_sync,
	output          demo_lp_mtime_clk,
	// demo_uart_apb_clk
	input           demo_uart_apb_clk_ea,
	output          demo_uart_apb_clk_ea_status,
	output          demo_uart_apb_clk,
	// demo_uart_core_clk
	input           demo_uart_core_clk_ea,
	output          demo_uart_core_clk_ea_status,
	output          demo_uart_core_clk,
	// demo_usim0_32k_clk
	input           demo_usim0_32k_clk_ea,
	output          demo_usim0_32k_clk_ea_status,
	output          demo_usim0_32k_clk,
	// demo_usim0_apb_clk
	input           demo_usim0_apb_clk_ea,
	output          demo_usim0_apb_clk_ea_status,
	output          demo_usim0_apb_clk,
	// demo_gpio_apb_clk
	input           pmu_clk_switch_refto32K_req_sel,
	input           demo_gpio_apb_clk_sel,
	output          demo_gpio_apb_clk_sel_clk0_sel,
	output          demo_gpio_apb_clk_sel_clk1_sel,
	output          demo_gpio_apb_clk_sel_done,
	input           demo_gpio_apb_clk_ea,
	output          demo_gpio_apb_clk_ea_status,
	output          demo_gpio_apb_clk,
	// demo_i2c_core_clk
	input           demo_i2c_core_clk_ea,
	output          demo_i2c_core_clk_ea_status,
	output          demo_i2c_core_clk,
	// demo_i2c_apb_clk
	input           demo_i2c_apb_clk_ea,
	output          demo_i2c_apb_clk_ea_status,
	output          demo_i2c_apb_clk,
	// demo_usim1_32k_clk
	input           demo_usim1_32k_clk_ea,
	output          demo_usim1_32k_clk_ea_status,
	output          demo_usim1_32k_clk,
	// demo_usim1_apb_clk
	input           demo_usim1_apb_clk_ea,
	output          demo_usim1_apb_clk_ea_status,
	output          demo_usim1_apb_clk,
	// demo_spi_core_clk
	input           demo_spi_core_clk_ea,
	output          demo_spi_core_clk_ea_status,
	output          demo_spi_core_clk,
	// demo_spi_apb_clk
	input           demo_spi_apb_clk_ea,
	output          demo_spi_apb_clk_ea_status,
	output          demo_spi_apb_clk,
	// demo_pmu_32k_clk
	input           demo_pmu_32k_clk_ea,
	output          demo_pmu_32k_clk_ea_status,
	output          demo_pmu_32k_clk,
	// demo_pmu_clk
	input           demo_pmu_clk_ea,
	output          demo_pmu_clk_ea_status,
	output          demo_pmu_clk,
	// demo_pmu_apb_clk
	input           demo_pmu_apb_clk_ea,
	output          demo_pmu_apb_clk_ea_status,
	output          demo_pmu_apb_clk,
	// demo_crg_apb_clk
	output          demo_crg_apb_clk,
	// demo_drx_timer_32k_clk
	input           demo_drx_timer_32k_clk_ea,
	output          demo_drx_timer_32k_clk_ea_status,
	output          demo_drx_timer_32k_clk,
	// demo_drx_timer_phy_clk
	output          demo_drx_timer_phy_clk,
	// demo_drx_timer_apb_clk
	input           demo_drx_timer_apb_clk_ea,
	output          demo_drx_timer_apb_clk_ea_status,
	output          demo_drx_timer_apb_clk,
	// demo_rtc_apb_clk
	input           demo_rtc_apb_clk_ea,
	output          demo_rtc_apb_clk_ea_status,
	output          demo_rtc_apb_clk,
	// demo_rtc_core_clk
	input           demo_rtc_core_clk_ea,
	output          demo_rtc_core_clk_ea_status,
	output          demo_rtc_core_clk,
	// demo_wdt_apb_clk
	input           demo_wdt_apb_clk_ea,
	output          demo_wdt_apb_clk_ea_status,
	output          demo_wdt_apb_clk,
	// demo_wdt_clk
	input           demo_wdt_clk_ea,
	output          demo_wdt_clk_ea_status,
	output          demo_wdt_clk,
	// demo_timer_apb_clk
	input           demo_timer_apb_clk_sel,
	output          demo_timer_apb_clk_sel_clk0_sel,
	output          demo_timer_apb_clk_sel_clk1_sel,
	output          demo_timer_apb_clk_sel_done,
	input           demo_timer_apb_clk_ea,
	output          demo_timer_apb_clk_ea_status,
	output          demo_timer_apb_clk,
	// demo_timer_cnt_clk
	input           demo_timer_cnt_clk_ea,
	output          demo_timer_cnt_clk_ea_status,
	output          demo_timer_cnt_clk,
	// demo_sc_apb_clk
	input           demo_sc_apb_clk_ea,
	output          demo_sc_apb_clk_ea_status,
	output          demo_sc_apb_clk,
	// demo_rom_ahb_clk
	input           demo_rom_ahb_clk_ea,
	output          demo_rom_ahb_clk_ea_status,
	input              demo_rom_gat_n,
	output             demo_rom_ahb_clk_demo_rom_gat_n_sync,
	output          demo_rom_ahb_clk,
	// demo_rdc_ahb_clk
	input           demo_rdc_ahb_clk_ea,
	output          demo_rdc_ahb_clk_ea_status,
	output          demo_rdc_ahb_clk,
	// demo_rdc_clk
	input           demo_rdc_clk_ea,
	output          demo_rdc_clk_ea_status,
	output          demo_rdc_clk,
	// demo_cipher_sec_core_clk
	input           demo_cipher_sec_core_clk_ea,
	output          demo_cipher_sec_core_clk_ea_status,
	output             demo_cipher_sec_core_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_core_clk,
	// demo_cipher_sec_aes_clk
	input           demo_cipher_sec_aes_clk_ea,
	output          demo_cipher_sec_aes_clk_ea_status,
	output             demo_cipher_sec_aes_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_aes_clk,
	// demo_cipher_sec_hash_clk
	input           demo_cipher_sec_hash_clk_ea,
	output          demo_cipher_sec_hash_clk_ea_status,
	output             demo_cipher_sec_hash_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_hash_clk,
	// demo_cipher_sec_sm4_clk
	input           demo_cipher_sec_sm4_clk_ea,
	output          demo_cipher_sec_sm4_clk_ea_status,
	output             demo_cipher_sec_sm4_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_sm4_clk,
	// demo_main_muxed_clk_for_pk_clk
	// demo_cipher_sec_pk_clk
	input           demo_cipher_sec_pk_clk_ea,
	output          demo_cipher_sec_pk_clk_ea_status,
	output             demo_cipher_sec_pk_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_pk_clk,
	// demo_cipher_sec_pkdiv2_clk
	input [ 2:0]    demo_cipher_sec_pkdiv2_clk_divider,
	input           demo_cipher_sec_pkdiv2_clk_divider_ea_req,
	output[ 2:0]    demo_cipher_sec_pkdiv2_clk_divider_status,
	output          demo_cipher_sec_pkdiv2_clk_divider_done,
	input           demo_cipher_sec_pkdiv2_clk_ea,
	output          demo_cipher_sec_pkdiv2_clk_ea_status,
	output             demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync,
	output          demo_cipher_sec_pkdiv2_clk,
	// demo_efuse_ctrl_ahb_clk
	input           demo_efuse_ctrl_ahb_clk_ea,
	output          demo_efuse_ctrl_ahb_clk_ea_status,
	output          demo_efuse_ctrl_ahb_clk,
	// demo_sec_ctrl0_clk
	input           demo_sec_ctrl0_clk_ea,
	output          demo_sec_ctrl0_clk_ea_status,
	output          demo_sec_ctrl0_clk,
	// demo_sec_ctrl1_clk
	input           demo_sec_ctrl1_clk_ea,
	output          demo_sec_ctrl1_clk_ea_status,
	output          demo_sec_ctrl1_clk,
	// demo_sec_ctrl2_clk
	input           demo_sec_ctrl2_clk_ea,
	output          demo_sec_ctrl2_clk_ea_status,
	output          demo_sec_ctrl2_clk,
	// demo_io_apb_clk
	input           demo_io_apb_clk_ea,
	output          demo_io_apb_clk_ea_status,
	output          demo_io_apb_clk,
	// demo_lp_bus_clk
	output          demo_lp_bus_clk,
	// soc_32k_clk
	output          soc_32k_clk,
	// misc_ahb_clk
	input           misc_ahb_clk_ea,
	output          misc_ahb_clk_ea_status,
	output          misc_ahb_clk,
	// dtss_dt_clk
	input           dtss_dt_clk_ea,
	output          dtss_dt_clk_ea_status,
	output          dtss_dt_clk,
	// demo_ocmem_ahb_clk
	input           demo_ocmem_ahb_clk_ea,
	output          demo_ocmem_ahb_clk_ea_status,
	output          demo_ocmem_ahb_clk,
	// demo_timer64_ahb_clk
	input           demo_timer64_ahb_clk_ea,
	output          demo_timer64_ahb_clk_ea_status,
	output          demo_timer64_ahb_clk,
	// demo_timer64_clk
	input           demo_timer64_clk_ea,
	output          demo_timer64_clk_ea_status,
	output          demo_timer64_clk,
	// demo_pwm_apb_clk
	input           demo_pwm_apb_clk_ea,
	output          demo_pwm_apb_clk_ea_status,
	output          demo_pwm_apb_clk,
	// demo_pwm_core_clk
	input           demo_pwm_core_clk_sel,
	output          demo_pwm_core_clk_sel_clk0_sel,
	output          demo_pwm_core_clk_sel_clk1_sel,
	output          demo_pwm_core_clk_sel_done,
	input           demo_pwm_core_clk_ea,
	output          demo_pwm_core_clk_ea_status,
	output          demo_pwm_core_clk,
	// demo_sc_ref_clk
	input           demo_sc_ref_clk_ea,
	output          demo_sc_ref_clk_ea_status,
	output          demo_sc_ref_clk
);

wire         rt32k_muxed0_clk_sel_clk0_sel_bf_sync;
wire         rt32k_muxed0_clk_sel_clk1_sel_bf_sync;
wire         rt32k_muxed0_clk_sel_done_bf_sync;
wire         rt32k_muxed0_clk_muxed;
wire        demo_ref_clk_test_clk_buf_out;
wire         demo_main_muxed_clk_sel_clk0_sel_bf_sync;
wire         demo_main_muxed_clk_sel_clk1_sel_bf_sync;
wire         demo_main_muxed_clk_sel_done_bf_sync;
wire         demo_main_muxed_clk_muxed;
wire        demo_main_muxed_clk;
wire        demo_main_muxed_occ_clk_buf_out;
wire        demo_lp_core_clk_ea_sync;
wire        demo_lp_core_clk_ea_multi;
wire        demo_lp_mtime_clk_ea_sync;
wire        demo_lp_mtime_clk_ea_multi;
wire        demo_uart_apb_clk_ea_sync;
wire        demo_uart_apb_clk_ea_multi;
wire        demo_uart_core_clk_ea_sync;
wire        demo_uart_core_clk_ea_multi;
wire        demo_usim0_32k_clk_ea_sync;
wire        demo_usim0_32k_clk_ea_multi;
wire        demo_usim0_apb_clk_ea_sync;
wire        demo_usim0_apb_clk_ea_multi;
wire         demo_gpio_apb_clk_sel_clk0_sel_bf_sync;
wire         demo_gpio_apb_clk_sel_clk1_sel_bf_sync;
wire         demo_gpio_apb_clk_sel_done_bf_sync;
wire         demo_gpio_apb_clk_muxed;
wire        demo_gpio_apb_clk_ea_sync;
wire        demo_gpio_apb_clk_ea_multi;
wire        demo_i2c_core_clk_ea_sync;
wire        demo_i2c_core_clk_ea_multi;
wire        demo_i2c_apb_clk_ea_sync;
wire        demo_i2c_apb_clk_ea_multi;
wire        demo_usim1_32k_clk_ea_sync;
wire        demo_usim1_32k_clk_ea_multi;
wire        demo_usim1_apb_clk_ea_sync;
wire        demo_usim1_apb_clk_ea_multi;
wire        demo_spi_core_clk_ea_sync;
wire        demo_spi_core_clk_ea_multi;
wire        demo_spi_apb_clk_ea_sync;
wire        demo_spi_apb_clk_ea_multi;
wire        demo_pmu_32k_clk_ea_sync;
wire        demo_pmu_32k_clk_ea_multi;
wire        demo_pmu_clk_ea_sync;
wire        demo_pmu_clk_ea_multi;
wire        demo_pmu_apb_clk_ea_sync;
wire        demo_pmu_apb_clk_ea_multi;
wire        demo_drx_timer_32k_clk_ea_sync;
wire        demo_drx_timer_32k_clk_ea_multi;
wire        demo_drx_timer_phy_clk_buf_out;
wire        demo_drx_timer_apb_clk_ea_sync;
wire        demo_drx_timer_apb_clk_ea_multi;
wire        demo_rtc_apb_clk_ea_sync;
wire        demo_rtc_apb_clk_ea_multi;
wire        demo_rtc_core_clk_ea_sync;
wire        demo_rtc_core_clk_ea_multi;
wire        demo_wdt_apb_clk_ea_sync;
wire        demo_wdt_apb_clk_ea_multi;
wire        demo_wdt_clk_ea_sync;
wire        demo_wdt_clk_ea_multi;
wire         demo_timer_apb_clk_sel_clk0_sel_bf_sync;
wire         demo_timer_apb_clk_sel_clk1_sel_bf_sync;
wire         demo_timer_apb_clk_sel_done_bf_sync;
wire         demo_timer_apb_clk_muxed;
wire        demo_timer_apb_clk_ea_sync;
wire        demo_timer_apb_clk_ea_multi;
wire        demo_timer_cnt_clk_ea_sync;
wire        demo_timer_cnt_clk_ea_multi;
wire        demo_sc_apb_clk_ea_sync;
wire        demo_sc_apb_clk_ea_multi;
wire        demo_rom_ahb_clk_ea_sync;
wire        demo_rom_ahb_clk_ea_multi;
wire        demo_rdc_ahb_clk_ea_sync;
wire        demo_rdc_ahb_clk_ea_multi;
wire        demo_rdc_clk_ea_sync;
wire        demo_rdc_clk_ea_multi;
wire        demo_cipher_sec_core_clk_ea_sync;
wire        demo_cipher_sec_core_clk_ea_multi;
wire        demo_cipher_sec_aes_clk_ea_sync;
wire        demo_cipher_sec_aes_clk_ea_multi;
wire        demo_cipher_sec_hash_clk_ea_sync;
wire        demo_cipher_sec_hash_clk_ea_multi;
wire        demo_cipher_sec_sm4_clk_ea_sync;
wire        demo_cipher_sec_sm4_clk_ea_multi;
wire        demo_main_muxed_clk_for_pk_clk;
wire        demo_cipher_sec_pk_clk_ea_sync;
wire        demo_cipher_sec_pk_clk_ea_multi;
wire        demo_cipher_sec_pkdiv2_clk_dived;
wire        demo_cipher_sec_pkdiv2_clk_buf_out;
wire        demo_cipher_sec_pkdiv2_clk_ea_sync;
wire        demo_cipher_sec_pkdiv2_clk_ea_multi;
wire        demo_efuse_ctrl_ahb_clk_ea_sync;
wire        demo_efuse_ctrl_ahb_clk_ea_multi;
wire        demo_sec_ctrl0_clk_ea_sync;
wire        demo_sec_ctrl0_clk_ea_multi;
wire        demo_sec_ctrl1_clk_ea_sync;
wire        demo_sec_ctrl1_clk_ea_multi;
wire        demo_sec_ctrl2_clk_ea_sync;
wire        demo_sec_ctrl2_clk_ea_multi;
wire        demo_io_apb_clk_ea_sync;
wire        demo_io_apb_clk_ea_multi;
wire        misc_ahb_clk_ea_sync;
wire        misc_ahb_clk_ea_multi;
wire        dtss_dt_clk_ea_sync;
wire        dtss_dt_clk_ea_multi;
wire        demo_ocmem_ahb_clk_ea_sync;
wire        demo_ocmem_ahb_clk_ea_multi;
wire        demo_timer64_ahb_clk_ea_sync;
wire        demo_timer64_ahb_clk_ea_multi;
wire        demo_timer64_clk_ea_sync;
wire        demo_timer64_clk_ea_multi;
wire        demo_pwm_apb_clk_ea_sync;
wire        demo_pwm_apb_clk_ea_multi;
wire         demo_pwm_core_clk_sel_clk0_sel_bf_sync;
wire         demo_pwm_core_clk_sel_clk1_sel_bf_sync;
wire         demo_pwm_core_clk_sel_done_bf_sync;
wire         demo_pwm_core_clk_muxed;
wire        demo_pwm_core_clk_ea_sync;
wire        demo_pwm_core_clk_ea_multi;
wire        demo_sc_ref_clk_ea_sync;
wire        demo_sc_ref_clk_ea_multi;
//===============
// rt32k_muxed0_clk ctrl
//===============
// clk sel
clk_glitch_free_switch u_rt32k_muxed0_clk_clk_glitch_free_switch(
    .test_mode  (test_mode              ),
    .rst0_n     (clk_gen_rst_n          ),
    .rst1_n     (clk_gen_rst_n          ),
    .clk0       (demo_32k_clk        ),
    .clk1       (demo_32k_sko        ),
    .sel        (rt32k_muxed0_clk_sel           ),
    .clk0_sel   (rt32k_muxed0_clk_sel_clk0_sel_bf_sync  ),
    .clk1_sel   (rt32k_muxed0_clk_sel_clk1_sel_bf_sync  ),
    .sel_done   (rt32k_muxed0_clk_sel_done_bf_sync      ),
    .clk_out    (rt32k_muxed0_clk_muxed         )
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_rt32k_muxed0_clk_sel_clk0_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (rt32k_muxed0_clk_sel_clk0_sel_bf_sync),
    .data_d     (rt32k_muxed0_clk_sel_clk0_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b0      )
)
u_rt32k_muxed0_clk_sel_clk1_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (rt32k_muxed0_clk_sel_clk1_sel_bf_sync),
    .data_d     (rt32k_muxed0_clk_sel_clk1_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_rt32k_muxed0_clk_sel_done_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (rt32k_muxed0_clk_sel_done_bf_sync),
    .data_d     (rt32k_muxed0_clk_sel_done)
);

assign rt32k_muxed0_clk = rt32k_muxed0_clk_muxed;
//===============
// demo_ref_clk_test_clk ctrl
//===============
clk_buf_for_occ u_demo_ref_clk_test_clk_buf_for_occ(/*autoinst*/
    .clkin                  (demo_ref_clk     ), //input
    .clkout                 (demo_ref_clk_test_clk_buf_out    )  //output
);
assign demo_ref_clk_test_clk = demo_ref_clk_test_clk_buf_out;
//===============
// demo_main_muxed_clk ctrl
//===============
// clk sel
clk_glitch_free_switch u_demo_main_muxed_clk_clk_glitch_free_switch(
    .test_mode  (test_mode              ),
    .rst0_n     (clk_gen_rst_n          ),
    .rst1_n     (clk_gen_rst_n          ),
    .clk0       (demo_ref_clk        ),
    .clk1       (demo_main_clk        ),
    .sel        (demo_main_muxed_clk_sel           ),
    .clk0_sel   (demo_main_muxed_clk_sel_clk0_sel_bf_sync  ),
    .clk1_sel   (demo_main_muxed_clk_sel_clk1_sel_bf_sync  ),
    .sel_done   (demo_main_muxed_clk_sel_done_bf_sync      ),
    .clk_out    (demo_main_muxed_clk_muxed         )
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_main_muxed_clk_sel_clk0_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_main_muxed_clk_sel_clk0_sel_bf_sync),
    .data_d     (demo_main_muxed_clk_sel_clk0_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b0      )
)
u_demo_main_muxed_clk_sel_clk1_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_main_muxed_clk_sel_clk1_sel_bf_sync),
    .data_d     (demo_main_muxed_clk_sel_clk1_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_main_muxed_clk_sel_done_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_main_muxed_clk_sel_done_bf_sync),
    .data_d     (demo_main_muxed_clk_sel_done)
);

assign demo_main_muxed_clk = demo_main_muxed_clk_muxed;
//===============
// demo_main_muxed_occ_clk ctrl
//===============
clk_buf_for_occ u_demo_main_muxed_occ_clk_buf_for_occ(/*autoinst*/
    .clkin                  (demo_main_muxed_clk     ), //input
    .clkout                 (demo_main_muxed_occ_clk_buf_out    )  //output
);
assign demo_main_muxed_occ_clk = demo_main_muxed_occ_clk_buf_out;
//===============
// demo_lp_core_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_lp_core_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_lp_core_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_lp_core_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_lp_core_clk_ea          ), //input
    .data_d                 (demo_lp_core_clk_ea_sync     )  //output
);

assign demo_lp_core_clk_ea_multi = demo_lp_core_clk_ea_sync & demo_lp_core_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_lp_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_lp_core_clk_ea_multi),
    .data_d     (demo_lp_core_clk_ea_status)
);

icg u_demo_lp_core_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_lp_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_lp_core_clk                     )  //output
);
//===============
// demo_lp_mtime_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_lp_mtime_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_ref_clk_test_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_lp_mtime_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_lp_mtime_clk_icg_sync(
    .clk_d                  (demo_ref_clk_test_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_lp_mtime_clk_ea          ), //input
    .data_d                 (demo_lp_mtime_clk_ea_sync     )  //output
);

assign demo_lp_mtime_clk_ea_multi = demo_lp_mtime_clk_ea_sync & demo_lp_mtime_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_lp_mtime_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_lp_mtime_clk_ea_multi),
    .data_d     (demo_lp_mtime_clk_ea_status)
);

icg u_demo_lp_mtime_clk_icg(
    .clkin                  (demo_ref_clk_test_clk     ), //input
    .enable                 (demo_lp_mtime_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_lp_mtime_clk                     )  //output
);
//===============
// demo_uart_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_uart_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_uart_apb_clk_ea          ), //input
    .data_d                 (demo_uart_apb_clk_ea_sync     )  //output
);

assign demo_uart_apb_clk_ea_multi = demo_uart_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_uart_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_uart_apb_clk_ea_multi),
    .data_d     (demo_uart_apb_clk_ea_status)
);

icg u_demo_uart_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_uart_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_uart_apb_clk                     )  //output
);
//===============
// demo_uart_core_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_uart_core_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_uart_core_clk_ea          ), //input
    .data_d                 (demo_uart_core_clk_ea_sync     )  //output
);

assign demo_uart_core_clk_ea_multi = demo_uart_core_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_uart_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_uart_core_clk_ea_multi),
    .data_d     (demo_uart_core_clk_ea_status)
);

icg u_demo_uart_core_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_uart_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_uart_core_clk                     )  //output
);
//===============
// demo_usim0_32k_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_usim0_32k_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_usim0_32k_clk_ea          ), //input
    .data_d                 (demo_usim0_32k_clk_ea_sync     )  //output
);

assign demo_usim0_32k_clk_ea_multi = demo_usim0_32k_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_usim0_32k_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_usim0_32k_clk_ea_multi),
    .data_d     (demo_usim0_32k_clk_ea_status)
);

icg u_demo_usim0_32k_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_usim0_32k_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_usim0_32k_clk                     )  //output
);
//===============
// demo_usim0_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_usim0_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_usim0_apb_clk_ea          ), //input
    .data_d                 (demo_usim0_apb_clk_ea_sync     )  //output
);

assign demo_usim0_apb_clk_ea_multi = demo_usim0_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_usim0_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_usim0_apb_clk_ea_multi),
    .data_d     (demo_usim0_apb_clk_ea_status)
);

icg u_demo_usim0_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_usim0_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_usim0_apb_clk                     )  //output
);
//===============
// demo_gpio_apb_clk ctrl
//===============
// clk sel
clk_glitch_free_switch u_demo_gpio_apb_clk_clk_glitch_free_switch(
    .test_mode  (test_mode              ),
    .rst0_n     (clk_gen_rst_n          ),
    .rst1_n     (clk_gen_rst_n          ),
    .clk0       (demo_main_muxed_occ_clk        ),
    .clk1       (rtc32k_muxed_clk        ),
    .sel        (demo_gpio_apb_clk_sel | pmu_clk_switch_refto32K_req_sel       ),
    .clk0_sel   (demo_gpio_apb_clk_sel_clk0_sel_bf_sync  ),
    .clk1_sel   (demo_gpio_apb_clk_sel_clk1_sel_bf_sync  ),
    .sel_done   (demo_gpio_apb_clk_sel_done_bf_sync      ),
    .clk_out    (demo_gpio_apb_clk_muxed         )
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_gpio_apb_clk_sel_clk0_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_gpio_apb_clk_sel_clk0_sel_bf_sync),
    .data_d     (demo_gpio_apb_clk_sel_clk0_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b0      )
)
u_demo_gpio_apb_clk_sel_clk1_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_gpio_apb_clk_sel_clk1_sel_bf_sync),
    .data_d     (demo_gpio_apb_clk_sel_clk1_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_gpio_apb_clk_sel_done_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_gpio_apb_clk_sel_done_bf_sync),
    .data_d     (demo_gpio_apb_clk_sel_done)
);


sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_gpio_apb_clk_icg_sync(
    .clk_d                  (demo_gpio_apb_clk_muxed     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_gpio_apb_clk_ea          ), //input
    .data_d                 (demo_gpio_apb_clk_ea_sync     )  //output
);

assign demo_gpio_apb_clk_ea_multi = demo_gpio_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_gpio_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_gpio_apb_clk_ea_multi),
    .data_d     (demo_gpio_apb_clk_ea_status)
);

icg u_demo_gpio_apb_clk_icg(
    .clkin                  (demo_gpio_apb_clk_muxed      ), //input
    .enable                 (demo_gpio_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_gpio_apb_clk                     )  //output
);
//===============
// demo_i2c_core_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_i2c_core_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_i2c_core_clk_ea          ), //input
    .data_d                 (demo_i2c_core_clk_ea_sync     )  //output
);

assign demo_i2c_core_clk_ea_multi = demo_i2c_core_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_i2c_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_i2c_core_clk_ea_multi),
    .data_d     (demo_i2c_core_clk_ea_status)
);

icg u_demo_i2c_core_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_i2c_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_i2c_core_clk                     )  //output
);
//===============
// demo_i2c_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_i2c_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_i2c_apb_clk_ea          ), //input
    .data_d                 (demo_i2c_apb_clk_ea_sync     )  //output
);

assign demo_i2c_apb_clk_ea_multi = demo_i2c_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_i2c_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_i2c_apb_clk_ea_multi),
    .data_d     (demo_i2c_apb_clk_ea_status)
);

icg u_demo_i2c_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_i2c_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_i2c_apb_clk                     )  //output
);
//===============
// demo_usim1_32k_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_usim1_32k_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_usim1_32k_clk_ea          ), //input
    .data_d                 (demo_usim1_32k_clk_ea_sync     )  //output
);

assign demo_usim1_32k_clk_ea_multi = demo_usim1_32k_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_usim1_32k_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_usim1_32k_clk_ea_multi),
    .data_d     (demo_usim1_32k_clk_ea_status)
);

icg u_demo_usim1_32k_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_usim1_32k_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_usim1_32k_clk                     )  //output
);
//===============
// demo_usim1_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_usim1_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_usim1_apb_clk_ea          ), //input
    .data_d                 (demo_usim1_apb_clk_ea_sync     )  //output
);

assign demo_usim1_apb_clk_ea_multi = demo_usim1_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_usim1_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_usim1_apb_clk_ea_multi),
    .data_d     (demo_usim1_apb_clk_ea_status)
);

icg u_demo_usim1_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_usim1_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_usim1_apb_clk                     )  //output
);
//===============
// demo_spi_core_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_spi_core_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_spi_core_clk_ea          ), //input
    .data_d                 (demo_spi_core_clk_ea_sync     )  //output
);

assign demo_spi_core_clk_ea_multi = demo_spi_core_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_spi_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_spi_core_clk_ea_multi),
    .data_d     (demo_spi_core_clk_ea_status)
);

icg u_demo_spi_core_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_spi_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_spi_core_clk                     )  //output
);
//===============
// demo_spi_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_spi_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_spi_apb_clk_ea          ), //input
    .data_d                 (demo_spi_apb_clk_ea_sync     )  //output
);

assign demo_spi_apb_clk_ea_multi = demo_spi_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_spi_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_spi_apb_clk_ea_multi),
    .data_d     (demo_spi_apb_clk_ea_status)
);

icg u_demo_spi_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_spi_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_spi_apb_clk                     )  //output
);
//===============
// demo_pmu_32k_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_pmu_32k_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_pmu_32k_clk_ea          ), //input
    .data_d                 (demo_pmu_32k_clk_ea_sync     )  //output
);

assign demo_pmu_32k_clk_ea_multi = demo_pmu_32k_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pmu_32k_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pmu_32k_clk_ea_multi),
    .data_d     (demo_pmu_32k_clk_ea_status)
);

icg u_demo_pmu_32k_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_pmu_32k_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_pmu_32k_clk                     )  //output
);
//===============
// demo_pmu_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_pmu_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_pmu_clk_ea          ), //input
    .data_d                 (demo_pmu_clk_ea_sync     )  //output
);

assign demo_pmu_clk_ea_multi = demo_pmu_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pmu_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pmu_clk_ea_multi),
    .data_d     (demo_pmu_clk_ea_status)
);

icg u_demo_pmu_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_pmu_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_pmu_clk                     )  //output
);
//===============
// demo_pmu_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_pmu_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_pmu_apb_clk_ea          ), //input
    .data_d                 (demo_pmu_apb_clk_ea_sync     )  //output
);

assign demo_pmu_apb_clk_ea_multi = demo_pmu_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pmu_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pmu_apb_clk_ea_multi),
    .data_d     (demo_pmu_apb_clk_ea_status)
);

icg u_demo_pmu_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_pmu_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_pmu_apb_clk                     )  //output
);
//===============
// demo_crg_apb_clk ctrl
//===============
assign demo_crg_apb_clk = demo_main_muxed_occ_clk;
//===============
// demo_drx_timer_32k_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_drx_timer_32k_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_drx_timer_32k_clk_ea          ), //input
    .data_d                 (demo_drx_timer_32k_clk_ea_sync     )  //output
);

assign demo_drx_timer_32k_clk_ea_multi = demo_drx_timer_32k_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_drx_timer_32k_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_drx_timer_32k_clk_ea_multi),
    .data_d     (demo_drx_timer_32k_clk_ea_status)
);

icg u_demo_drx_timer_32k_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_drx_timer_32k_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_drx_timer_32k_clk                     )  //output
);
//===============
// demo_drx_timer_phy_clk ctrl
//===============
clk_buf_for_occ u_demo_drx_timer_phy_clk_buf_for_occ(/*autoinst*/
    .clkin                  (demo_bb_clk     ), //input
    .clkout                 (demo_drx_timer_phy_clk_buf_out    )  //output
);
assign demo_drx_timer_phy_clk = demo_drx_timer_phy_clk_buf_out;
//===============
// demo_drx_timer_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_drx_timer_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_drx_timer_apb_clk_ea          ), //input
    .data_d                 (demo_drx_timer_apb_clk_ea_sync     )  //output
);

assign demo_drx_timer_apb_clk_ea_multi = demo_drx_timer_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_drx_timer_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_drx_timer_apb_clk_ea_multi),
    .data_d     (demo_drx_timer_apb_clk_ea_status)
);

icg u_demo_drx_timer_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_drx_timer_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_drx_timer_apb_clk                     )  //output
);
//===============
// demo_rtc_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_rtc_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_rtc_apb_clk_ea          ), //input
    .data_d                 (demo_rtc_apb_clk_ea_sync     )  //output
);

assign demo_rtc_apb_clk_ea_multi = demo_rtc_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_rtc_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_rtc_apb_clk_ea_multi),
    .data_d     (demo_rtc_apb_clk_ea_status)
);

icg u_demo_rtc_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_rtc_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_rtc_apb_clk                     )  //output
);
//===============
// demo_rtc_core_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_rtc_core_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_rtc_core_clk_ea          ), //input
    .data_d                 (demo_rtc_core_clk_ea_sync     )  //output
);

assign demo_rtc_core_clk_ea_multi = demo_rtc_core_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_rtc_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_rtc_core_clk_ea_multi),
    .data_d     (demo_rtc_core_clk_ea_status)
);

icg u_demo_rtc_core_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_rtc_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_rtc_core_clk                     )  //output
);
//===============
// demo_wdt_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_wdt_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_wdt_apb_clk_ea          ), //input
    .data_d                 (demo_wdt_apb_clk_ea_sync     )  //output
);

assign demo_wdt_apb_clk_ea_multi = demo_wdt_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_wdt_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_wdt_apb_clk_ea_multi),
    .data_d     (demo_wdt_apb_clk_ea_status)
);

icg u_demo_wdt_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_wdt_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_wdt_apb_clk                     )  //output
);
//===============
// demo_wdt_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_wdt_clk_icg_sync(
    .clk_d                  (demo_ref_clk_test_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_wdt_clk_ea          ), //input
    .data_d                 (demo_wdt_clk_ea_sync     )  //output
);

assign demo_wdt_clk_ea_multi = demo_wdt_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_wdt_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_wdt_clk_ea_multi),
    .data_d     (demo_wdt_clk_ea_status)
);

icg u_demo_wdt_clk_icg(
    .clkin                  (demo_ref_clk_test_clk     ), //input
    .enable                 (demo_wdt_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_wdt_clk                     )  //output
);
//===============
// demo_timer_apb_clk ctrl
//===============
// clk sel
clk_glitch_free_switch u_demo_timer_apb_clk_clk_glitch_free_switch(
    .test_mode  (test_mode              ),
    .rst0_n     (clk_gen_rst_n          ),
    .rst1_n     (clk_gen_rst_n          ),
    .clk0       (demo_main_muxed_occ_clk        ),
    .clk1       (rtc32k_muxed_clk        ),
    .sel        (demo_timer_apb_clk_sel | pmu_clk_switch_refto32K_req_sel       ),
    .clk0_sel   (demo_timer_apb_clk_sel_clk0_sel_bf_sync  ),
    .clk1_sel   (demo_timer_apb_clk_sel_clk1_sel_bf_sync  ),
    .sel_done   (demo_timer_apb_clk_sel_done_bf_sync      ),
    .clk_out    (demo_timer_apb_clk_muxed         )
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer_apb_clk_sel_clk0_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer_apb_clk_sel_clk0_sel_bf_sync),
    .data_d     (demo_timer_apb_clk_sel_clk0_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b0      )
)
u_demo_timer_apb_clk_sel_clk1_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer_apb_clk_sel_clk1_sel_bf_sync),
    .data_d     (demo_timer_apb_clk_sel_clk1_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer_apb_clk_sel_done_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer_apb_clk_sel_done_bf_sync),
    .data_d     (demo_timer_apb_clk_sel_done)
);


sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_timer_apb_clk_icg_sync(
    .clk_d                  (demo_timer_apb_clk_muxed     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_timer_apb_clk_ea          ), //input
    .data_d                 (demo_timer_apb_clk_ea_sync     )  //output
);

assign demo_timer_apb_clk_ea_multi = demo_timer_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer_apb_clk_ea_multi),
    .data_d     (demo_timer_apb_clk_ea_status)
);

icg u_demo_timer_apb_clk_icg(
    .clkin                  (demo_timer_apb_clk_muxed      ), //input
    .enable                 (demo_timer_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_timer_apb_clk                     )  //output
);
//===============
// demo_timer_cnt_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_timer_cnt_clk_icg_sync(
    .clk_d                  (rtc32k_muxed_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_timer_cnt_clk_ea          ), //input
    .data_d                 (demo_timer_cnt_clk_ea_sync     )  //output
);

assign demo_timer_cnt_clk_ea_multi = demo_timer_cnt_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer_cnt_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer_cnt_clk_ea_multi),
    .data_d     (demo_timer_cnt_clk_ea_status)
);

icg u_demo_timer_cnt_clk_icg(
    .clkin                  (rtc32k_muxed_clk     ), //input
    .enable                 (demo_timer_cnt_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_timer_cnt_clk                     )  //output
);
//===============
// demo_sc_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_sc_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_sc_apb_clk_ea          ), //input
    .data_d                 (demo_sc_apb_clk_ea_sync     )  //output
);

assign demo_sc_apb_clk_ea_multi = demo_sc_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_sc_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_sc_apb_clk_ea_multi),
    .data_d     (demo_sc_apb_clk_ea_status)
);

icg u_demo_sc_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_sc_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_sc_apb_clk                     )  //output
);
//===============
// demo_rom_ahb_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_rom_ahb_clk_demo_rom_gat_n_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_rom_gat_n          ), //input
            .data_d                 (demo_rom_ahb_clk_demo_rom_gat_n_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_rom_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_rom_ahb_clk_ea          ), //input
    .data_d                 (demo_rom_ahb_clk_ea_sync     )  //output
);

assign demo_rom_ahb_clk_ea_multi = demo_rom_ahb_clk_ea_sync & demo_rom_ahb_clk_demo_rom_gat_n_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_rom_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_rom_ahb_clk_ea_multi),
    .data_d     (demo_rom_ahb_clk_ea_status)
);

icg u_demo_rom_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_rom_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_rom_ahb_clk                     )  //output
);
//===============
// demo_rdc_ahb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_rdc_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_rdc_ahb_clk_ea          ), //input
    .data_d                 (demo_rdc_ahb_clk_ea_sync     )  //output
);

assign demo_rdc_ahb_clk_ea_multi = demo_rdc_ahb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_rdc_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_rdc_ahb_clk_ea_multi),
    .data_d     (demo_rdc_ahb_clk_ea_status)
);

icg u_demo_rdc_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_rdc_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_rdc_ahb_clk                     )  //output
);
//===============
// demo_rdc_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_rdc_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_rdc_clk_ea          ), //input
    .data_d                 (demo_rdc_clk_ea_sync     )  //output
);

assign demo_rdc_clk_ea_multi = demo_rdc_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_rdc_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_rdc_clk_ea_multi),
    .data_d     (demo_rdc_clk_ea_status)
);

icg u_demo_rdc_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_rdc_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_rdc_clk                     )  //output
);
//===============
// demo_cipher_sec_core_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_core_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_core_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_core_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_core_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_core_clk_ea_sync     )  //output
);

assign demo_cipher_sec_core_clk_ea_multi = demo_cipher_sec_core_clk_ea_sync & demo_cipher_sec_core_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_core_clk_ea_multi),
    .data_d     (demo_cipher_sec_core_clk_ea_status)
);

icg u_demo_cipher_sec_core_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_cipher_sec_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_core_clk                     )  //output
);
//===============
// demo_cipher_sec_aes_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_aes_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_aes_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_aes_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_aes_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_aes_clk_ea_sync     )  //output
);

assign demo_cipher_sec_aes_clk_ea_multi = demo_cipher_sec_aes_clk_ea_sync & demo_cipher_sec_aes_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_aes_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_aes_clk_ea_multi),
    .data_d     (demo_cipher_sec_aes_clk_ea_status)
);

icg u_demo_cipher_sec_aes_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_cipher_sec_aes_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_aes_clk                     )  //output
);
//===============
// demo_cipher_sec_hash_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_hash_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_hash_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_hash_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_hash_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_hash_clk_ea_sync     )  //output
);

assign demo_cipher_sec_hash_clk_ea_multi = demo_cipher_sec_hash_clk_ea_sync & demo_cipher_sec_hash_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_hash_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_hash_clk_ea_multi),
    .data_d     (demo_cipher_sec_hash_clk_ea_status)
);

icg u_demo_cipher_sec_hash_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_cipher_sec_hash_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_hash_clk                     )  //output
);
//===============
// demo_cipher_sec_sm4_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_sm4_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_sm4_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_sm4_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_sm4_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_sm4_clk_ea_sync     )  //output
);

assign demo_cipher_sec_sm4_clk_ea_multi = demo_cipher_sec_sm4_clk_ea_sync & demo_cipher_sec_sm4_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_sm4_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_sm4_clk_ea_multi),
    .data_d     (demo_cipher_sec_sm4_clk_ea_status)
);

icg u_demo_cipher_sec_sm4_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_cipher_sec_sm4_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_sm4_clk                     )  //output
);
//===============
// demo_main_muxed_clk_for_pk_clk ctrl
//===============
assign demo_main_muxed_clk_for_pk_clk = demo_main_muxed_clk;
//===============
// demo_cipher_sec_pk_clk ctrl
//===============
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_pk_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_main_muxed_occ_clk     ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_pk_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_pk_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_pk_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_pk_clk_ea_sync     )  //output
);

assign demo_cipher_sec_pk_clk_ea_multi = demo_cipher_sec_pk_clk_ea_sync & demo_cipher_sec_pk_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_pk_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_pk_clk_ea_multi),
    .data_d     (demo_cipher_sec_pk_clk_ea_status)
);

icg u_demo_cipher_sec_pk_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_cipher_sec_pk_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_pk_clk                     )  //output
);
//===============
// demo_cipher_sec_pkdiv2_clk ctrl
//===============
clk_divider_wrap
        #(
    .PRRWIDTH        (3),
    .BYPASS          (1'b0),
    .DELAY_2          (1'b1),
    .DIV_VAL_TO_EN          (1'b0),
    .DEFAULT_VALUE   (2)
    )
u_demo_cipher_sec_pkdiv2_clk_divider_wrap(/*autoinst*/
    .test_mode              (test_mode               ), //input
    .cfg_clk                (apb_clk                 ), //input
    .cfg_rst_n              (apb_rst_n               ), //input
    .clk_div_sync_clk       (demo_main_muxed_clk_for_pk_clk), //input
    .clk_in                 (demo_main_muxed_clk_for_pk_clk), //input
    .clk_gen_rst_n          (clk_gen_rst_n                       ), //input
    .clk_div_to_en          (1'b0                  ), //input
    .clk_to_divider         (3'b0 ), //input
    .clk_divider_ea_req     (demo_cipher_sec_pkdiv2_clk_divider_ea_req ), //input
    .clk_divider            (demo_cipher_sec_pkdiv2_clk_divider           ), //input
    .clk_divider_status     (demo_cipher_sec_pkdiv2_clk_divider_status    ), //output
    .clk_divider_done       (demo_cipher_sec_pkdiv2_clk_divider_done      ), //output
    .clk_dived              (demo_cipher_sec_pkdiv2_clk_dived             )  //output
    );
clk_buf_for_occ u_demo_cipher_sec_pkdiv2_clk_buf_for_occ(/*autoinst*/
    .clkin                  (demo_cipher_sec_pkdiv2_clk_dived     ), //input
    .clkout                 (demo_cipher_sec_pkdiv2_clk_buf_out    )  //output
);
sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync(
            .clk_d                  (demo_cipher_sec_pkdiv2_clk_buf_out    ), //input
            .rst_d_n                (clk_gen_rst_n         ), //input
            .data_s                 (demo_clkgat_req          ), //input
            .data_d                 (demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync     )  //output
        );

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_cipher_sec_pkdiv2_clk_icg_sync(
    .clk_d                  (demo_cipher_sec_pkdiv2_clk_buf_out    ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_cipher_sec_pkdiv2_clk_ea          ), //input
    .data_d                 (demo_cipher_sec_pkdiv2_clk_ea_sync     )  //output
);

assign demo_cipher_sec_pkdiv2_clk_ea_multi = demo_cipher_sec_pkdiv2_clk_ea_sync & demo_cipher_sec_pkdiv2_clk_demo_clkgat_req_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_cipher_sec_pkdiv2_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_cipher_sec_pkdiv2_clk_ea_multi),
    .data_d     (demo_cipher_sec_pkdiv2_clk_ea_status)
);

icg u_demo_cipher_sec_pkdiv2_clk_icg(
    .clkin                  (demo_cipher_sec_pkdiv2_clk_buf_out    ), //input
    .enable                 (demo_cipher_sec_pkdiv2_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_cipher_sec_pkdiv2_clk                     )  //output
);
//===============
// demo_efuse_ctrl_ahb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_efuse_ctrl_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_efuse_ctrl_ahb_clk_ea          ), //input
    .data_d                 (demo_efuse_ctrl_ahb_clk_ea_sync     )  //output
);

assign demo_efuse_ctrl_ahb_clk_ea_multi = demo_efuse_ctrl_ahb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_efuse_ctrl_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_efuse_ctrl_ahb_clk_ea_multi),
    .data_d     (demo_efuse_ctrl_ahb_clk_ea_status)
);

icg u_demo_efuse_ctrl_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_efuse_ctrl_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_efuse_ctrl_ahb_clk                     )  //output
);
//===============
// demo_sec_ctrl0_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_sec_ctrl0_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_sec_ctrl0_clk_ea          ), //input
    .data_d                 (demo_sec_ctrl0_clk_ea_sync     )  //output
);

assign demo_sec_ctrl0_clk_ea_multi = demo_sec_ctrl0_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_sec_ctrl0_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_sec_ctrl0_clk_ea_multi),
    .data_d     (demo_sec_ctrl0_clk_ea_status)
);

icg u_demo_sec_ctrl0_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_sec_ctrl0_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_sec_ctrl0_clk                     )  //output
);
//===============
// demo_sec_ctrl1_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_sec_ctrl1_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_sec_ctrl1_clk_ea          ), //input
    .data_d                 (demo_sec_ctrl1_clk_ea_sync     )  //output
);

assign demo_sec_ctrl1_clk_ea_multi = demo_sec_ctrl1_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_sec_ctrl1_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_sec_ctrl1_clk_ea_multi),
    .data_d     (demo_sec_ctrl1_clk_ea_status)
);

icg u_demo_sec_ctrl1_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_sec_ctrl1_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_sec_ctrl1_clk                     )  //output
);
//===============
// demo_sec_ctrl2_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_sec_ctrl2_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_sec_ctrl2_clk_ea          ), //input
    .data_d                 (demo_sec_ctrl2_clk_ea_sync     )  //output
);

assign demo_sec_ctrl2_clk_ea_multi = demo_sec_ctrl2_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_sec_ctrl2_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_sec_ctrl2_clk_ea_multi),
    .data_d     (demo_sec_ctrl2_clk_ea_status)
);

icg u_demo_sec_ctrl2_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_sec_ctrl2_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_sec_ctrl2_clk                     )  //output
);
//===============
// demo_io_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_io_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_io_apb_clk_ea          ), //input
    .data_d                 (demo_io_apb_clk_ea_sync     )  //output
);

assign demo_io_apb_clk_ea_multi = demo_io_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_io_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_io_apb_clk_ea_multi),
    .data_d     (demo_io_apb_clk_ea_status)
);

icg u_demo_io_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_io_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_io_apb_clk                     )  //output
);
//===============
// demo_lp_bus_clk ctrl
//===============
assign demo_lp_bus_clk = demo_main_muxed_occ_clk;
//===============
// soc_32k_clk ctrl
//===============
assign soc_32k_clk = rt32k_muxed1_clk;
//===============
// misc_ahb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_misc_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (misc_ahb_clk_ea          ), //input
    .data_d                 (misc_ahb_clk_ea_sync     )  //output
);

assign misc_ahb_clk_ea_multi = misc_ahb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_misc_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (misc_ahb_clk_ea_multi),
    .data_d     (misc_ahb_clk_ea_status)
);

icg u_misc_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (misc_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (misc_ahb_clk                     )  //output
);
//===============
// dtss_dt_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_dtss_dt_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (dtss_dt_clk_ea          ), //input
    .data_d                 (dtss_dt_clk_ea_sync     )  //output
);

assign dtss_dt_clk_ea_multi = dtss_dt_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_dtss_dt_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (dtss_dt_clk_ea_multi),
    .data_d     (dtss_dt_clk_ea_status)
);

icg u_dtss_dt_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (dtss_dt_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (dtss_dt_clk                     )  //output
);
//===============
// demo_ocmem_ahb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_ocmem_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_ocmem_ahb_clk_ea          ), //input
    .data_d                 (demo_ocmem_ahb_clk_ea_sync     )  //output
);

assign demo_ocmem_ahb_clk_ea_multi = demo_ocmem_ahb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_ocmem_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_ocmem_ahb_clk_ea_multi),
    .data_d     (demo_ocmem_ahb_clk_ea_status)
);

icg u_demo_ocmem_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_ocmem_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_ocmem_ahb_clk                     )  //output
);
//===============
// demo_timer64_ahb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_timer64_ahb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_timer64_ahb_clk_ea          ), //input
    .data_d                 (demo_timer64_ahb_clk_ea_sync     )  //output
);

assign demo_timer64_ahb_clk_ea_multi = demo_timer64_ahb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer64_ahb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer64_ahb_clk_ea_multi),
    .data_d     (demo_timer64_ahb_clk_ea_status)
);

icg u_demo_timer64_ahb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_timer64_ahb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_timer64_ahb_clk                     )  //output
);
//===============
// demo_timer64_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_timer64_clk_icg_sync(
    .clk_d                  (demo_ref_clk_test_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_timer64_clk_ea          ), //input
    .data_d                 (demo_timer64_clk_ea_sync     )  //output
);

assign demo_timer64_clk_ea_multi = demo_timer64_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_timer64_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_timer64_clk_ea_multi),
    .data_d     (demo_timer64_clk_ea_status)
);

icg u_demo_timer64_clk_icg(
    .clkin                  (demo_ref_clk_test_clk     ), //input
    .enable                 (demo_timer64_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_timer64_clk                     )  //output
);
//===============
// demo_pwm_apb_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_pwm_apb_clk_icg_sync(
    .clk_d                  (demo_main_muxed_occ_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_pwm_apb_clk_ea          ), //input
    .data_d                 (demo_pwm_apb_clk_ea_sync     )  //output
);

assign demo_pwm_apb_clk_ea_multi = demo_pwm_apb_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pwm_apb_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pwm_apb_clk_ea_multi),
    .data_d     (demo_pwm_apb_clk_ea_status)
);

icg u_demo_pwm_apb_clk_icg(
    .clkin                  (demo_main_muxed_occ_clk     ), //input
    .enable                 (demo_pwm_apb_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_pwm_apb_clk                     )  //output
);
//===============
// demo_pwm_core_clk ctrl
//===============
// clk sel
clk_glitch_free_switch u_demo_pwm_core_clk_clk_glitch_free_switch(
    .test_mode  (test_mode              ),
    .rst0_n     (clk_gen_rst_n          ),
    .rst1_n     (clk_gen_rst_n          ),
    .clk0       (rtc32k_muxed_clk        ),
    .clk1       (demo_ref_clk_test_clk        ),
    .sel        (demo_pwm_core_clk_sel           ),
    .clk0_sel   (demo_pwm_core_clk_sel_clk0_sel_bf_sync  ),
    .clk1_sel   (demo_pwm_core_clk_sel_clk1_sel_bf_sync  ),
    .sel_done   (demo_pwm_core_clk_sel_done_bf_sync      ),
    .clk_out    (demo_pwm_core_clk_muxed         )
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pwm_core_clk_sel_clk0_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pwm_core_clk_sel_clk0_sel_bf_sync),
    .data_d     (demo_pwm_core_clk_sel_clk0_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b0      )
)
u_demo_pwm_core_clk_sel_clk1_sel_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pwm_core_clk_sel_clk1_sel_bf_sync),
    .data_d     (demo_pwm_core_clk_sel_clk1_sel)
);

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pwm_core_clk_sel_done_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pwm_core_clk_sel_done_bf_sync),
    .data_d     (demo_pwm_core_clk_sel_done)
);


sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b0                           ) 
)
u_demo_pwm_core_clk_icg_sync(
    .clk_d                  (demo_pwm_core_clk_muxed     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_pwm_core_clk_ea          ), //input
    .data_d                 (demo_pwm_core_clk_ea_sync     )  //output
);

assign demo_pwm_core_clk_ea_multi = demo_pwm_core_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_pwm_core_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_pwm_core_clk_ea_multi),
    .data_d     (demo_pwm_core_clk_ea_status)
);

icg u_demo_pwm_core_clk_icg(
    .clkin                  (demo_pwm_core_clk_muxed      ), //input
    .enable                 (demo_pwm_core_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_pwm_core_clk                     )  //output
);
//===============
// demo_sc_ref_clk ctrl
//===============

sync 
#(
    .D_WIDTH                (1                              ),
    .DATA_DEFAULT           (1'b1                           ) 
)
u_demo_sc_ref_clk_icg_sync(
    .clk_d                  (demo_ref_clk_test_clk     ), //input
    .rst_d_n                (clk_gen_rst_n         ), //input
    .data_s                 (demo_sc_ref_clk_ea          ), //input
    .data_d                 (demo_sc_ref_clk_ea_sync     )  //output
);

assign demo_sc_ref_clk_ea_multi = demo_sc_ref_clk_ea_sync;

sync
#(
    .D_WIDTH        (1        ),
    .DATA_DEFAULT   (1'b1      )
)
u_demo_sc_ref_clk_ea_status_sync(
    .clk_d      (apb_clk                ),
    .rst_d_n    (apb_rst_n              ),
    .data_s     (demo_sc_ref_clk_ea_multi),
    .data_d     (demo_sc_ref_clk_ea_status)
);

icg u_demo_sc_ref_clk_icg(
    .clkin                  (demo_ref_clk_test_clk     ), //input
    .enable                 (demo_sc_ref_clk_ea_multi            ), //input
    .icg_test_mode          (dft_icg_mode_root            ), //input
    .clkout                 (demo_sc_ref_clk                     )  //output
);

endmodule