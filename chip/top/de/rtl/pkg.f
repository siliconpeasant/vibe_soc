// Package compile order: IP pkg.f blocks plus chip/top package files.
// Sorted by package dependency topology.

$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/jtag_id_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/top_pkg.sv
-f $SOC/ip/digital/rv_core_ibex/de/rtl/pkg.f
-f $SOC/ip/digital/i2c/de/rtl/pkg.f
-f $SOC/ip/digital/rv_dm/de/rtl/pkg.f
-f $SOC/ip/digital/timer/de/rtl/pkg.f
-f $SOC/ip/digital/spi_ot/de/rtl/pkg.f
-f $SOC/ip/digital/usbdev/de/rtl/pkg.f
-f $SOC/ip/digital/prim/de/rtl/pkg.f
-f $SOC/ip/digital/alert_handler/de/rtl/pkg.f
-f $SOC/ip/digital/gpio/de/rtl/pkg.f
-f $SOC/ip/digital/pwm/de/rtl/pkg.f
-f $SOC/ip/digital/rv_plic/de/rtl/pkg.f
-f $SOC/ip/digital/adc_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/hmac/de/rtl/pkg.f
-f $SOC/ip/digital/pattgen/de/rtl/pkg.f
-f $SOC/ip/digital/kmac/de/rtl/pkg.f
-f $SOC/ip/digital/sysrst_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/uart_ot/de/rtl/pkg.f
-f $SOC/ip/digital/sensor_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/xbar/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/ibex_pmp_reset_pkg.sv
-f $SOC/ip/digital/entropy_src/de/rtl/pkg.f
-f $SOC/ip/digital/keymgr/de/rtl/pkg.f
-f $SOC/ip/digital/pinmux/de/rtl/pkg.f
-f $SOC/ip/digital/power_reset/de/rtl/pkg.f
-f $SOC/ip/digital/lc_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/rom_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/aes/de/rtl/pkg.f
-f $SOC/ip/digital/ast/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/scan_role_pkg.sv
-f $SOC/ip/digital/tlul/de/rtl/pkg.f
-f $SOC/ip/digital/csrng/de/rtl/pkg.f
-f $SOC/ip/digital/otp_ctrl/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/testing/lc_ctrl_token_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/top_earlgrey_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/top_racl_pkg.sv
-f $SOC/ip/digital/edn/de/rtl/pkg.f
-f $SOC/ip/digital/otbn/de/rtl/pkg.f
-f $SOC/ip/digital/sram_ctrl/de/rtl/pkg.f
-f $SOC/ip/digital/flash_ctrl/de/rtl/pkg.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/testing/top_earlgrey_rnd_cnst_pkg.sv
