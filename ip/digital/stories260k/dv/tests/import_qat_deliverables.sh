#!/usr/bin/env bash
# Import GPU QAT deliverables into design-B module and refresh TB golden.
set -euo pipefail
MODULE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="${QAT_SRC:-/mnt/hgfs/EDA_PACKAGE/share/stories260k/out_qat}"
PY="${PYTHON:-python3}"

echo "QAT_SRC=$SRC"
test -f "$SRC/stories260K_qat.bin"
test -f "$SRC/img/wbuf.hex"
test -f "$SRC/img/vecbuf.hex"
test -f "$SRC/metrics.json"

mkdir -p "$MODULE_ROOT/dv/sim/quality/qat" "$MODULE_ROOT/dv/sim/img" \
  "$MODULE_ROOT/assets/weights"

cp -f "$SRC/stories260K_qat.bin" "$MODULE_ROOT/assets/weights/"
cp -f "$SRC/img/wbuf.hex" "$SRC/img/vecbuf.hex" "$MODULE_ROOT/dv/sim/img/"
cp -f "$SRC/metrics.json" "$MODULE_ROOT/dv/sim/quality/qat/"
cp -f "$SRC/qat_train_metrics.json" "$MODULE_ROOT/dv/sim/quality/qat/" 2>/dev/null || true
cp -f "$SRC/prefix_alphas.json" "$MODULE_ROOT/dv/sim/quality/qat/" 2>/dev/null || true
cp -f "$SRC/README.md" "$MODULE_ROOT/dv/sim/quality/qat/" 2>/dev/null || true

"$PY" - "$MODULE_ROOT" <<'PY'
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1])
metrics = json.loads((root / "dv/sim/quality/qat/metrics.json").read_text(encoding="utf-8"))
toks = metrics["evaluation"]["64"]["qat_fixed"]["tokens"][:64]
tb = root / "dv/tb/tb_stories260k.sv"
text = tb.read_text(encoding="utf-8")
lines = []
for i in range(0, 64, 2):
    lines.append(
        f"                {i:2d}: golden_token = 9'd{toks[i]};  "
        f"{i+1:2d}: golden_token = 9'd{toks[i+1]};"
    )
block = "\n".join(lines)
new, n = re.subn(
    r"(case \(idx\)\n)(.*?)(\n                default: golden_token = 9'd0;)",
    r"\1" + block + r"\3",
    text,
    count=1,
    flags=re.S,
)
assert n == 1, "failed to patch golden_token"
tb.write_text(new, encoding="utf-8")
pref = metrics["evaluation"]["64"]["qat_fixed"]["prefix_match_vs_original_fp32"]
detok = metrics["evaluation"]["64"]["qat_fixed"]["detokenized"]
print(f"imported QAT; prefix_match={pref}/64")
print("opening:", detok[:200])
(root / "dv/sim/quality/qat/IMPORT_OK.txt").write_text(
    f"prefix_match={pref}/64\nopening={detok[:300]}\n", encoding="utf-8"
)
PY

echo "done: images -> dv/sim/img, golden updated"
