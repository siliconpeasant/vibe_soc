#!/usr/bin/env python3
"""Pack a llama2.c stories260K checkpoint into stories260k chip images.

Reads stories260K.bin (karpathy/llama2.c export format), quantizes weights
to INT4 except activation-sensitive layer-1 WQ to INT8, using per-64-element
Q4.12 group scales, and emits the 8x8 tile-interleaved WBUF image (weights,
split WQ1 INT8 upper halves, scales, 512-position RoPE table)
and the VECBUF image (RMSNorm gains, requant slots) as $readmemh hex files:

    +WIMAGE=<out>/wbuf.hex +VIMAGE=<out>/vecbuf.hex

Layout constants must stay in sync with de/rtl/stories260k_core.v and
docs/design_spec.md. Optional float forward-pass calibration derives the
per-op requant shifts from observed activation magnitudes (requires numpy).

Usage: pack_stories260k.py <stories260K.bin> <out_dir> [--no-calib]
"""

import math
import os
import struct
import sys

# model config (llama2.c stories260K: dim=64, hidden=172, 5 layers,
# 8 q-heads, 4 KV heads (GQA kv_mul=2, kv_dim=32), vocab=512; chip
# context matches the checkpoint maximum of 512 positions)
DIM, HID, NL, NH, HD, VLEN, SEQ = 64, 172, 5, 8, 8, 512, 512
NKVH = 4
KVDIM = DIM * NKVH // NH          # 32

# WBUF layout (32-byte words)
WBUF_WORDS = 4736
EMB_TILE_W = 0
LAYER_TILE_W = 512
LAYER_TILE_STRIDE = 720
TILE_OFF = {"wq": 0, "wk": 64, "wv": 96, "wo": 128,
            "w1": 192, "w2": 368, "w3": 544}
SC_EMB_W = 4112
SC_LAYER_W = 4144
SC_LAYER_STRIDE = 46
SC_OFF = {"wq": 0, "wk": 4, "wv": 6, "wo": 8, "w1": 12, "w2": 23, "w3": 35}
WBUF_ROPE_W = 4374  # 256 words; two {cos64,sin64} positions per 256b word
WBUF_WQ1_I8_HI_W = 4630  # 64 words: rows 4..7 of layer-1 WQ INT8 tiles

# VECBUF layout (8-byte words)
VEC_WORDS = 1024
GAIN_W = 0          # 11 entries x 16 words
RQ_W = 176
RQ_SLOTS = 37

MATS = ("wq", "wk", "wv", "wo", "w1", "w2", "w3")
MAT_DIMS = {"wq": (DIM, DIM), "wk": (KVDIM, DIM), "wv": (KVDIM, DIM),
            "wo": (DIM, DIM), "w1": (HID, DIM), "w2": (DIM, HID),
            "w3": (HID, DIM)}

# requant slot for q folds the attention 1/sqrt(head_dim) factor:
# q·k/sqrt(8) == (q*5793>>>14)·k with 5793 = round(1/sqrt(8)*2^14)
Q_ATT_SCALE = 5793
Q_ATT_SHIFT = 14


def parse_checkpoint(path):
    with open(path, "rb") as f:
        header = struct.unpack("<7i", f.read(28))
        dim, hid, nl, nh, nkv, vocab, seq = header
        if (dim, hid, nl, nh, nkv, vocab) != (DIM, HID, NL, NH, NKVH, VLEN):
            raise SystemExit(f"unexpected checkpoint header {header}")
        raw = f.read()
    floats = struct.unpack(f"<{len(raw)//4}f", raw)
    pos = [0]

    def take(n):
        vals = floats[pos[0]:pos[0] + n]
        if len(vals) != n:
            raise SystemExit("checkpoint truncated")
        pos[0] += n
        return list(vals)

    ck = {}
    ck["emb"] = take(vocab * dim)
    ck["rms_att"] = take(nl * dim)
    for name in ("wq", "wk", "wv", "wo"):
        m, k = MAT_DIMS[name]
        ck[name] = [take(m * k) for _ in range(nl)]
    ck["rms_ffn"] = take(nl * dim)
    for name in ("w1", "w2", "w3"):
        m, k = MAT_DIMS[name]
        ck[name] = [take(m * k) for _ in range(nl)]
    ck["rms_final"] = take(dim)
    # remaining floats (freq_cis tables, optional wcls) are regenerated
    # locally; shared_classifier means wcls == emb.
    return ck, seq


