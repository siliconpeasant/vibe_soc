# opentitan_tlul - RTL Filelist Dependencies
# 用法: 在其他 Makefile 中 include $(PROJECT_ROOT)/.../de/rtl/filelist.mk

ifndef OPENTITAN_TLUL_FILELIST_MK
OPENTITAN_TLUL_FILELIST_MK := 1

# 本模块 RTL filelist（自动推导当前目录）
OPENTITAN_TLUL_FILELIST := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))filelist.f

# ---------------------------------------------------------------------------
# 依赖的子模块：取消注释并添加你依赖的其他模块的 filelist.mk
# ---------------------------------------------------------------------------

# include $(PROJECT_ROOT)/ip/digital/sub_ip/de/rtl/filelist.mk

# ---------------------------------------------------------------------------

# 注册到全局收集变量（去重：已存在则不重复添加）
ifeq (,$(filter $(OPENTITAN_TLUL_FILELIST),$(MODULE_FILELISTS)))
  MODULE_FILELISTS += $(OPENTITAN_TLUL_FILELIST)
endif

endif
