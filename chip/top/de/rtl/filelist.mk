# top - RTL Filelist Dependencies

ifndef TOP_FILELIST_MK
TOP_FILELIST_MK := 1

TOP_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f

ifeq (,$(filter $(TOP_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(TOP_FILELIST)
endif

endif
