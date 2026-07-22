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

# DEC_CFG profiles (CSR 0x038). Per-field overrides still work via REP_PEN/ADAPT_EN/NOREP_WIN.
#   golden — R4 bit-exact (default)
#   mid    — light anti-repeat, better 256/512 balance
#   long   — measured 512 anti-loop (rep_pen=64, adapt, norep=12)
DEC_PROFILE ?= golden
ifeq ($(DEC_PROFILE),golden)
  REP_PEN   ?= 32
  ADAPT_EN  ?= 0
  NOREP_WIN ?= 0
else ifeq ($(DEC_PROFILE),mid)
  REP_PEN   ?= 48
  ADAPT_EN  ?= 0
  NOREP_WIN ?= 0
else ifeq ($(DEC_PROFILE),long)
  REP_PEN   ?= 64
  ADAPT_EN  ?= 1
  NOREP_WIN ?= 12
else
  $(error unknown DEC_PROFILE=$(DEC_PROFILE); use golden|mid|long)
endif
USER_SIM_FLAGS += +DEC_PROFILE=$(DEC_PROFILE)
USER_SIM_FLAGS += +REP_PEN=$(REP_PEN)
USER_SIM_FLAGS += +ADAPT_EN=$(ADAPT_EN)
USER_SIM_FLAGS += +NOREP_WIN=$(NOREP_WIN)

# Selected GPU QAT deliverables (share path may be refreshed by external training).
# R5 formal deliver_here_r5 not promoted (no hard_pass). Temporary best-effort:
# B0 blend R4↔A1325 alpha=0.25 (only fails R5 gate: 512 repeat4 slightly high).
QAT_SRC ?= /mnt/hgfs/EDA_PACKAGE/share/stories260k/p0_qat_v17/deliver_here_r5_best_effort
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

# Score a QAT bin with multi-length + fragmentation gates (R5 selector).
# Usage: make score-qat CKPT=path/to/stories260K_qat.bin [STEPS_LIST="64 128 256 512"]
.PHONY: score-qat
score-qat:
	@test -n "$(CKPT)" || (echo "usage: make score-qat CKPT=<bin>" >&2; exit 2)
	@$(PY) $(MODULE_ROOT)/dv/tests/score_qat_checkpoint.py \
		--checkpoint $(CKPT) \
		--tokenizer $(MODULE_ROOT)/assets/weights/tok512.bin \
		--teacher $(MODULE_ROOT)/assets/weights/stories260K.bin \
		--out-dir $(MODULE_ROOT)/dv/sim/quality/score_qat \
		$(if $(STEPS_LIST),--steps $(STEPS_LIST),)

# Convenience long-story sim profiles (VCS via normal sim target vars).
.PHONY: sim-long-golden sim-long-mid sim-long-anti
sim-long-golden:
	@$(MAKE) sim TEST=long512 TOP_MODULE=tb_stories260k_long512 DEC_PROFILE=golden
sim-long-mid:
	@$(MAKE) sim TEST=long512 TOP_MODULE=tb_stories260k_long512 DEC_PROFILE=mid
sim-long-anti:
	@$(MAKE) sim TEST=long512 TOP_MODULE=tb_stories260k_long512 DEC_PROFILE=long