# top - ordered RTL Filelist Dependencies

ifndef TOP_FILELIST_MK
TOP_FILELIST_MK := 1

TOP_RTL_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
TOP_FILELIST := $(TOP_RTL_DIR)filelist.f
TOP_FRAGMENT_00 := $(TOP_RTL_DIR)fragments/00_before_tlul_pkg.f
TOP_FRAGMENT_10 := $(TOP_RTL_DIR)fragments/10_after_tlul_pkg.f
TOP_FRAGMENT_20 := $(TOP_RTL_DIR)fragments/20_after_tlul_integrity.f
TOP_FRAGMENT_30 := $(TOP_RTL_DIR)fragments/30_after_tlul_fifo_assert.f
TOP_FRAGMENT_40 := $(TOP_RTL_DIR)fragments/40_after_tlul_adapters.f
TOP_FRAGMENT_50 := $(TOP_RTL_DIR)fragments/50_after_tlul_racl.f
TOP_FRAGMENT_60 := $(TOP_RTL_DIR)fragments/60_after_tlul_debug_before_uart.f
TOP_FRAGMENT_70 := $(TOP_RTL_DIR)fragments/70_after_uart.f

OPENTITAN_TLUL_NO_AUTO_REGISTER := 1
include $(PROJECT_ROOT)/ip/digital/opentitan_tlul/de/rtl/filelist.mk
OPENTITAN_UART_NO_AUTO_REGISTER := 1
include $(PROJECT_ROOT)/ip/digital/opentitan_uart/de/rtl/filelist.mk

# Preserve the known-good OpenTitan source order while sourcing TLUL/UART from native IP packages.
ifeq (,$(filter $(TOP_FRAGMENT_00),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_00)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_01_PKG),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_01_PKG)
endif

ifeq (,$(filter $(TOP_FRAGMENT_10),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_10)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_02_INTEGRITY),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_02_INTEGRITY)
endif

ifeq (,$(filter $(TOP_FRAGMENT_20),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_20)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_03_FIFO_ASSERT),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_03_FIFO_ASSERT)
endif

ifeq (,$(filter $(TOP_FRAGMENT_30),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_30)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_04_ADAPTERS),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_04_ADAPTERS)
endif

ifeq (,$(filter $(TOP_FRAGMENT_40),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_40)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_05_RACL),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_05_RACL)
endif

ifeq (,$(filter $(TOP_FRAGMENT_50),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_50)
endif

ifeq (,$(filter $(OPENTITAN_TLUL_FRAGMENT_06_DEBUG),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FRAGMENT_06_DEBUG)
endif

ifeq (,$(filter $(TOP_FRAGMENT_60),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_60)
endif

ifeq (,$(filter $(OPENTITAN_UART_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_UART_FILELIST)
endif

ifeq (,$(filter $(TOP_FRAGMENT_70),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FRAGMENT_70)
endif

endif
