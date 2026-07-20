#!/usr/bin/env python3
"""Generate alternate greedy stories from different seed tokens (QAT ckpt)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_point_model as fpm

# Candidate seeds: BOS + common TinyStories openings by id guess-scan
# We pick seeds by trying tokens whose first-piece starts with capital letters
# of interest after a quick scan of the tokenizer.
SEEDS_DEFAULT = [
    ("BOS", 1),
    # Will be filled by scanning tokenizer for useful words if present
]


def find_seeds(pieces, wanted):
    found = []
    for name, needle in wanted:
        needle_b = needle.encode("utf-8")
        # prefer exact match, then prefix with leading space
        hit = None
        for i, p in enumerate(pieces):
            if p == needle_b or p == b" " + needle_b:
                hit = i
                break
        if hit is None:
            for i, p in enumerate(pieces):
                if needle_b in p and 3 <= i < 512:
                    hit = i
                    break
        if hit is not None:
            found.append((name, hit))
    return found


def main():
    ckpt = ROOT / "assets/weights/stories260K_qat.bin"
    if not ckpt.is_file():
        ckpt = ROOT / "assets/weights/stories260K.bin"
    tok = ROOT / "assets/weights/tok512.bin"
    out_dir = ROOT / "dv/sim/quality/alt_stories"
    out_dir.mkdir(parents=True, exist_ok=True)

    pieces = fpm.load_tokenizer(str(tok))
    ck, dims = fpm.load(str(ckpt))
    # Optional packer alphas from QAT deliverable
    alphas_path = ROOT / "dv/sim/quality/qat/prefix_alphas.json"
    pre = None
    if alphas_path.is_file():
        alphas = json.loads(alphas_path.read_text(encoding="utf-8"))
        pre = {}
        mats = [("emb", None, ck["emb"], 512, 64, True, False)]
        for l in range(5):
            for name, (m, k) in dims.items():
                i8 = (name == "wq" and l == 1)
                mats.append((name, l, ck[name][l], m, k, False, i8))
        for name, layer, vals, m, k, emb, i8 in mats:
            key = name if emb else f"{name}{layer}"
            a = float(alphas.get(key, 1.0))
            pre[key] = fpm.quant_matrix(
                vals, m, k, k_x=(3 if emb else 0),
                bits=(8 if i8 else 4), clip=a, mse_scale=False,
            )

    wanted = [
        ("BOS", b"<s>"),  # may fail; force id 1 below
        ("Once", b"Once"),
        ("The", b"The"),
        ("Tim", b"Tim"),
        ("One", b"One"),
        ("There", b"There"),
        ("A", b"A"),
        ("She", b"She"),
        ("He", b"He"),
        ("Tom", b"Tom"),
        ("Lily", b"Lily"),
        ("It", b"It"),
    ]
    seeds = [("BOS", 1)]
    for name, needle in wanted[1:]:
        hit = None
        for i, p in enumerate(pieces):
            if p == needle or p == b" " + needle:
                hit = i
                break
        if hit is None:
            for i, p in enumerate(pieces):
                if p.startswith(needle) or p.startswith(b" " + needle):
                    hit = i
                    break
        if hit is not None and hit != 1:
            seeds.append((name, hit))

    steps = 64
    report = []
    text_out = []
    for name, sid in seeds[:8]:
        toks = fpm.emulate(
            ck, dims, k_x=3, sm_shift=2, steps=steps,
            int8_ops=("wq1",), prequant=pre, start_token=sid,
        )
        # story = seed piece + generated
        full_ids = [sid] + toks
        story = fpm.detokenize(pieces, full_ids)
        entry = {
            "seed_name": name,
            "seed_token": sid,
            "seed_piece": pieces[sid].decode("utf-8", errors="replace"),
            "tokens": full_ids,
            "story": story,
        }
        report.append(entry)
        text_out.append(f"## seed={name} id={sid} piece={entry['seed_piece']!r}\n")
        text_out.append(story + "\n\n---\n")
        print(f"[{name}/{sid}] {story[:120]!r}", flush=True)

    (out_dir / "alt_stories.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "alt_stories.txt").write_text("".join(text_out), encoding="utf-8")
    print("wrote", out_dir / "alt_stories.txt")


if __name__ == "__main__":
    main()