def quant_matrix(vals, m, k, k_x=0, bits=4, mse_scale=False, clip=1.0):
    """Return (nibbles[m][k_padded], scales[m][groups]) for row-major vals.
    k_x bumps the scale by 2^k_x (only the embedding, to establish the
    residual x grid; every other matrix consumes an already-gridded input).

    mse_scale searches a scale in [0.55,1.0]*max/qmax minimizing recon MSE,
    then re-quantizes with the stored Q4.12 scale (RTL-compatible).
    clip multiplies the max-abs (and mse candidates) — used for prefix-aware
    alpha calibration without RTL changes."""
    qmax = 7 if bits == 4 else 127
    qmin = -8 if bits == 4 else -128
    kpad = (k + 7) // 8 * 8
    groups = (k + 63) // 64
    nib = [[0] * kpad for _ in range(m)]
    sc = [[0] * groups for _ in range(m)]
    legacy = (not mse_scale) and abs(clip - 1.0) < 1e-12
    alphas = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55) if mse_scale else (1.0,)
    for r in range(m):
        row = vals[r * k:(r + 1) * k]
        for g in range(groups):
            seg = row[g * 64:min((g + 1) * 64, k)]
            mx = max((abs(v) for v in seg), default=0.0)
            if mx <= 0.0:
                sc[r][g] = max(1, 1 << k_x)
                continue
            if legacy:
                # Historical bit-exact path used by TB golden / v1.2 images.
                scale = mx / qmax
                sc[r][g] = max(1, min(32767, int(round(scale * 4096.0 * (1 << k_x)))))
                for j, v in enumerate(seg):
                    q = int(round(v / scale)) if scale > 0.0 else 0
                    nib[r][g * 64 + j] = max(qmin, min(qmax, q))
                continue
            best_scale, best_mse = None, None
            for a in alphas:
                scale = (mx * clip * a) / qmax
                if scale <= 0.0:
                    continue
                mse = 0.0
                for v in seg:
                    q = max(qmin, min(qmax, int(round(v / scale))))
                    err = v - q * scale
                    mse += err * err
                if best_mse is None or mse < best_mse:
                    best_scale, best_mse = scale, mse
            sc[r][g] = max(1, min(32767, int(round(best_scale * 4096.0 * (1 << k_x)))))
            stored = sc[r][g] / (4096.0 * (1 << k_x))
            for j, v in enumerate(seg):
                q = int(round(v / stored)) if stored > 0.0 else 0
                nib[r][g * 64 + j] = max(qmin, min(qmax, q))
    return nib, sc


