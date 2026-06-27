// chip/top ordered RTL fragment.
// Assembled by chip/top/de/rtl/filelist.mk.

// Canonical OpenTitan Earlgrey DUT RTL/model filelist for vibe_soc chip/top.
// Source order is frozen from the known-good FuseSoC top_earlgrey_chip_sim dependency graph.
// DV/UVM/DPI/SVA/bind sources live in chip/top/dv/tb/filelist.f.

+incdir+$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/aes/model
+incdir+$SOC/chip/top/de/rtl/vendor/opentitan/hw/dv/sv/dv_utils

$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/jtag_id_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/top_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_macro_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/entropy_src/rtl/entropy_src_ack_sm_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/entropy_src/rtl/entropy_src_main_sm_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/flash_ctrl/rtl/flash_ctrl_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/i2c/rtl/i2c_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/rv_dm/rtl/jtag_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/otp_macro/rtl/otp_macro_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/rv_timer/rtl/rv_timer_reg_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/spi_device/rtl/spi_device_reg_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/spi_device/rtl/spi_device_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/usbdev/rtl/usbdev_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/aes/model/crypto.c
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/aes/model/aes.c
-f $SOC/ip/digital/opentitan_common/de/rtl/filelist.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/autogen/top_earlgrey_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/scan_role_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_icache.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_tracer_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_tracer.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/rv_core_ibex/rtl/rv_core_ibex_pkg.sv
-f $SOC/ip/digital/opentitan_common/de/rtl/fragments/10_top00_prim_block1.f
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/physical_pads.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/top_earlgrey/rtl/ibex_pmp_reset_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/entropy_src/rtl/entropy_src_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/keymgr/rtl/keymgr_reg_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/keymgr/rtl/keymgr_pkg.sv
$SOC/chip/top/de/rtl/vendor/opentitan/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv
-f $SOC/ip/digital/opentitan_common/de/rtl/fragments/20_top00_prim_block2.f
