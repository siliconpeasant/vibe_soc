# opentitan_uart - RTL Filelist Dependencies

ifndef OPENTITAN_UART_FILELIST_MK
OPENTITAN_UART_FILELIST_MK := 1

OPENTITAN_UART_RTL_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
OPENTITAN_UART_FILELIST := $(OPENTITAN_UART_RTL_DIR)filelist.f

ifneq ($(OPENTITAN_UART_NO_AUTO_REGISTER),1)
include $(PROJECT_ROOT)/ip/digital/opentitan_common/de/rtl/filelist.mk
ifeq (,$(filter $(OPENTITAN_UART_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_UART_FILELIST)
endif
endif

endif
