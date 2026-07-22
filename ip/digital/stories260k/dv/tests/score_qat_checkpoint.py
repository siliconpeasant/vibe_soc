#!/usr/bin/env python3
"""Multi-length + fragmentation scorer for stories260k QAT checkpoints (R5).

Runs the RTL-exact fixed_point_model trail at 64/128/256/512 (default),
compares prefix vs official FP32 greedy when a teacher bin is provided, and
applies hard gates including:
  - 4-gram repeat fraction
  - BOS-reset count (token id 1 reappearing after start)
  - unique-token fraction
  - long alpha-word fragmentation (max_alpha, n_long>=12)

Score is lower-is-better (R5 formula). Exit code 0 only when all hard gates pass.

Usage:
  python3 score_qat_checkpoint.py --checkpoint stories260K_qat.bin \\
      --tokenizer tok512.bin --teacher stories260K.bin --out-dir out/
  make score-qat CKPT=assets/weights/stories260K_qat.bin
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import fixed_point_model as fpm


def ngram_repeat_frac(toks, n=4):
    if len(toks) < n:
        return 0.0
    seen = set()
    rep = total = 0
    for i in range(len(toks) - n + 1):
        g = tuple(toks[i:i + n])
        total += 1
        if g in seen:
            rep += 1
        else:
            seen.add(g)
    return rep / total if total else 0.0


def bos_reset_count(toks):
    """Count BOS (id=1) reappearances after the first emitted token."""
    return sum(1 for t in toks[1:] if t == 1)


def alpha_frag_stats(text: str):
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return {
            "max_alpha": 0,
            "n_long_ge12": 0,
            "n_long_ge15": 0,
            "long_char_frac": 0.0,
            "longest_words": [],
        }
    long12 = [w for w in words if len(w) >= 12]
    long15 = [w for w in words if len(w) >= 15]
    long_chars = sum(len(w) for w in long12)
    uniq_long = sorted(set(long12), key=len, reverse=True)
    return {
        "max_alpha": max(len(w) for w in words),
        "n_long_ge12": len(long12),
        "n_long_ge15": len(long15),
        "long_char_frac": long_chars / max(1, len(text)),
        "longest_words": uniq_long[:8],
    }


def trail_metrics(toks, pieces, ref=None):
    story = fpm.detokenize(pieces, [1] + list(toks)) if pieces is not None else ""
    frag = alpha_frag_stats(story)
    m = {
        "tokens": len(toks),
        "unique_frac": len(set(toks)) / max(1, len(toks)),
        "repeat4": ngram_repeat_frac(toks, 4),
        "repeat4_tail_half": ngram_repeat_frac(toks[len(toks) // 2:], 4),
        "bos_reset": bos_reset_count(toks),
        "prefix_vs_fp32": fpm.prefix_match_len(toks, ref) if ref is not None else None,
        "story": story,
        **frag,
    }
    return m


# R5 hard gates (stricter on 512 fragmentation than R4).
GATES = {
    64:  {"prefix_min": 20, "repeat4_max": 0.0,   "bos_max": 0, "max_alpha_max": 14, "n_long12_max": 0},
    128: {"prefix_min": 20, "repeat4_max": 0.010, "bos_max": 0, "max_alpha_max": 16, "n_long12_max": 1},
    256: {"prefix_min": 20, "repeat4_max": 0.010, "bos_max": 0, "max_alpha_max": 16, "n_long12_max": 2},
    512: {"prefix_min": 20, "repeat4_max": 0.040, "bos_max": 1, "max_alpha_max": 14, "n_long12_max": 1},
}


def gate_failures(length, m, have_teacher: bool):
    g = GATES[length]
    fails = []
    if have_teacher and m["prefix_vs_fp32"] is not None:
        if m["prefix_vs_fp32"] < g["prefix_min"]:
            fails.append(f"prefix {m['prefix_vs_fp32']}<{g['prefix_min']}")
    if m["repeat4"] > g["repeat4_max"] + 1e-12:
        fails.append(f"repeat4 {m['repeat4']:.4f}>{g['repeat4_max']}")
    if m["bos_reset"] > g["bos_max"]:
        fails.append(f"bos_reset {m['bos_reset']}>{g['bos_max']}")
    if m["max_alpha"] > g["max_alpha_max"]:
        fails.append(f"max_alpha {m['max_alpha']}>{g['max_alpha_max']}")
    if m["n_long_ge12"] > g["n_long12_max"]:
        fails.append(f"n_long>=12 {m['n_long_ge12']}>{g['n_long12_max']}")
    return fails


def r5_score(by_len: dict) -> float:
    """Lower is better. Extends R4 multi-length formula with fragmentation terms."""
    def r4(L):
        return float(by_len[L]["repeat4"])

    def bos(L):
        return float(by_len[L]["bos_reset"])

    def pref(L):
        p = by_len[L].get("prefix_vs_fp32")
        return 20 if p is None else int(p)

    s = 0.0
    s += 3.0 * max(0.0, r4(256) - 0.008)
    s += 2.0 * max(0.0, r4(128) - 0.005)
    s += 1.5 * max(0.0, r4(512) - 0.030)   # R5: tighter than R4's 0.039
    s += 2.0 * bos(128)
    s += 3.0 * bos(256)
    s += 1.0 * bos(512)
    s += 0.2 * max(0, 20 - pref(64))
    # Fragmentation (new in R5)
    s += 0.8 * max(0, by_len[512]["max_alpha"] - 12)
    s += 1.0 * by_len[512]["n_long_ge12"]
    s += 0.5 * by_len[256]["n_long_ge12"]
    s += 0.4 * max(0.0, 0.40 - by_len[512]["unique_frac"])  # reward uniq ~>=0.40
    s += 1.2 * by_len[512]["repeat4_tail_half"]
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--tokenizer", type=Path, default=None)
    ap.add_argument("--teacher", type=Path, default=None,
                    help="official FP32 stories260K.bin for prefix compare")
    ap.add_argument("--steps", nargs="+", type=int, default=[64, 128, 256, 512])
    ap.add_argument("--sm-shift", type=int, default=fpm.DEFAULT_SM_SHIFT)
    ap.add_argument("--rep-pen", type=int, default=fpm.DEFAULT_REP_PEN)
    ap.add_argument("--adapt-en", type=int, default=0)
    ap.add_argument("--norep-win", type=int, default=0)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args(argv)

    ck_path = args.checkpoint
    if not ck_path.is_file():
        print(f"ERROR: missing checkpoint {ck_path}", file=sys.stderr)
        return 2

    t0 = time.time()
    ck, dims = fpm.load(str(ck_path))
    pieces = fpm.load_tokenizer(str(args.tokenizer)) if args.tokenizer and args.tokenizer.is_file() else None
    ops = fpm.DEFAULT_INT8_OPS

    refs = {}
    have_teacher = args.teacher is not None and args.teacher.is_file()
    if have_teacher:
        tck, tdims = fpm.load(str(args.teacher))
        for s in args.steps:
            refs[s] = fpm.float_trace(tck, tdims, steps=s)

    by_len = {}
    for s in args.steps:
        toks = list(fpm.emulate(
            ck, dims, k_x=3, sm_shift=args.sm_shift, steps=s,
            int8_ops=ops, rep_pen=args.rep_pen,
            adapt_en=args.adapt_en, norep_win=args.norep_win,
        ))
        by_len[s] = trail_metrics(toks, pieces, refs.get(s))
        by_len[s]["token_ids"] = toks
        print(
            f"[{s}] uniq={by_len[s]['unique_frac']:.3f} "
            f"r4={by_len[s]['repeat4']:.4f} r4_tail={by_len[s]['repeat4_tail_half']:.4f} "
            f"bos={by_len[s]['bos_reset']} max_alpha={by_len[s]['max_alpha']} "
            f"nlong12={by_len[s]['n_long_ge12']} "
            f"prefix={by_len[s]['prefix_vs_fp32']}",
            flush=True,
        )

    all_fails = {}
    for s in args.steps:
        if s in GATES:
            all_fails[s] = gate_failures(s, by_len[s], have_teacher)
    hard_pass = all(len(v) == 0 for v in all_fails.values())

    # Full R5 score only when all four lengths are present.
    have_full = all(L in by_len for L in (64, 128, 256, 512))
    score = r5_score(by_len) if have_full else None

    # Serialize without huge token lists in summary (keep them in per-length files).
    summary = {
        "format": "stories260k-qat-score-r5",
        "checkpoint": str(ck_path),
        "tag": args.tag,
        "decode": {
            "sm_shift": args.sm_shift,
            "rep_pen": args.rep_pen,
            "adapt_en": args.adapt_en,
            "norep_win": args.norep_win,
        },
        "int8_ops": list(ops),
        "score_lower_better": score,
        "score_note": None if have_full else "partial steps; full R5 score needs 64/128/256/512",
        "hard_pass": hard_pass,
        "gate_failures": all_fails,
        "gates": GATES,
        "lengths": {
            str(s): {
                k: by_len[s][k]
                for k in (
                    "tokens", "unique_frac", "repeat4", "repeat4_tail_half",
                    "bos_reset", "prefix_vs_fp32", "max_alpha", "n_long_ge12",
                    "n_long_ge15", "long_char_frac", "longest_words",
                )
                if k in by_len[s]
            }
            for s in args.steps
        },
        "elapsed_s": round(time.time() - t0, 2),
    }

    if score is None:
        print(f"score=n/a (need 64/128/256/512) hard_pass={hard_pass} "
              f"elapsed={summary['elapsed_s']}s")
    else:
        print(f"score={score:.4f} hard_pass={hard_pass} elapsed={summary['elapsed_s']}s")
    if not hard_pass:
        print("FAIL gates:", json.dumps(all_fails, ensure_ascii=False))
    else:
        print("PASS all hard gates")

    if args.out_dir is not None:
        out = args.out_dir
        out.mkdir(parents=True, exist_ok=True)
        stem = args.tag or ck_path.stem
        (out / f"{stem}_score.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for s in args.steps:
            (out / f"{stem}_story_{s}.txt").write_text(
                by_len[s].get("story", "") + "\n", encoding="utf-8")
            (out / f"{stem}_tokens_{s}.json").write_text(
                json.dumps(by_len[s].get("token_ids", []), ensure_ascii=False) + "\n",
                encoding="utf-8")
        print(f"wrote {out}/{stem}_score.json")

    return 0 if hard_pass else 1


if __name__ == "__main__":
    sys.exit(main())
