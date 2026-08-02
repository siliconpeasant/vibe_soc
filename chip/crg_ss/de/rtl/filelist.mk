# crg_ss - RTL Filelist Dependencies
ifndef CRG_SS_FILELIST_MK
CRG_SS_FILELIST_MK := 1
CRG_SS_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f
# Note: do not include soc_ip_common here — generator port names differ.
ifeq (,$(filter $(CRG_SS_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(CRG_SS_FILELIST)
endif
endif
