// Package compile order: IP pkg.f blocks plus chip/top package files.
// Sorted by package dependency topology.

$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/jtag_id_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/top_pkg.sv
-f $SOC/ip/digital/opentitan_rv_core_ibex/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_i2c/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_rv_dm/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_timer/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_spi/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_usbdev/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_prim/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_alert_handler/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_gpio/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_pwm/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_rv_plic/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_adc_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_hmac/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_pattgen/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_kmac/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_sysrst_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_uart/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_sensor_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_xbar/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/ibex_pmp_reset_pkg.sv
-f $SOC/ip/digital/opentitan_entropy_src/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_keymgr/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_pinmux/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_power_reset/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_lc_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_rom_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_aes/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_ast/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/scan_role_pkg.sv
-f $SOC/ip/digital/opentitan_tlul/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_csrng/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_otp_ctrl/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/testing/lc_ctrl_token_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/top_earlgrey_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/top_racl_pkg.sv
-f $SOC/ip/digital/opentitan_edn/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_otbn/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_sram_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/opentitan_flash_ctrl/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/testing/top_earlgrey_rnd_cnst_pkg.sv
