# top - RTL Filelist Dependencies

ifndef TOP_FILELIST_MK
TOP_FILELIST_MK := 1

ifeq ($(OT_VENDOR),1)
TOP_FILELIST := $(RTL_PATH)/$(or $(OT_FILELIST_NAME),filelist.opentitan.f)
else
TOP_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f

include $(PROJECT_ROOT)/chip/core/de/rtl/filelist.mk
include $(PROJECT_ROOT)/chip/bus/de/rtl/filelist.mk
include $(PROJECT_ROOT)/ip/digital/uart/de/rtl/filelist.mk
endif

ifeq (,$(filter $(TOP_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FILELIST)
endif

endif
