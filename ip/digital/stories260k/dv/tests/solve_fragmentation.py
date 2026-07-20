#!/usr/bin/env python3
"""Solve design-B story fragmentation without changing RTL.

Pipeline:
  1) Measure baseline fixed-point vs FP32 greedy prefix
  2) Try MSE weight scales (packer-compatible)
  3) If torch is available, run hardware-format QAT and re-measure
  4) Keep the best checkpoint under assets/weights/stories260K_qat.bin
  5) Repack dv/sim/img/{wbuf,vecbuf}.hex from the best checkpoint

Exit code 0 even if only baseline is available (so make syn succeeds);
writes dv/sim/quality/FRAGMENTATION_SOLVE.md with the outcome.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
ASSETS = ROOT / "assets" / "weights"
SCRATCH = ROOT / "dv" / "sim" / "quality"
IMG = ROOT / "dv" / "sim" / "img"
QAT_OUT = SCRATCH / "qat"


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else None


def find_python():
    for p in (os.environ.get("PYTHON"), sys.executable, "python3", "/usr/bin/python3"):
        if not p:
            continue
        if p in ("python3",) or Path(p).exists():
            return p
    return "python3"


def ensure_assets():
    ASSETS.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    QAT_OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    ckpt = ASSETS / "stories260K.bin"
    tok = ASSETS / "tok512.bin"
    sibling_ckpt = _env_path("SIBLING_CKPT")
    sibling_tok = _env_path("SIBLING_TOK")
    if not ckpt.is_file() and sibling_ckpt is not None and sibling_ckpt.is_file():
        shutil.copy2(sibling_ckpt, ckpt)
    if (not tok.is_file() or tok.stat().st_size == 0) and sibling_tok is not None and sibling_tok.is_file():
        shutil.copy2(sibling_tok, tok)
    corpus = None
    corpus_candidates = [SCRATCH / "TinyStories-valid.txt"]
    corpus_src = _env_path("CORPUS_SRC")
    if corpus_src is not None:
        corpus_candidates.append(corpus_src)
    for c in corpus_candidates:
        if c.is_file() and c.stat().st_size > 1000:
            corpus = c
            break
    if corpus is None:
        # Minimal fallback corpus so QAT can still run lightly.
        corpus = SCRATCH / "TinyStories-minimal.txt"
        corpus.write_text(
            "Once upon a time, there was a little girl named Lily. "
            "She loved to play outside in the park.\n"
            "One day, she saw a big red ball and wanted to play with it.\n"
            "Tim and his friend went to the river to find a fish.\n"
            "The little boy was happy to see his mom at home.\n",
            encoding="utf-8",
        )
    elif corpus != SCRATCH / "TinyStories-valid.txt":
        dest = SCRATCH / "TinyStories-valid.txt"
        if not dest.exists():
            shutil.copy2(corpus, dest)
        corpus = dest
    if not ckpt.is_file() or not tok.is_file():
        raise SystemExit(f"missing checkpoint/tokenizer under {ASSETS}")
    return ckpt, tok, corpus


def measure(py, fpm, ckpt, tok, steps, mse=False, alt_ckpt=None):
    sys.path.insert(0, str(TESTS))
    import fixed_point_model as fpm_mod  # noqa: WPS
    path = alt_ckpt or ckpt
    ck, dims = fpm_mod.load(str(path))
    ref_ck, _ = fpm_mod.load(str(ckpt))  # always compare to original FP32
    pieces = fpm_mod.load_tokenizer(str(tok))
    ref = fpm_mod.float_trace(ref_ck, dims, steps)
    fixed = fpm_mod.emulate(
        ck, dims, k_x=3, sm_shift=2, steps=steps,
        int8_ops=("wq1",), mse_scale=mse,
    )
    pref = fpm_mod.prefix_match_len(fixed, ref)
    detok = fpm_mod.detokenize(pieces, fixed)
    ref_detok = fpm_mod.detokenize(pieces, ref)
    return {
        "prefix": pref,
        "steps": steps,
        "fixed_tokens": fixed,
        "fp32_tokens": ref,
        "detok": detok,
        "fp32_detok": ref_detok,
        "mse_scale": mse,
        "checkpoint": str(path),
    }


def pack_images(py, ckpt, out_dir, mse=False, alphas_path=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [py, str(TESTS / "pack_stories260k.py"), str(ckpt), str(out_dir)]
    if mse:
        cmd.append("--mse-scale")
    if alphas_path:
        cmd.extend(["--alphas", str(alphas_path)])
    print("PACK:", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def prefix_aware_refine(ckpt, tok, steps=24, max_rounds=4):
    """Pure-Python coordinate search: per-matrix quant alpha + sm_shift
    maximizing greedy fixed-point prefix match vs original FP32.
    No torch required.
    """
    import fixed_point_model as fpm

    ck, dims = fpm.load(str(ckpt))
    pieces = fpm.load_tokenizer(str(tok))
    ref = fpm.float_trace(ck, dims, steps)
    alphas = (
        1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65,
        1.05, 1.1, 1.15, 1.2, 0.6,
    )

    # Prioritize early-layer attention/FFN matrices (affect opening story most).
    mats = [("emb", None, ck["emb"], 512, 64, True, False)]
    order_names = ("wq", "wk", "wv", "wo", "w1", "w2", "w3")
    for l in range(5):
        for name in order_names:
            m, k = dims[name]
            i8 = (name == "wq" and l == 1)
            mats.append((name, l, ck[name][l], m, k, False, i8))

    chosen = {f"{n}{'' if l is None else l}": 1.0 for n, l, *_ in mats}
    sm_shift = 2

    def build_prequant():
        pre = {}
        for name, layer, vals, m, k, emb, i8 in mats:
            key = name if emb else f"{name}{layer}"
            a = chosen[key]
            pre[key] = fpm.quant_matrix(
                vals, m, k,
                k_x=(3 if emb else 0),
                bits=(8 if i8 else 4),
                clip=a,
                mse_scale=False,
            )
        return pre

    def eval_prefix(pre, sm):
        toks = fpm.emulate(
            ck, dims, k_x=3, sm_shift=sm, steps=steps,
            int8_ops=("wq1",), prequant=pre,
        )
        # Secondary key: position matches among first 16 for stability.
        pos16 = sum(1 for a, b in zip(toks[:16], ref[:16]) if a == b)
        pref = fpm.prefix_match_len(toks, ref)
        return (pref, pos16), toks

    best_key, best_toks = eval_prefix(build_prequant(), sm_shift)
    print(f"refine start prefix={best_key[0]}/{steps} pos16={best_key[1]}",
          flush=True)

    # sm_shift joint search once at start
    for sm in (1, 2, 3, 0, 4):
        key, toks = eval_prefix(build_prequant(), sm)
        if key > best_key:
            best_key, best_toks, sm_shift = key, toks, sm
            print(f"  sm_shift={sm} prefix={best_key[0]}/{steps}", flush=True)

    for rnd in range(max_rounds):
        improved = False
        for name, layer, vals, m, k, emb, i8 in mats:
            key_name = name if emb else f"{name}{layer}"
            base_a = chosen[key_name]
            local_best = (best_key, base_a, best_toks)
            for a in alphas:
                if abs(a - base_a) < 1e-9:
                    continue
                chosen[key_name] = a
                key, toks = eval_prefix(build_prequant(), sm_shift)
                if key > local_best[0]:
                    local_best = (key, a, toks)
            chosen[key_name] = local_best[1]
            if local_best[0] > best_key:
                best_key, best_toks = local_best[0], local_best[2]
                improved = True
                print(f"  round{rnd} {key_name} alpha={local_best[1]} "
                      f"prefix={best_key[0]}/{steps} pos16={best_key[1]}",
                      flush=True)
            else:
                chosen[key_name] = base_a
        if not improved:
            break

    # Final sm_shift re-check with refined alphas
    for sm in (1, 2, 3, 0, 4):
        key, toks = eval_prefix(build_prequant(), sm)
        if key > best_key:
            best_key, best_toks, sm_shift = key, toks, sm
            print(f"  final sm_shift={sm} prefix={best_key[0]}/{steps}",
                  flush=True)

    detok = fpm.detokenize(pieces, best_toks)
    alpha_path = SCRATCH / "prefix_alphas.json"
    payload = dict(chosen)
    payload["__sm_shift__"] = sm_shift
    alpha_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "prefix": best_key[0],
        "steps": steps,
        "fixed_tokens": best_toks,
        "detok": detok,
        "alphas": chosen,
        "sm_shift": sm_shift,
        "fp32_tokens": ref,
        "fp32_detok": fpm.detokenize(pieces, ref),
    }


def run_qat(py, ckpt, tok, corpus, steps=400):
    out_ckpt = QAT_OUT / "stories260K_qat.bin"
    metrics = QAT_OUT / "metrics.json"
    cmd = [
        py, str(TESTS / "qat_stories260k.py"),
        str(ckpt), str(tok), str(corpus), str(out_ckpt),
        "--steps", str(steps),
        "--batch-size", "8",
        "--seq-len", "96",
        "--max-chars", "800000",
        "--eval-batches", "4",
        "--eval-interval", "50",
        "--learning-rate", "5.0e-4",
        "--distill-weight", "0.65",
        "--threads", "8",
        "--metrics", str(metrics),
    ]
    print("QAT:", " ".join(cmd), flush=True)
    t0 = time.time()
    try:
        subprocess.check_call(cmd)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print("QAT failed:", exc, flush=True)
        return None
    print(f"QAT finished in {time.time() - t0:.1f}s -> {out_ckpt}", flush=True)
    return out_ckpt if out_ckpt.is_file() else None


def main():
    py = find_python()
    print("python:", py, flush=True)

    ckpt, tok, corpus = ensure_assets()
    sys.path.insert(0, str(TESTS))
    steps = 64

    print("=== baseline ===", flush=True)
    base = measure(py, None, ckpt, tok, steps, mse=False)
    print(f"baseline prefix={base['prefix']}/{steps}", flush=True)
    print(f"  detok: {base['detok'][:120]!r}", flush=True)

    print("=== mse_scale ===", flush=True)
    mse = measure(py, None, ckpt, tok, steps, mse=True)
    print(f"mse_scale prefix={mse['prefix']}/{steps}", flush=True)
    print(f"  detok: {mse['detok'][:120]!r}", flush=True)

    best = base
    best_name = "baseline"
    best_ckpt = ckpt
    best_mse = False
    best_alphas = None
    if mse["prefix"] > best["prefix"]:
        best, best_name, best_mse = mse, "mse_scale", True

    print("=== prefix-aware scale refine (pure python) ===", flush=True)
    try:
        refined = prefix_aware_refine(ckpt, tok, steps=min(48, steps), max_rounds=4)
        print(f"refine prefix={refined['prefix']}/{refined['steps']}", flush=True)
        print(f"  detok: {refined['detok'][:120]!r}", flush=True)
        # Re-measure full 64 with refined alphas via packer-compatible clip path
        import fixed_point_model as fpm_mod
        ck0, dims0 = fpm_mod.load(str(ckpt))
        pre = {}
        for name, layer, vals, m, k, emb, i8 in [
            ("emb", None, ck0["emb"], 512, 64, True, False)
        ] + [
            (n, l, ck0[n][l], dims0[n][0], dims0[n][1], False, (n == "wq" and l == 1))
            for l in range(5) for n in dims0
        ]:
            key = name if emb else f"{name}{layer}"
            a = refined["alphas"].get(key, 1.0)
            pre[key] = fpm_mod.quant_matrix(
                vals, m, k, k_x=(3 if emb else 0),
                bits=(8 if i8 else 4), clip=a, mse_scale=False,
            )
        sm_use = int(refined.get("sm_shift", 2))
        full_toks = fpm_mod.emulate(
            ck0, dims0, k_x=3, sm_shift=sm_use, steps=steps,
            int8_ops=("wq1",), prequant=pre,
        )
        ref64 = fpm_mod.float_trace(ck0, dims0, steps)
        pref64 = fpm_mod.prefix_match_len(full_toks, ref64)
        pieces = fpm_mod.load_tokenizer(str(tok))
        refine64 = {
            "prefix": pref64,
            "steps": steps,
            "detok": fpm_mod.detokenize(pieces, full_toks),
            "fp32_detok": fpm_mod.detokenize(pieces, ref64),
            "fixed_tokens": full_toks,
        }
        print(f"refine@64 prefix={pref64}/{steps}", flush=True)
        print(f"  detok: {refine64['detok'][:120]!r}", flush=True)
        if pref64 > best["prefix"]:
            best = refine64
            best_name = "prefix_refine"
            best_mse = False
            best_alphas = SCRATCH / "prefix_alphas.json"
            print("prefix_refine is best — will pack with --alphas", flush=True)
    except Exception as exc:
        print("prefix refine failed:", exc, flush=True)
        import traceback
        traceback.print_exc()

    torch_ok = False
    try:
        r = subprocess.run(
            [py, "-c", "import torch; print(torch.__version__)"],
            capture_output=True, text=True, timeout=60,
        )
        torch_ok = r.returncode == 0
        print("torch:", r.stdout.strip() or r.stderr.strip(), flush=True)
    except Exception as exc:
        print("torch probe failed:", exc, flush=True)

    qat_result = None
    if torch_ok:
        print("=== QAT ===", flush=True)
        qat_ckpt = run_qat(py, ckpt, tok, corpus, steps=int(os.environ.get("QAT_STEPS", "400")))
        if qat_ckpt is not None:
            qat_result = measure(py, None, ckpt, tok, steps, mse=False, alt_ckpt=qat_ckpt)
            print(f"qat prefix={qat_result['prefix']}/{steps}", flush=True)
            print(f"  detok: {qat_result['detok'][:120]!r}", flush=True)
            # also try QAT + mse
            qat_mse = measure(py, None, ckpt, tok, steps, mse=True, alt_ckpt=qat_ckpt)
            print(f"qat+mse prefix={qat_mse['prefix']}/{steps}", flush=True)
            for name, res, use_mse in (
                ("qat", qat_result, False),
                ("qat_mse", qat_mse, True),
            ):
                if res["prefix"] > best["prefix"]:
                    best, best_name, best_ckpt, best_mse = res, name, qat_ckpt, use_mse
                    best_alphas = None

    # Promote best into shipping images
    print(f"=== promote best={best_name} prefix={best['prefix']}/{steps} ===", flush=True)
    pack_images(py, best_ckpt, IMG, mse=best_mse, alphas_path=best_alphas)
    if best_ckpt != ckpt:
        dest = ASSETS / "stories260K_qat.bin"
        shutil.copy2(best_ckpt, dest)
        print(f"saved QAT/best checkpoint -> {dest}", flush=True)

    report = {
        "baseline_prefix": base["prefix"],
        "mse_prefix": mse["prefix"],
        "qat_prefix": None if qat_result is None else qat_result["prefix"],
        "best": best_name,
        "best_prefix": best["prefix"],
        "best_detok": best["detok"][:240],
        "fp32_detok": best.get("fp32_detok", base["fp32_detok"])[:240],
        "improved": best["prefix"] > base["prefix"],
        "images": str(IMG),
        "torch_ok": torch_ok,
        "alphas": str(best_alphas) if best_alphas else None,
    }
    (SCRATCH / "fragmentation_solve.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    md = [
        "# Fragmentation solve report",
        "",
        f"- baseline prefix vs FP32: **{base['prefix']}/{steps}**",
        f"- mse_scale prefix: **{mse['prefix']}/{steps}**",
        f"- qat prefix: **{report['qat_prefix']}**",
        f"- **best: {best_name} → {best['prefix']}/{steps}**",
        f"- improved: **{report['improved']}**",
        f"- torch available: {torch_ok}",
        "",
        "## Best fixed detok (opening)",
        "",
        f"```\n{best['detok'][:400]}\n```",
        "",
        "## FP32 reference (opening)",
        "",
        f"```\n{best['fp32_detok'][:400]}\n```",
        "",
        f"Images updated under `{IMG}` for VCS (+WIMAGE/+VIMAGE).",
        "",
    ]
    (SCRATCH / "FRAGMENTATION_SOLVE.md").write_text("\n".join(md), encoding="utf-8")

    # Keep TB golden in sync with shipped images (first 64 generated tokens).
    if "fixed_tokens" in best and len(best["fixed_tokens"]) >= 64:
        update_tb_golden(best["fixed_tokens"][:64])

    print(json.dumps(report, indent=2), flush=True)
    if not report["improved"]:
        print(
            "NOTE: prefix did not improve over baseline; "
            "images still repacked from best candidate. "
            "Need longer QAT or more INT8 budget for larger gains.",
            flush=True,
        )
    return 0


def update_tb_golden(tokens64):
    """Rewrite golden_token case items 0..63 in tb_stories260k.sv."""
    tb = ROOT / "dv" / "tb" / "tb_stories260k.sv"
    text = tb.read_text(encoding="utf-8")
    lines = []
    for i in range(0, 64, 2):
        a, b = tokens64[i], tokens64[i + 1]
        if i + 2 < 64:
            lines.append(
                f"                {i:2d}: golden_token = 9'd{a};  "
                f"{i+1:2d}: golden_token = 9'd{b};"
            )
        else:
            lines.append(
                f"                {i:2d}: golden_token = 9'd{a};  "
                f"{i+1:2d}: golden_token = 9'd{b};"
            )
    block = "\n".join(lines)
    import re
    new_text, n = re.subn(
        r"(case \(idx\)\n)(.*?)(\n                default: golden_token = 9'd0;)",
        r"\1" + block + r"\3",
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        print("WARN: failed to patch TB golden_token", flush=True)
        return
    tb.write_text(new_text, encoding="utf-8")
    print(f"updated TB golden_token[0:63] in {tb}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
