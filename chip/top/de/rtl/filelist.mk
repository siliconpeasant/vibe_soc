# top - ordered RTL Filelist Dependencies

ifndef TOP_FILELIST_MK
TOP_FILELIST_MK := 1

TOP_RTL_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
TOP_FILELIST := $(TOP_RTL_DIR)filelist.f
TOP_PKG_FILELIST := $(TOP_RTL_DIR)pkg.f

# filelist.mk owns the top compile assembly order:
# 1. dependency-sorted packages, 2. inherited IP RTL/model filelists, 3. top RTL tail.
MODULE_FILELISTS += $(TOP_PKG_FILELIST)

# Child filelist.mk files auto-register their own filelist.f into MODULE_FILELISTS.
AUTO_REGISTER_FILELISTS := 1
NATIVE_IP_DIRS := \
  opentitan_otp_ctrl \
  opentitan_rv_core_ibex \
  opentitan_entropy_src \
  opentitan_flash_ctrl \
  opentitan_i2c \
  opentitan_rv_dm \
  opentitan_timer \
  opentitan_spi \
  opentitan_usbdev \
  opentitan_aes \
  opentitan_prim \
  opentitan_keymgr \
  opentitan_lc_ctrl \
  opentitan_tlul \
  opentitan_alert_handler \
  opentitan_power_reset \
  opentitan_pinmux \
  opentitan_rom_ctrl \
  opentitan_csrng \
  opentitan_ast \
  opentitan_rv_plic \
  opentitan_edn \
  opentitan_otbn \
  opentitan_sram_ctrl \
  opentitan_gpio \
  opentitan_pwm \
  opentitan_adc_ctrl \
  opentitan_hmac \
  opentitan_pattgen \
  opentitan_kmac \
  opentitan_sysrst_ctrl \
  opentitan_uart \
  opentitan_sensor_ctrl \
  opentitan_xbar \
  opentitan_boot \
  opentitan_common
include $(addprefix $(PROJECT_ROOT)/ip/digital/,$(addsuffix /de/rtl/filelist.mk,$(NATIVE_IP_DIRS)))

MODULE_FILELISTS += $(TOP_FILELIST)

endif
