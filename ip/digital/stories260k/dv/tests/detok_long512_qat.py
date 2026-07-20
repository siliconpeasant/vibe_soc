#!/usr/bin/env python3
"""Detokenize rtl_tokens_long.json under long512 / long256 / tb run dirs."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_point_model as fpm

tok_path = ROOT / "assets/weights/tok512.bin"
candidates = [
    ROOT / "dv/sim/long512/rtl_tokens_long.json",
    ROOT / "dv/sim/long256/rtl_tokens_long.json",
    ROOT / "dv/sim/tb_stories260k/rtl_tokens_long.json",
]

if not tok_path.is_file():
    print(f"skip detok: missing {tok_path}")
    sys.exit(0)

pieces = fpm.load_tokenizer(str(tok_path))
did = 0
for tokens_path in candidates:
    if not tokens_path.is_file():
        continue
    toks = json.loads(tokens_path.read_text(encoding="utf-8"))
    story = fpm.detokenize(pieces, toks)
    out_path = tokens_path.with_name(
        "story_long512_qat.txt" if "long512" in tokens_path.parts
        else "story_long256_qat.txt" if "long256" in tokens_path.parts
        else "story_detok.txt"
    )
    out_path.write_text(
        f"RTL VCS story detok\n"
        f"source={tokens_path}\n"
        f"tokens={len(toks)} (incl seed if first is seed)\n"
        f"first20={toks[:20]}\n"
        f"last20={toks[-20:]}\n\n"
        f"{story}\n",
        encoding="utf-8",
    )
    print(out_path)
    print(f"tokens={len(toks)}")
    print("---STORY_BEGIN---")
    print(story)
    print("---STORY_END---")
    did += 1

if did == 0:
    print("skip detok: no rtl_tokens_long.json found")
