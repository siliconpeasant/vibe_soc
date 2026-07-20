#!/usr/bin/env bash
# Fetch stories260K assets and run design-B quality diagnosis / optional QAT.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ASSETS="$ROOT/assets/weights"
SCRATCH="$ROOT/dv/sim/quality"
TESTS="$ROOT/dv/tests"
mkdir -p "$ASSETS" "$SCRATCH"

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1 && [[ -x /usr/bin/python3 ]]; then
  PY=/usr/bin/python3
fi
echo "using python: $PY ($($PY -V 2>&1))"

# Optional bootstrap sources (env overrides; no host-absolute defaults).
SIBLING_CKPT="${SIBLING_CKPT:-}"
SIBLING_TOK="${SIBLING_TOK:-}"
CORPUS_SRC="${CORPUS_SRC:-}"

CKPT="$ASSETS/stories260K.bin"
TOK="$ASSETS/tok512.bin"
CORPUS="$SCRATCH/TinyStories-valid.txt"

if [[ ! -f "$CKPT" ]]; then
  if [[ -n "$SIBLING_CKPT" && -f "$SIBLING_CKPT" ]]; then
    cp -f "$SIBLING_CKPT" "$CKPT"
    echo "copied checkpoint from SIBLING_CKPT -> $CKPT"
  else
    curl -L --fail -o "$CKPT" \
      "https://hf-mirror.com/karpathy/tinyllamas/resolve/main/stories260K/stories260K.bin" \
      || curl -L --fail -o "$CKPT" \
      "https://hf-mirror.com/karpathy/tinystories/resolve/main/stories260K.bin"
  fi
fi

if [[ ! -s "$TOK" ]]; then
  if [[ -n "$SIBLING_TOK" && -f "$SIBLING_TOK" ]]; then
    cp -f "$SIBLING_TOK" "$TOK"
  else
    curl -L --fail -o "$TOK" \
      "https://hf-mirror.com/karpathy/tinyllamas/resolve/main/stories260K/tok512.bin"
  fi
fi

if [[ ! -f "$CORPUS" && -n "$CORPUS_SRC" && -f "$CORPUS_SRC" ]]; then
  cp -f "$CORPUS_SRC" "$CORPUS"
fi

ls -la "$CKPT" "$TOK"

# Reuse prior baseline if present; always re-run experiments that can improve quality.
if [[ ! -f "$SCRATCH/baseline_32.txt" ]]; then
  echo "=== baseline 32 ==="
  $PY "$TESTS/fixed_point_model.py" "$CKPT" --steps 32 --tokenizer "$TOK" \
    | tee "$SCRATCH/baseline_32.txt"
fi
if [[ ! -f "$SCRATCH/baseline_64.txt" ]]; then
  echo "=== baseline 64 ==="
  $PY "$TESTS/fixed_point_model.py" "$CKPT" --steps 64 --tokenizer "$TOK" \
    | tee "$SCRATCH/baseline_64.txt"
fi

echo "=== software int8 expansion / clip experiments (32 steps) ==="
$PY - "$CKPT" "$TOK" 32 "$TESTS/fixed_point_model.py" <<'PY' | tee "$SCRATCH/int8_clip_experiments_32.txt"
import sys
from pathlib import Path
import importlib.util
ckpt, tok, steps, fpm_arg = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
fpm_path = Path(fpm_arg)
spec = importlib.util.spec_from_file_location("fixed_point_model", fpm_path)
fpm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fpm)
ck, dims = fpm.load(ckpt)
pieces = fpm.load_tokenizer(tok)
ref = fpm.float_trace(ck, dims, steps)
print("fp32 prefix", fpm.detokenize(pieces, ref[:12]))
cfgs = [
    ("baseline_wq1", ("wq1",), 1.0),
    ("all_wq", ("wq0","wq1","wq2","wq3","wq4"), 1.0),
    ("wq1_wk1", ("wq1","wk1"), 1.0),
    ("wq1_wv1", ("wq1","wv1"), 1.0),
    ("wq1_wo1", ("wq1","wo1"), 1.0),
    ("attn_l1", ("wq1","wk1","wv1","wo1"), 1.0),
    ("wq1_clip95", ("wq1",), 0.95),
    ("wq1_clip90", ("wq1",), 0.90),
    ("wq1_clip85", ("wq1",), 0.85),
    ("all_w4", (), 1.0),
]
best = None
for name, ops, clip in cfgs:
    toks = fpm.emulate(ck, dims, k_x=3, sm_shift=2, steps=steps,
                       int8_ops=ops, weight_clip=clip)
    pref = fpm.prefix_match_len(toks, ref)
    pos = sum(1 for a,b in zip(toks, ref) if a==b)
    print(f"{name}: prefix {pref}/{steps} pos {pos}/{steps} detok={fpm.detokenize(pieces, toks[:12])!r}")
    key = (pref, pos)
    if best is None or key > best[0]:
        best = (key, name, ops, clip, toks)
print("BEST_EXP", best[1], "prefix", best[0][0], "pos", best[0][1], "ops", best[2], "clip", best[3])
fpm.report_trail("best_exp_fixed", best[4], ref, pieces)
PY

# Try install torch into scratch if missing
export PYTHONPATH="${SCRATCH}/pydeps${PYTHONPATH:+:$PYTHONPATH}"
if ! $PY -c "import torch; print(torch.__version__)" 2>/dev/null; then
  echo "=== attempting CPU torch install into $SCRATCH/pydeps ==="
  $PY -m pip install --upgrade pip setuptools wheel -q || true
  $PY -m pip install --target "$SCRATCH/pydeps" --index-url https://download.pytorch.org/whl/cpu \
    "torch==2.6.0+cpu" 2>&1 | tee "$SCRATCH/pip_torch.txt" || \
  $PY -m pip install --target "$SCRATCH/pydeps" torch --index-url https://download.pytorch.org/whl/cpu \
    2>&1 | tee -a "$SCRATCH/pip_torch.txt" || true
fi

if $PY -c "import torch; print('torch', torch.__version__)"; then
  if [[ -f "$CORPUS" ]]; then
    QAT_OUT="$SCRATCH/stories260K_qat.bin"
    echo "=== QAT (small CPU steps) ==="
    $PY "$TESTS/qat_stories260k.py" "$CKPT" "$TOK" "$CORPUS" "$QAT_OUT" \
      --steps "${QAT_STEPS:-80}" --batch-size 4 --seq-len 64 --max-chars 200000 \
      --eval-interval 20 --threads 8 --metrics "$SCRATCH/qat_metrics.json" \
      | tee "$SCRATCH/qat_train.txt"
    $PY "$TESTS/compare_qat.py" "$CKPT" "$QAT_OUT" --tokenizer "$TOK" --steps 32 \
      | tee "$SCRATCH/qat_vs_orig_fp32_32.txt"
    $PY "$TESTS/compare_qat.py" "$CKPT" "$QAT_OUT" --tokenizer "$TOK" --steps 64 \
      | tee "$SCRATCH/qat_vs_orig_fp32_64.txt"
    $PY "$TESTS/pack_stories260k.py" "$QAT_OUT" "$SCRATCH/img_qat"
  else
    echo "WARN: no corpus for QAT"
  fi
else
  echo "WARN: torch still unavailable; skip QAT"
fi

echo "done"
ls -la "$SCRATCH"
