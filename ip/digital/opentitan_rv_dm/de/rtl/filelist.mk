# opentitan_rv_dm - RTL Filelist Dependencies

MODULE_RTL_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
MODULE_FILELIST := $(MODULE_RTL_DIR)filelist.f
MODULE_PKG_FILELIST := $(MODULE_RTL_DIR)pkg.f
AUTO_REGISTER_FILELISTS ?= 1

ifeq ($(AUTO_REGISTER_FILELISTS),1)
ifeq (,$(filter $(MODULE_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS := $(MODULE_FILELISTS) $(MODULE_FILELIST)
endif
endif
