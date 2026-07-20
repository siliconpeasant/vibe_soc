# stories260k module
PROJECT_ROOT ?= $(shell cd ../../.. && pwd -P)
MODULE_NAME   = stories260k
MODULE_ROOT   := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
# Absolute paths remain valid in per-test run directories created by soc_sim.
USER_SIM_FLAGS += +WIMAGE=$(MODULE_ROOT)/dv/sim/img/wbuf.hex
USER_SIM_FLAGS += +VIMAGE=$(MODULE_ROOT)/dv/sim/img/vecbuf.hex
# TOKEN_IN seed: 1=BOS Lily; 291=The; 326=Tim; 385=One day
SEED_TOKEN ?= 1
USER_SIM_FLAGS += +SEED_TOKEN=$(SEED_TOKEN)
# Selected GPU QAT deliverables (share path may be refreshed by external training).
QAT_SRC ?= /mnt/hgfs/EDA_PACKAGE/share/stories260k/out_qat
include $(PROJECT_ROOT)/scripts/common.mk

# Import selected QAT bin/img/metrics and refresh TB golden (Python shutil; no torch).
# Prefer PYTHON if set, else python3 on PATH (no host-absolute tool paths).
PY ?= python3

.PHONY: import-qat
import-qat:
	@$(PY) $(MODULE_ROOT)/dv/tests/reimport_qat_offline.py \
		--src $(QAT_SRC) --module $(MODULE_ROOT)

.PHONY: detok-long512
detok-long512:
	@$(PY) $(MODULE_ROOT)/dv/tests/detok_long512_qat.py

# Refresh share QAT before compile/sim so updated training is picked up.
# detok-long512 runs after import so latest long512 tokens become story text.
comp: import-qat detok-long512
sim: import-qat detok-long512

.PHONY: story-quality
story-quality:
	@QAT_STEPS=$${QAT_STEPS:-0} $(PY) $(MODULE_ROOT)/dv/tests/solve_fragmentation.py
