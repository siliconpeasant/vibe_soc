// ============================================================================
// File Name    : demo_crg_rst_gen.v
// Description  :
// Author       : autumn
// Created On   : 2026/08/02 13:16
// Last Modified: 2026/08/02 13:16
// ----------------------------------------------------------------------------
// Date         By           Version  Description
// ----------------------------------------------------------------------------
// 2026/08/02   autumn      1.0      Initial version
// ============================================================================
module demo_crg_rst_gen(
	input           demo_rst_n,
	input           demo_por_rst_n,
	input           test_rstn,
	input           test_mode,
	// demo_lp_core_rst_n
	input           demo_lp_core_rst_n_sftrstn,
	output          demo_lp_core_rst_n,
	input           demo_lpcore_rst_n,
	input           demo_lp_cpu_rst_n,
	// demo_lp_core_demo_por_rst_n
	input           demo_lp_core_demo_por_rst_n_sftrstn,
	output          demo_lp_core_demo_por_rst_n,
	input           demo_hw_rst_n,
	// demo_uart_apb_rst_n
	input           demo_uart_apb_rst_n_sftrstn,
	output          demo_uart_apb_rst_n,
	input           demo_top_rst_n,
	// demo_uart_core_rst_n
	input           demo_uart_core_rst_n_sftrstn,
	output          demo_uart_core_rst_n,
	// demo_usim0_32k_rst_n
	input           demo_usim0_32k_rst_n_sftrstn,
	output          demo_usim0_32k_rst_n,
	input           demo_usim_rst_n,
	// demo_usim0_apb_rst_n
	input           demo_usim0_apb_rst_n_sftrstn,
	output          demo_usim0_apb_rst_n,
	// demo_gpio_apb_rst_n
	input           demo_gpio_apb_rst_n_sftrstn,
	output          demo_gpio_apb_rst_n,
	// demo_i2c_core_rst_n
	input           demo_i2c_core_rst_n_sftrstn,
	output          demo_i2c_core_rst_n,
	// demo_i2c_apb_rst_n
	input           demo_i2c_apb_rst_n_sftrstn,
	output          demo_i2c_apb_rst_n,
	// demo_usim1_32k_rst_n
	input           demo_usim1_32k_rst_n_sftrstn,
	output          demo_usim1_32k_rst_n,
	// demo_usim1_apb_rst_n
	input           demo_usim1_apb_rst_n_sftrstn,
	output          demo_usim1_apb_rst_n,
	// demo_spi_core_rst_n
	input           demo_spi_core_rst_n_sftrstn,
	output          demo_spi_core_rst_n,
	// demo_spi_apb_rst_n
	input           demo_spi_apb_rst_n_sftrstn,
	output          demo_spi_apb_rst_n,
	// demo_pmu_rst_n
	output          demo_pmu_rst_n,
	// demo_pmu_apb_rst_n
	output          demo_pmu_apb_rst_n,
	// demo_pmu_32k_rst_n
	output          demo_pmu_32k_rst_n,
	// demo_pmu_demo_por_rst_n
	output          demo_pmu_demo_por_rst_n,
	// demo_crg_apb_rst_n
	output          demo_crg_apb_rst_n,
	// demo_drx_timer_32k_rst_n
	input           demo_drx_timer_32k_rst_n_sftrstn,
	output          demo_drx_timer_32k_rst_n,
	// demo_drx_timer_phy_rst_n
	input           demo_drx_timer_phy_rst_n_sftrstn,
	output          demo_drx_timer_phy_rst_n,
	// demo_drx_timer_apb_rst_n
	input           demo_drx_timer_apb_rst_n_sftrstn,
	output          demo_drx_timer_apb_rst_n,
	// demo_rtc_apb_rst_n
	input           demo_rtc_apb_rst_n_sftrstn,
	output          demo_rtc_apb_rst_n,
	// demo_rtc_core_rst_n
	input           demo_rtc_core_rst_n_sftrstn,
	output          demo_rtc_core_rst_n,
	// demo_wdt_apb_rst_n
	input           demo_wdt_apb_rst_n_sftrstn,
	output          demo_wdt_apb_rst_n,
	// demo_wdt_rst_n
	input           demo_wdt_rst_n_sftrstn,
	output          demo_wdt_rst_n,
	// demo_timer_apb_rst_n
	input           demo_timer_apb_rst_n_sftrstn,
	output          demo_timer_apb_rst_n,
	// demo_sc_apb_rst_n
	input           demo_sc_apb_rst_n_sftrstn,
	output          demo_sc_apb_rst_n,
	// demo_sc_demo_por_rst_n
	output          demo_sc_demo_por_rst_n,
	// demo_rom_ahb_rst_n
	input           demo_rom_ahb_rst_n_sftrstn,
	output          demo_rom_ahb_rst_n,
	// demo_rdc_ahb_rst_n
	input           demo_rdc_ahb_rst_n_sftrstn,
	output          demo_rdc_ahb_rst_n,
	// demo_rdc_rst_n
	input           demo_rdc_rst_n_sftrstn,
	output          demo_rdc_rst_n,
	// demo_cipher_sec_core_rst_n
	input           demo_cipher_sec_core_rst_n_sftrstn,
	output          demo_cipher_sec_core_rst_n,
	// demo_cipher_sec_pk_rst_n
	input           demo_cipher_sec_pk_rst_n_sftrstn,
	output          demo_cipher_sec_pk_rst_n,
	// demo_efuse_ctrl_logic_rst_n
	input           demo_efuse_ctrl_logic_rst_n_sftrstn,
	output          demo_efuse_ctrl_logic_rst_n,
	// demo_efuse_ctrl_demo_por_rst_n
	output          demo_efuse_ctrl_demo_por_rst_n,
	// demo_sec_ctrl0_rst_n
	input           demo_sec_ctrl0_rst_n_sftrstn,
	output          demo_sec_ctrl0_rst_n,
	// demo_sec_ctrl1_rst_n
	output          demo_sec_ctrl1_rst_n,
	// demo_sec_ctrl2_rst_n
	input           demo_sec_ctrl2_rst_n_sftrstn,
	output          demo_sec_ctrl2_rst_n,
	// demo_io_apb_rst_n
	input           demo_io_apb_rst_n_sftrstn,
	output          demo_io_apb_rst_n,
	// misc_ahb_rst_n
	input           misc_ahb_rst_n_sftrstn,
	output          misc_ahb_rst_n,
	input           demo_soctop_rst_n,
	// dtss_dt_rst_n
	input           dtss_dt_rst_n_sftrstn,
	output          dtss_dt_rst_n,
	// demo_ocmem_ahb_rst_n
	input           demo_ocmem_ahb_rst_n_sftrstn,
	output          demo_ocmem_ahb_rst_n,
	// demo_timer64_ahb_rst_n
	input           demo_timer64_ahb_rst_n_sftrstn,
	output          demo_timer64_ahb_rst_n,
	// demo_timer64_rst_n
	input           demo_timer64_rst_n_sftrstn,
	output          demo_timer64_rst_n,
	// demo_pwm_apb_rst_n
	input           demo_pwm_apb_rst_n_sftrstn,
	output          demo_pwm_apb_rst_n,
	// demo_pwm_core_rst_n
	input           demo_pwm_core_rst_n_sftrstn,
	output          demo_pwm_core_rst_n,
	// demo_timer_cnt_rst_n
	input           demo_timer_cnt_rst_n_sftrstn,
	output          demo_timer_cnt_rst_n,
	// demo_lp_bus_rst_n
	output          demo_lp_bus_rst_n,
	// demo_top_lp_bus_rst_n
	input           demo_top_lp_bus_rst_n_sftrstn,
	output          demo_top_lp_bus_rst_n,
	input           demo_top_soc_soft_rst_n
);

