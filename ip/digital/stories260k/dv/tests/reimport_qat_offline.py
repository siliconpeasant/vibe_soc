#!/usr/bin/env python3
"""Offline QAT re-import for stories260k (no make / no MCP required).

Default: import the *selected* main QAT deliverable from share out_qat:
  stories260K_qat.bin + pre-packed img/ + prefix_alphas.json + metrics.json
  and patch TB golden from metrics evaluation.64.qat_fixed tokens.

Optional --use-long-best: pack long_qat/stories260K_qat_long_best.bin instead
(share metrics mark long_qat as selected=false; not recommended for golden).

Usage:
  python3 reimport_qat_offline.py --src /mnt/hgfs/EDA_PACKAGE/share/stories260k/out_qat \\
      --module /path/to/ip/digital/stories260k
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> str:
    if not path.is_file():
        return f"MISSING {path}"
    st = path.stat()
    return f"{path} size={st.st_size} mtime={st.st_mtime:.0f} md5={md5(path)}"


def compare(src: Path, mod: Path) -> None:
    pairs = [
        (src / "img/wbuf.hex", mod / "dv/sim/img/wbuf.hex"),
        (src / "img/vecbuf.hex", mod / "dv/sim/img/vecbuf.hex"),
        (src / "stories260K_qat.bin", mod / "assets/weights/stories260K_qat.bin"),
        (src / "long_qat/stories260K_qat_long_best.bin",
         mod / "assets/weights/stories260K_qat.bin"),
    ]
    print("=== compare ===")
    for a, b in pairs:
        print("SRC ", file_info(a))
        print("MOD ", file_info(b))
        if a.is_file() and b.is_file():
            same = md5(a) == md5(b)
            print("  same_md5=" + str(same))
        print()
    long_img = list((src / "long_qat").glob("**/*.hex")) if (src / "long_qat").is_dir() else []
    print(f"long_qat packed hex files: {len(long_img)}")
    for p in (src / "prefix_alphas.json", src / "prefix_alphas_long.json"):
        print(file_info(p))


def patch_tb_golden(tb: Path, tokens: list[int]) -> None:
    assert len(tokens) >= 64, "need 64 golden tokens"
    toks = tokens[:64]
    lines = []
    for i in range(0, 64, 2):
        lines.append(
            f"                {i:2d}: golden_token = 9'd{toks[i]};  "
            f"{i+1:2d}: golden_token = 9'd{toks[i+1]};"
        )
    block = "\n".join(lines)
    text = tb.read_text(encoding="utf-8")
    new, n = re.subn(
        r"(case \(idx\)\n)(.*?)(\n                default: golden_token = 9'd0;)",
        r"\1" + block + r"\3",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"failed to patch golden_token in {tb}")
    tb.write_text(new, encoding="utf-8")


def run_pack(py: str, pack_py: Path, ckpt: Path, out_img: Path,
             alphas: Path | None = None) -> None:
    """Pack WBUF/VECBUF. Prefer no alphas so hex matches fixed_point_model
    defaults used for TB golden (clip=1.0). Optional alphas for experiments."""
    out_img.mkdir(parents=True, exist_ok=True)
    cmd = [py, str(pack_py), str(ckpt), str(out_img)]
    if alphas is not None and Path(alphas).is_file():
        cmd.extend(["--alphas", str(alphas)])
    print("RUN", " ".join(cmd))
    subprocess.check_call(cmd)


def run_fixed(py: str, fixed_py: Path, ckpt: Path, tok: Path, alphas_note: Path,
              out_txt: Path, steps: int = 64) -> list[int]:
    """Run fixed_point_model. Note: CLI has no --alphas; packing alphas are
    applied at pack time. Emulator uses default weight_clip=1.0 per op unless
    metrics already provide golden tokens."""
    cmd = [py, str(fixed_py), str(ckpt), "--steps", str(steps),
           "--tokenizer", str(tok)]
    print("RUN", " ".join(cmd), f"(alphas note: {alphas_note})")
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    out_txt.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    print(proc.stdout)
    # Prefer tokens from metrics when available; parser of fixed output is best-effort.
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, required=True,
                    help="share out_qat directory")
    ap.add_argument("--module", type=Path, required=True,
                    help="module root ip/digital/stories260k")
    ap.add_argument("--use-long-best", action="store_true",
                    help="import long_qat best.bin and re-pack (selected=false)")
    ap.add_argument("--compare-only", action="store_true")
    ap.add_argument("--python", default="")
    args = ap.parse_args()

    src: Path = args.src
    mod: Path = args.module
    py = args.python or sys.executable

    compare(src, mod)
    if args.compare_only:
        return 0

    qat_dir = mod / "dv/sim/quality/qat"
    img_dir = mod / "dv/sim/img"
    wdir = mod / "assets/weights"
    qat_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    wdir.mkdir(parents=True, exist_ok=True)

    # prefix_alphas.json is optional. Silicon TB golden uses clip=1.0 / no alphas.
    alphas = src / "prefix_alphas.json"
    if alphas.is_file():
        shutil.copy2(alphas, qat_dir / "prefix_alphas.json")
    if (src / "prefix_alphas_long.json").is_file():
        shutil.copy2(src / "prefix_alphas_long.json",
                     qat_dir / "prefix_alphas_long.json")

    metrics_src = src / "metrics.json"
    if metrics_src.is_file():
        shutil.copy2(metrics_src, qat_dir / "metrics.json")
    if (src / "qat_train_metrics.json").is_file():
        shutil.copy2(src / "qat_train_metrics.json",
                     qat_dir / "qat_train_metrics.json")
    if (src / "long_qat/metrics.json").is_file():
        shutil.copy2(src / "long_qat/metrics.json",
                     qat_dir / "long_qat_metrics.json")
    # Copy fixed/story reports if present (P0 hard 64/128/256/512 delivery).
    for name in ("README.md", "fixed_64.txt", "fixed_128.txt", "fixed_256.txt",
                 "fixed_512.txt", "story_64.txt", "story_128.txt",
                 "story_256.txt", "story_512.txt", "compare_64.txt",
                 "compare_128.txt"):
        p = src / name
        if p.is_file():
            shutil.copy2(p, qat_dir / name)

    pack_py = mod / "dv/tests/pack_stories260k.py"
    fixed_py = mod / "dv/tests/fixed_point_model.py"
    tok = wdir / "tok512.bin"
    tb = mod / "dv/tb/tb_stories260k.sv"

    if args.use_long_best:
        ckpt_src = src / "long_qat/stories260K_qat_long_best.bin"
        if not ckpt_src.is_file():
            raise SystemExit(f"missing {ckpt_src}")
        shutil.copy2(ckpt_src, wdir / "stories260K_qat.bin")
        print("WARNING: using long_best (metrics selected=false)")
    else:
        ckpt_src = src / "stories260K_qat.bin"
        if not ckpt_src.is_file():
            raise SystemExit(f"missing {ckpt_src}")
        shutil.copy2(ckpt_src, wdir / "stories260K_qat.bin")

    # Always re-pack with the module packer so INT8 layout (v1.7 high-halves)
    # matches current RTL. Do not apply share alphas here: golden is
    # generated from fixed_point_model defaults (clip=1.0).
    run_pack(py, pack_py, wdir / "stories260K_qat.bin", img_dir, alphas=None)

    # Golden tokens from the RTL-exact fixed model (design-B defaults).
    sys.path.insert(0, str(mod / "dv/tests"))
    import fixed_point_model as fpm  # noqa: WPS433
    ckpt_path = wdir / "stories260K_qat.bin"
    ck, dims = fpm.load(str(ckpt_path))
    tokens = list(fpm.emulate(
        ck, dims,
        k_x=fpm.DEFAULT_K_X,
        sm_shift=fpm.DEFAULT_SM_SHIFT,
        steps=64,
        int8_ops=fpm.DEFAULT_INT8_OPS,
    ))
    pieces = fpm.load_tokenizer(str(tok)) if tok.is_file() else None
    detok = fpm.detokenize(pieces, tokens) if pieces is not None else ""
    ref = fpm.float_trace(ck, dims, 64)
    pref = fpm.prefix_match_len(tokens, ref)

    patch_tb_golden(tb, tokens)
    (qat_dir / "fixed64_new.txt").write_text(
        "tokens_64 = " + json.dumps(tokens) + "\n"
        f"prefix_match={pref}\n"
        f"detokenized={detok!r}\n",
        encoding="utf-8",
    )
    (qat_dir / "IMPORT_OK.txt").write_text(
        f"reimport ok; use_long_best={args.use_long_best}\n"
        f"prefix_match={pref}\n"
        f"opening={detok[:300]}\n"
        f"wbuf={file_info(img_dir / 'wbuf.hex')}\n"
        f"vecbuf={file_info(img_dir / 'vecbuf.hex')}\n"
        f"ckpt={file_info(wdir / 'stories260K_qat.bin')}\n",
        encoding="utf-8",
    )
    print("TB golden updated:", tb)
    print("tokens[:8] =", tokens[:8])
    print("tokens[24:32] =", tokens[24:32])
    print("opening:", detok[:200])
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
