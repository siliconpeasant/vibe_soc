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
  otp_ctrl \
  rv_core_ibex \
  entropy_src \
  flash_ctrl \
  i2c \
  rv_dm \
  timer \
  spi_ot \
  usbdev \
  aes \
  prim \
  keymgr \
  lc_ctrl \
  tlul \
  alert_handler \
  power_reset \
  pinmux \
  rom_ctrl \
  csrng \
  ast \
  rv_plic \
  edn \
  otbn \
  sram_ctrl \
  gpio \
  pwm \
  adc_ctrl \
  hmac \
  pattgen \
  kmac \
  sysrst_ctrl \
  uart_ot \
  sensor_ctrl \
  xbar \
  boot \
  common
include $(addprefix $(PROJECT_ROOT)/ip/digital/,$(addsuffix /de/rtl/filelist.mk,$(NATIVE_IP_DIRS)))

MODULE_FILELISTS += $(TOP_FILELIST)

endif
