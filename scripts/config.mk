# Project-wide build defaults. Override from the command line or scripts/local.mk.

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c
TMPDIR := /tmp
export TMPDIR
PYTHON3 ?= $(shell for name in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do \
  path=$$(command -v $$name 2>/dev/null); \
  if [ -n "$$path" ] && env -u PYTHONHOME -u PYTHONPATH TMPDIR=/tmp $$path \
    -c 'import sys,tempfile; assert sys.version_info >= (3,8); assert tempfile.gettempdir() == "/tmp"' \
    >/dev/null 2>&1; then echo $$path; break; fi; \
done)
PYTHON_RUN := env -u PYTHONHOME -u PYTHONPATH TMPDIR=$(TMPDIR) $(PYTHON3)

ifeq ($(strip $(PYTHON3)),)
  $(error Python 3.8 or newer is required for build automation)
endif

SUPPORTED_SIMULATORS := iverilog verilator vcs xcelium

SIMULATOR ?= vcs
LINT_TOOL ?= verilator
TIMESCALE ?= 1ns/1ps
SEED      ?= 1
TEST      ?= default
GUI       ?= 0
FSDB      ?= 0
PARTCOMP  ?= 1
FORCE     ?= 0
COVERAGE  ?= 0

REGRESS_TESTS      ?= default
REGRESS_SEEDS      ?= 1
REGRESS_JOBS       ?= 1
REGRESS_TEST_FILE  ?= $(MODULE_PATH)/dv/tests/tests.list
REGRESS_PASS_REGEX ?=

COV_METRICS ?= line+branch+cond+tgl+fsm+assert

IVERILOG ?= iverilog
VVP      ?= vvp
IVERILOG_FLAGS ?= -g2012
VVP_FLAGS      ?=
VERILATOR_FLAGS ?= -Wall
VLOG_FLAGS      ?= +systemverilogext+.sv+.svi+.svh+.v \
                   -extinclude \
                   +libext+.vlib+.v+.sv+.svi+.svh+.vt+.vp+.defs \
                   +vcs+lic+wait +lint=TFIPC-L \
                   +define+VCS +define+RTL_SIM +define+UVM1P2 \
                   -sverilog -nc -kdb -full64 -lca \
                   -xlrm floating_pnt_constraint
VCS_ELAB_FLAGS  ?= +vcs+lic+wait +notimingcheck -kdb -full64 -lca \
                   -xlrm floating_pnt_constraint \
                   +vcs+initreg+random -debug_access+pp
VCS_SIM_FLAGS   ?= +vcs+lic+wait +ntb_random_seed=$(SEED) +vcs+flush+log +vcs+flush+dump
VCS_HW_ROOT     ?= $(PROJECT_ROOT)
VCS_UVM_HOME    ?= $(VCS_HOME)/etc/uvm-1.2
VCS_DW_SIM_PATH ?=
XCELIUM_FLAGS   ?= -64bit -sv -access +rwc
XCELIUM_SIM_FLAGS ?= -seed $(SEED)

USER_COMPILE_FLAGS ?=
USER_SIM_FLAGS     ?=
VERDI_FLAGS        ?= -sverilog +libext+.v+.sv+.svh

# Optional per-user settings. This file is intentionally not required.
-include $(PROJECT_ROOT)/scripts/local.mk

# Support relocatable user-local Icarus installs. Some packaged iverilog
# binaries keep a compiled-in /usr/lib64/ivl backend path even when the real
# backend lives next to the binary under ~/.local/usr/lib64/ivl.
IVERILOG_REAL := $(realpath $(shell command -v $(IVERILOG) 2>/dev/null))
IVERILOG_PREFIX := $(patsubst %/bin/,%,$(dir $(IVERILOG_REAL)))
IVERILOG_BACKEND ?= $(firstword \
  $(wildcard $(IVERILOG_PREFIX)/lib64/ivl) \
  $(wildcard $(IVERILOG_PREFIX)/lib/ivl))
ifneq ($(wildcard $(IVERILOG_BACKEND)/ivlpp),)
  ifeq (,$(findstring -B,$(IVERILOG_FLAGS)))
    IVERILOG_FLAGS += -B $(IVERILOG_BACKEND)
  endif
  ifeq (,$(findstring -M,$(VVP_FLAGS)))
    VVP_FLAGS += -M $(IVERILOG_BACKEND)
  endif
endif

# Make/MCP child processes do not always inherit shell license variables.
export SNPSLMD_LICENSE_FILE LM_LICENSE_FILE CDS_LIC_FILE

ifeq (,$(filter $(SIMULATOR),$(SUPPORTED_SIMULATORS)))
  $(error Unsupported SIMULATOR '$(SIMULATOR)'; choose one of: $(SUPPORTED_SIMULATORS))
endif
