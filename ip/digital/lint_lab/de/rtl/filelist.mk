LINT_LAB_RTL_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
RTL_SRCS += $(LINT_LAB_RTL_DIR)/lint_lab.v
