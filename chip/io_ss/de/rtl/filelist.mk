# io_ss - RTL Filelist Dependencies
ifndef IO_SS_FILELIST_MK
IO_SS_FILELIST_MK := 1

IO_SS_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f

ifeq (,$(filter $(IO_SS_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(IO_SS_FILELIST)
endif

endif
