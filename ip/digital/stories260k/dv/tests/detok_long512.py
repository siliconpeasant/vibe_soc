#!/usr/bin/env python3
"""Detokenize RTL long512 tokens using tok512.bin (via fixed_point_model)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # ip/digital/stories260k
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixed_point_model as fpm  # noqa: E402

TOK = ROOT / "assets/weights/tok512.bin"
TOKENS = ROOT / "dv/sim/long512/rtl_tokens_long.json"
OUT = ROOT / "dv/sim/long512/story_long512.txt"


def main():
    tokens = json.loads(TOKENS.read_text())
    pieces = fpm.load_tokenizer(str(TOK))
    text = fpm.detokenize(pieces, tokens)
    first20 = tokens[:20]
    first20_text = fpm.detokenize(pieces, first20)

    lines = [
        "RTL long-story detokenization (512 tokens)",
        "=" * 60,
        "",
        f"Token count: {len(tokens)}",
        f"First 20 tokens: {first20}",
        f"First 20 detok: {first20_text!r}",
        "",
        'Note: first 6 generated pieces should be "Once upon a time, there"',
        "then quality drops (quantization / W4A8 fidelity).",
        "",
        "Full detokenized text:",
        "-" * 60,
        text,
        "-" * 60,
        "",
    ]
    OUT.write_text("\n".join(lines))
    print("OUT:", OUT)
    print("N_TOKENS:", len(tokens))
    print("FIRST20:", first20)
    print("FIRST20_DETOK:", repr(first20_text))
    print("STORY_PREFIX200:", repr(text[:200]))
    print("STORY_LEN:", len(text))


if __name__ == "__main__":
    main()
