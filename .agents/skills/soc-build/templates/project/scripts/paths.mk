# Central path definitions shared by every module.
# PROJECT_ROOT and MODULE_PATH are resolved by scripts/common.mk.

SOC          ?= $(PROJECT_ROOT)
export SOC
CHIP_PATH    := $(PROJECT_ROOT)/chip
IP_PATH      := $(PROJECT_ROOT)/ip
DOC_PATH     := $(PROJECT_ROOT)/doc
SCRIPTS_PATH := $(PROJECT_ROOT)/scripts

RTL_PATH     := $(MODULE_PATH)/de/rtl
TB_PATH      := $(MODULE_PATH)/dv/tb
RUN_DIR      := $(MODULE_PATH)/de/run
SIM_DIR      := $(MODULE_PATH)/dv/sim
SYN_DIR      := $(MODULE_PATH)/de/syn

SIM_FLIST    := $(SIM_DIR)/dut.f
CANONICAL_FLIST := $(SIM_DIR)/dut.canonical.f
BUILD_FINGERPRINT := $(SIM_DIR)/.build.fingerprint
REGRESS_DIR  := $(SIM_DIR)/regress
COV_DIR      := $(SIM_DIR)/coverage.vdb
COV_REPORT_DIR := $(MODULE_PATH)/dv/cov/report
