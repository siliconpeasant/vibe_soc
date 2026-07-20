#!/usr/bin/env bash
# Story-quality optimization for design-B stories260k.
# 1) baseline fixed-vs-fp32
# 2) MSE-scale pack experiment (no RTL change)
# 3) optional QAT (needs torch)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ASSETS="$ROOT/assets/weights"
SCRATCH="$ROOT/dv/sim/quality"
TESTS="$ROOT/dv/tests"
mkdir -p "$ASSETS" "$SCRATCH" "$SCRATCH/img_mse" "$SCRATCH/qat"

PY="${PYTHON:-python3}"

CKPT="$ASSETS/stories260K.bin"
TOK="$ASSETS/tok512.bin"
# Optional overrides for offline asset bootstrap (no hard-coded host paths).
CORPUS_SRC="${CORPUS_SRC:-}"
CORPUS="$SCRATCH/TinyStories-valid.txt"
SIBLING_CKPT="${SIBLING_CKPT:-}"
SIBLING_TOK="${SIBLING_TOK:-}"

if [[ ! -f "$CKPT" && -n "$SIBLING_CKPT" && -f "$SIBLING_CKPT" ]]; then
  cp -f "$SIBLING_CKPT" "$CKPT"
fi
if [[ ! -s "$TOK" && -n "$SIBLING_TOK" && -f "$SIBLING_TOK" ]]; then
  cp -f "$SIBLING_TOK" "$TOK"
fi
if [[ ! -f "$CORPUS" && -n "$CORPUS_SRC" && -f "$CORPUS_SRC" ]]; then
  cp -f "$CORPUS_SRC" "$CORPUS"
fi

echo "=== baseline (max-abs scale, sm=2, wq1 INT8) ==="
$PY "$TESTS/fixed_point_model.py" "$CKPT" --steps 64 --tokenizer "$TOK" \
  | tee "$SCRATCH/opt_baseline_64.txt"

echo "=== MSE scale (software fixed path) ==="
$PY "$TESTS/fixed_point_model.py" "$CKPT" --steps 64 --tokenizer "$TOK" --mse-scale \
  | tee "$SCRATCH/opt_mse_64.txt"

echo "=== pack images with MSE scale ==="
$PY "$TESTS/pack_stories260k.py" "$CKPT" "$SCRATCH/img_mse" --mse-scale

if $PY -c "import torch" 2>/dev/null && [[ -f "$CORPUS" ]]; then
  echo "=== QAT (hardware-format STE) ==="
  $PY "$TESTS/qat_stories260k.py" \
    --checkpoint "$CKPT" \
    --tokenizer "$TOK" \
    --corpus "$CORPUS" \
    --output "$SCRATCH/qat/stories260K_qat.bin" \
    --metrics "$SCRATCH/qat/metrics.json" \
    --steps "${QAT_STEPS:-200}" \
    --batch-size 8 \
    --seq-len 128 \
    --eval-interval 50 \
    --eval-batches 8
  $PY "$TESTS/compare_qat.py" "$CKPT" "$SCRATCH/qat/stories260K_qat.bin" \
    --tokenizer "$TOK" --steps 64 \
    | tee "$SCRATCH/opt_qat_compare_64.txt"
  $PY "$TESTS/pack_stories260k.py" "$SCRATCH/qat/stories260K_qat.bin" \
    "$SCRATCH/img_qat"
  echo "QAT images: $SCRATCH/img_qat  (use +WIMAGE/+VIMAGE for VCS)"
else
  echo "skip QAT: torch or corpus missing"
fi

echo "=== done; see $SCRATCH/opt_*.txt ==="