//===============
// demo_lp_core_rst_n ctrl
assign demo_lp_core_rst_n = demo_rst_n & demo_lp_core_rst_n_sftrstn & demo_lpcore_rst_n & demo_lp_cpu_rst_n;

//===============
// demo_lp_core_demo_por_rst_n ctrl
assign demo_lp_core_demo_por_rst_n = demo_rst_n & demo_lp_core_demo_por_rst_n_sftrstn & demo_lpcore_rst_n & demo_hw_rst_n;

//===============
// demo_uart_apb_rst_n ctrl
assign demo_uart_apb_rst_n = demo_rst_n & demo_uart_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_uart_core_rst_n ctrl
assign demo_uart_core_rst_n = demo_rst_n & demo_uart_core_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_usim0_32k_rst_n ctrl
assign demo_usim0_32k_rst_n = demo_rst_n & demo_usim0_32k_rst_n_sftrstn & demo_usim_rst_n;

//===============
// demo_usim0_apb_rst_n ctrl
assign demo_usim0_apb_rst_n = demo_rst_n & demo_usim0_apb_rst_n_sftrstn & demo_usim_rst_n;

//===============
// demo_gpio_apb_rst_n ctrl
assign demo_gpio_apb_rst_n = demo_rst_n & demo_gpio_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_i2c_core_rst_n ctrl
assign demo_i2c_core_rst_n = demo_rst_n & demo_i2c_core_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_i2c_apb_rst_n ctrl
assign demo_i2c_apb_rst_n = demo_rst_n & demo_i2c_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_usim1_32k_rst_n ctrl
assign demo_usim1_32k_rst_n = demo_rst_n & demo_usim1_32k_rst_n_sftrstn & demo_usim_rst_n;

//===============
// demo_usim1_apb_rst_n ctrl
assign demo_usim1_apb_rst_n = demo_rst_n & demo_usim1_apb_rst_n_sftrstn & demo_usim_rst_n;

//===============
// demo_spi_core_rst_n ctrl
assign demo_spi_core_rst_n = demo_rst_n & demo_spi_core_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_spi_apb_rst_n ctrl
assign demo_spi_apb_rst_n = demo_rst_n & demo_spi_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_pmu_rst_n ctrl
assign demo_pmu_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_pmu_apb_rst_n ctrl
assign demo_pmu_apb_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_pmu_32k_rst_n ctrl
assign demo_pmu_32k_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_pmu_demo_por_rst_n ctrl
assign demo_pmu_demo_por_rst_n = demo_por_rst_n;