def pack_tiles(wbuf, base_word, nib, m, k):
    """Pack INT4 matrix into 8x8 tiles; each 32B word: rows r..r+7 x 8 nib."""
    kwords = k // 8
    for m0 in range((m + 7) // 8):
        for k0 in range(kwords):
            rows = []
            for r in range(8):
                word32 = 0
                mr = m0 * 8 + r
                for l in range(8):
                    v = nib[mr][k0 * 8 + l] if mr < m else 0
                    word32 |= (v & 0xF) << (l * 4)
                rows.append(word32)
            word = 0
            for r in range(8):
                word |= rows[r] << (r * 32)
            wbuf[base_word + m0 * kwords + k0] = word


def pack_i8_split_tiles(wbuf, base_word, high_word, quant, m, k):
    """Pack 8x8 INT8 tiles as two 256-bit four-row halves."""
    kwords = k // 8
    for m0 in range((m + 7) // 8):
        for k0 in range(kwords):
            low = 0
            high = 0
            for row in range(8):
                row64 = 0
                mr = m0 * 8 + row
                for lane in range(8):
                    value = quant[mr][k0 * 8 + lane] if mr < m else 0
                    row64 |= (value & 0xFF) << (lane * 8)
                if row < 4:
                    low |= row64 << (row * 64)
                else:
                    high |= row64 << ((row - 4) * 64)
            tile = m0 * kwords + k0
            wbuf[base_word + tile] = low
            wbuf[high_word + tile] = high


def pack_scales(wbuf, base_word, sc, m, k):
    """Pack Q4.12 scales as [m-block][group][8 rows x int16] 16B units."""
    groups = (k + 63) // 64
    for m0 in range((m + 7) // 8):
        for g in range(groups):
            unit_idx = base_word * 2 + m0 * groups + g  # 16B units
            word_idx = unit_idx >> 1
            half = unit_idx & 1
            val = 0
            for r in range(8):
                mr = m0 * 8 + r
                s = sc[mr][g] if mr < m else 0
                val |= (s & 0xFFFF) << (r * 16)
            cur = wbuf[word_idx]
            if half:
                cur |= val << 128
            else:
                cur |= val
            wbuf[word_idx] = cur


def q14(x):
    return max(-32768, min(32767, int(round(x * 16384.0))))


def build_images(ck, rq, mse_scale=False, alphas=None):
    alphas = {k: v for k, v in (alphas or {}).items()
              if not str(k).startswith("__")}
    wbuf = [0] * WBUF_WORDS
    # embedding tiles + scales (x-grid bump k_x=3: residual stream is on
    # the x8 grid end to end; see fixed_point_model.py)
    emb_clip = float(alphas.get("emb", 1.0))
    nib, sc = quant_matrix(ck["emb"], VLEN, DIM, k_x=3, mse_scale=mse_scale,
                           clip=emb_clip)
    pack_tiles(wbuf, EMB_TILE_W, nib, VLEN, DIM)
    pack_scales(wbuf, SC_EMB_W, sc, VLEN, DIM)
    # per-layer matrices
    for l in range(NL):
        for name in MATS:
            m, k = MAT_DIMS[name]
            is_i8 = (l == 1 and name == "wq")
            clip = float(alphas.get(f"{name}{l}", 1.0))
            nib, sc = quant_matrix(ck[name][l], m, k,
                                   bits=(8 if is_i8 else 4),
                                   mse_scale=mse_scale, clip=clip)
            tile_base = LAYER_TILE_W + l * LAYER_TILE_STRIDE + TILE_OFF[name]
            if is_i8:
                pack_i8_split_tiles(wbuf, tile_base, WBUF_WQ1_I8_HI_W,
                                    nib, m, (k + 7) // 8 * 8)
            else:
                pack_tiles(wbuf, tile_base, nib, m, (k + 7) // 8 * 8)
            pack_scales(wbuf, SC_LAYER_W + l * SC_LAYER_STRIDE + SC_OFF[name],
                        sc, m, k)

    vec = [0] * VEC_WORDS
    # rms gains, interleaved [att, ffn] per layer, then final
    for l in range(NL):
        for e, src in ((0, ck["rms_att"][l * DIM:(l + 1) * DIM]),
                       (1, ck["rms_ffn"][l * DIM:(l + 1) * DIM])):
            idx = l * 2 + e
            for w in range(16):
                v = 0
                for j in range(4):
                    v |= (q14(src[w * 4 + j]) & 0xFFFF) << (j * 16)
                vec[GAIN_W + idx * 16 + w] = v
    for w in range(16):
        v = 0
        for j in range(4):
            v |= (q14(ck["rms_final"][w * 4 + j]) & 0xFFFF) << (j * 16)
        vec[GAIN_W + 10 * 16 + w] = v
    # rope tables: pair pi freq = 10000^(-2*pi/8), theta = pos * freq
    for p in range(SEQ):
        cv = 0
        sv = 0
        for pi in range(4):
            theta = p * (10000.0 ** (-2.0 * pi / 8.0))
            cv |= (q14(math.cos(theta)) & 0xFFFF) << (pi * 16)
            sv |= (q14(math.sin(theta)) & 0xFFFF) << (pi * 16)
        shift = (p & 1) * 128
        wbuf[WBUF_ROPE_W + (p >> 1)] |= cv << shift
        wbuf[WBUF_ROPE_W + (p >> 1)] |= sv << (shift + 64)
    # requant slots: word = {shift[39:32], mult[31:0]}
    for i in range(RQ_SLOTS):
        mult, shift = rq[i]
        vec[RQ_W + i] = ((shift & 0xFF) << 32) | (mult & 0xFFFFFFFF)
    assert WBUF_WQ1_I8_HI_W + 64 <= WBUF_WORDS
    assert RQ_W + RQ_SLOTS <= VEC_WORDS
    return wbuf, vec


def structural_rq():
    """Fixed requant table from the fixed-point grid analysis (no data
    calibration needed): q folds 1/sqrt(8); w1/w3 land on the SwiGLU x16
    grid; w2 lands its output back on the residual x8 grid."""
    rq = []
    for l in range(NL):
        rq.append((Q_ATT_SCALE, Q_ATT_SHIFT))  # q: x8 * 1/sqrt(8)
        rq.append((1, 0))                      # k: x8
        rq.append((1, 0))                      # v: x8
        rq.append((1, 0))                      # wo: x8
        rq.append((2, 0))                      # w1: x16 (GLU input grid)
        rq.append((4, 0))                      # w2: x2 acc -> x8 out
        rq.append((2, 0))                      # w3: x16
    rq.append((1, 16))  # slot 35: reserved (fused attention uses local recip)
    rq.append((1, 8))   # slot 36: reserved
    return rq


def emit_hex(path, words, bits):
    digits = bits // 4
    with open(path, "w") as f:
        for w in words:
            f.write(f"{w:0{digits}x}\n")


def main():
    raw = sys.argv[1:]
    mse_scale = "--mse-scale" in raw
    alphas = None
    args = []
    i = 0
    while i < len(raw):
        if raw[i] == "--mse-scale":
            i += 1
            continue
        if raw[i] == "--alphas" and i + 1 < len(raw):
            import json
            with open(raw[i + 1], "r") as f:
                alphas = json.load(f)
            i += 2
            continue
        args.append(raw[i])
        i += 1
    if len(args) < 2:
        sys.exit(__doc__ + "\nOptional: --mse-scale  --alphas prefix_alphas.json\n")
    ck, seq = parse_checkpoint(args[0])
    out_dir = args[1]
    os.makedirs(out_dir, exist_ok=True)
    rq = structural_rq()
    wbuf, vec = build_images(ck, rq, mse_scale=mse_scale, alphas=alphas)
    wp = os.path.join(out_dir, "wbuf.hex")
    vp = os.path.join(out_dir, "vecbuf.hex")
    emit_hex(wp, wbuf, 256)
    emit_hex(vp, vec, 64)
    used_w = sum(1 for w in wbuf if w)
    print(f"packed: {wp} ({len(wbuf)} words, {used_w} nonzero) mse_scale={mse_scale}")
    print(f"packed: {vp} ({len(vec)} words)")
    print(f"requant shifts: {[s for _, s in rq]}")


if __name__ == "__main__":
    main()