//===============
// demo_crg_apb_rst_n ctrl
assign demo_crg_apb_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_drx_timer_32k_rst_n ctrl
assign demo_drx_timer_32k_rst_n = demo_rst_n & demo_drx_timer_32k_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_drx_timer_phy_rst_n ctrl
assign demo_drx_timer_phy_rst_n = demo_rst_n & demo_drx_timer_phy_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_drx_timer_apb_rst_n ctrl
assign demo_drx_timer_apb_rst_n = demo_rst_n & demo_drx_timer_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_rtc_apb_rst_n ctrl
assign demo_rtc_apb_rst_n = demo_rst_n & demo_rtc_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_rtc_core_rst_n ctrl
assign demo_rtc_core_rst_n = demo_rst_n & demo_rtc_core_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_wdt_apb_rst_n ctrl
assign demo_wdt_apb_rst_n = demo_rst_n & demo_wdt_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_wdt_rst_n ctrl
assign demo_wdt_rst_n = demo_rst_n & demo_wdt_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_timer_apb_rst_n ctrl
assign demo_timer_apb_rst_n = demo_rst_n & demo_timer_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_sc_apb_rst_n ctrl
assign demo_sc_apb_rst_n = demo_rst_n & demo_sc_apb_rst_n_sftrstn & demo_hw_rst_n;

//===============
// demo_sc_demo_por_rst_n ctrl
assign demo_sc_demo_por_rst_n = demo_por_rst_n;

//===============
// demo_rom_ahb_rst_n ctrl
assign demo_rom_ahb_rst_n = demo_rst_n & demo_rom_ahb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_rdc_ahb_rst_n ctrl
assign demo_rdc_ahb_rst_n = demo_rst_n & demo_rdc_ahb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_rdc_rst_n ctrl
assign demo_rdc_rst_n = demo_rst_n & demo_rdc_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_cipher_sec_core_rst_n ctrl
assign demo_cipher_sec_core_rst_n = demo_rst_n & demo_cipher_sec_core_rst_n_sftrstn & demo_lpcore_rst_n & demo_top_rst_n;

//===============
// demo_cipher_sec_pk_rst_n ctrl
assign demo_cipher_sec_pk_rst_n = demo_rst_n & demo_cipher_sec_pk_rst_n_sftrstn & demo_lpcore_rst_n & demo_top_rst_n;

//===============
// demo_efuse_ctrl_logic_rst_n ctrl
assign demo_efuse_ctrl_logic_rst_n = demo_rst_n & demo_efuse_ctrl_logic_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_efuse_ctrl_demo_por_rst_n ctrl
assign demo_efuse_ctrl_demo_por_rst_n = demo_por_rst_n;

//===============
// demo_sec_ctrl0_rst_n ctrl
assign demo_sec_ctrl0_rst_n = demo_rst_n & demo_sec_ctrl0_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_sec_ctrl1_rst_n ctrl
assign demo_sec_ctrl1_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_sec_ctrl2_rst_n ctrl
assign demo_sec_ctrl2_rst_n = demo_rst_n & demo_sec_ctrl2_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_io_apb_rst_n ctrl
assign demo_io_apb_rst_n = demo_rst_n & demo_io_apb_rst_n_sftrstn & demo_hw_rst_n;

//===============
// misc_ahb_rst_n ctrl
assign misc_ahb_rst_n = demo_rst_n & misc_ahb_rst_n_sftrstn & demo_soctop_rst_n & demo_hw_rst_n;

//===============
// dtss_dt_rst_n ctrl
assign dtss_dt_rst_n = demo_rst_n & dtss_dt_rst_n_sftrstn & demo_hw_rst_n;

//===============
// demo_ocmem_ahb_rst_n ctrl
assign demo_ocmem_ahb_rst_n = demo_rst_n & demo_ocmem_ahb_rst_n_sftrstn & demo_hw_rst_n;

//===============
// demo_timer64_ahb_rst_n ctrl
assign demo_timer64_ahb_rst_n = demo_rst_n & demo_timer64_ahb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_timer64_rst_n ctrl
assign demo_timer64_rst_n = demo_rst_n & demo_timer64_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_pwm_apb_rst_n ctrl
assign demo_pwm_apb_rst_n = demo_rst_n & demo_pwm_apb_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_pwm_core_rst_n ctrl
assign demo_pwm_core_rst_n = demo_rst_n & demo_pwm_core_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_timer_cnt_rst_n ctrl
assign demo_timer_cnt_rst_n = demo_rst_n & demo_timer_cnt_rst_n_sftrstn & demo_top_rst_n;

//===============
// demo_lp_bus_rst_n ctrl
assign demo_lp_bus_rst_n = demo_rst_n & demo_hw_rst_n;

//===============
// demo_top_lp_bus_rst_n ctrl
assign demo_top_lp_bus_rst_n = demo_rst_n & demo_top_lp_bus_rst_n_sftrstn & demo_soctop_rst_n & demo_top_soc_soft_rst_n;


endmodule