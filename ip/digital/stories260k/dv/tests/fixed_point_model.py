#!/usr/bin/env python3
"""RTL-exact fixed-point emulator for stories260k numerics calibration.

Mirrors the stories260k hardware semantics operation-for-operation: mixed
W4/W8 group dequant, round-half-up folds, INT8 saturation, power-of-two KV
scales, fused attention, generated exp/sigmoid LUTs, restoring-divider
reciprocal, sm_shift scaling, and lowest-index argmax. Used to calibrate the
residual grid, requant values, and sm_shift and to generate the RTL prefix.

Design B (shipped) defaults match pack_stories260k.py / RTL:
  residual k_x=3, sm_shift=1, INT8 ops wq1/wk1/wv1/wo1/wq2/wo2/wq3 (Design-B v1.7),
  decode DEC_CFG defaults: rep_pen=32, adapt_en=0, norep_win=0 (R4 bit-exact).

Usage:
  fixed_point_model.py <stories260K.bin> [steps] [k_x] [sm_shift]
  fixed_point_model.py <stories260K.bin> --steps 64 --tokenizer tok512.bin
  fixed_point_model.py <stories260K.bin> --sweep --steps 32
"""

import argparse
import math
import struct
import sys

DIM, HID, NL, NH, HD, VLEN = 64, 172, 5, 8, 8, 512
NKVH = 4
KVDIM = DIM * NKVH // NH
SEQ_CAP = 512

# Shipped mixed-W4/W8 image (design B). Keep in sync with packer + RTL.
DEFAULT_K_X = 3
DEFAULT_SM_SHIFT = 1  # QAT mixed-W4/W8 image (design-B v1.3); base ckpt may prefer 2
DEFAULT_INT8_OPS = ("wq1", "wk1", "wv1", "wo1", "wq2", "wo2", "wq3")  # Design-B v1.7
# Decode-time frequency penalty (CSR DEC_CFG @ 0x038):
#   pen_eff = adapt_en ? (rep_pen + floor(pos/16)) : rep_pen
#   logit'  = logit - count*pen_eff  (count saturates at 15)
#   norep_win=N hard-bans the last N emitted tokens from argmax.
DEFAULT_REP_PEN = 32
DEFAULT_ADAPT_EN = 0
DEFAULT_NOREP_WIN = 0

EXP_TAB = [round(127 * math.exp((i - 128) / 16.0)) for i in range(129)]
SIG_TAB = [round(32767 / (1.0 + math.exp(-i / 16.0))) for i in range(129)]


def sat8(v):
    return 127 if v > 127 else (-128 if v < -128 else int(v))


def sat4(v):
    return 7 if v > 7 else (-8 if v < -8 else int(v))


def msb7(v):
    return v.bit_length() - 1 if v > 0 else 0


def load(path):
    with open(path, "rb") as f:
        header = struct.unpack("<7i", f.read(28))
        dim, hid, nl, nh, nkv, vocab, seq = header
        assert (dim, hid, nl, nh, nkv, vocab) == (DIM, HID, NL, NH, NKVH, VLEN), header
        raw = f.read()
    fl = struct.unpack(f"<{len(raw)//4}f", raw)
    p = [0]

    def take(n):
        v = fl[p[0]:p[0] + n]
        p[0] += n
        return list(v)

    ck = {"emb": take(vocab * dim), "rms_att": take(nl * dim)}
    dims = {"wq": (DIM, DIM), "wk": (KVDIM, DIM), "wv": (KVDIM, DIM),
            "wo": (DIM, DIM), "w1": (HID, DIM), "w2": (DIM, HID), "w3": (HID, DIM)}
    for name in ("wq", "wk", "wv", "wo"):
        ck[name] = [take(dims[name][0] * dims[name][1]) for _ in range(nl)]
    ck["rms_ffn"] = take(nl * dim)
    for name in ("w1", "w2", "w3"):
        ck[name] = [take(dims[name][0] * dims[name][1]) for _ in range(nl)]
    ck["rms_final"] = take(dim)
    return ck, dims


def _quant_seg(seg, qmin, qmax, scale):
    """Quantize one group; return (codes, mse) for float scale > 0."""
    codes = []
    mse = 0.0
    for v in seg:
        q = max(qmin, min(qmax, int(round(v / scale)))) if scale > 0 else 0
        codes.append(q)
        err = v - q * scale
        mse += err * err
    return codes, mse


def quant_matrix(vals, m, k, k_x=0, bits=4, clip=1.0, mse_scale=False):
    """Symmetric per-64-group quantization. Returns q[m][k], sc[m][groups].
    sc is Q4.12 including the optional x-grid bump by 2^k_x.

    mse_scale=True searches a scale multiplier in [0.55, 1.0] of max/qmax to
    minimize reconstruction MSE (still dequantized by RTL as q*sc>>12)."""
    qmax = 7 if bits == 4 else 127
    qmin = -8 if bits == 4 else -128
    groups = (k + 63) // 64
    nib = [[0] * k for _ in range(m)]
    sc = [[0] * groups for _ in range(m)]
    # Multipliers denser near 1.0; include 1.0 first for max-abs baseline.
    # Default max-abs path must stay bit-identical to the historical packer:
    # quantize with the *float* scale, then store rounded Q4.12. Only mse /
    # non-1 clip paths re-quantize from the stored scale.
    legacy = (not mse_scale) and abs(clip - 1.0) < 1e-12
    alphas = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55) if mse_scale else (1.0,)
    for r in range(m):
        row = vals[r * k:(r + 1) * k]
        for g in range(groups):
            seg = row[g * 64:min((g + 1) * 64, k)]
            mx = max((abs(v) for v in seg), default=0.0)
            if mx <= 0:
                sc[r][g] = max(1, 1 << k_x)
                continue
            if legacy:
                scale = mx / qmax
                sc[r][g] = max(1, min(32767, round(scale * 4096.0 * (1 << k_x))))
                for j, v in enumerate(seg):
                    q = int(round(v / scale)) if scale > 0 else 0
                    nib[r][g * 64 + j] = max(qmin, min(qmax, q))
                continue
            best_scale, best_mse = None, None
            for a in alphas:
                scale = (mx * clip * a) / qmax
                if scale <= 0:
                    continue
                _codes, err = _quant_seg(seg, qmin, qmax, scale)
                if best_mse is None or err < best_mse:
                    best_scale, best_mse = scale, err
            sc[r][g] = max(1, min(32767, round(best_scale * 4096.0 * (1 << k_x))))
            stored = sc[r][g] / (4096.0 * (1 << k_x))
            for j, v in enumerate(seg):
                q = int(round(v / stored)) if stored > 0 else 0
                nib[r][g * 64 + j] = max(qmin, min(qmax, q))
    return nib, sc


def mvm(nib, sc, x, m, k, mult=1, shift=0, groups_k=64):
    """Hardware MVM: int4 group dequant into int32 acc, then requant.
    Rounding at the group fold and at requant (round-half-up)."""
    y = []
    for r in range(m):
        acc = 0
        row = nib[r]
        for g in range((k + groups_k - 1) // groups_k):
            part = 0
            for j in range(g * groups_k, min((g + 1) * groups_k, k)):
                part += row[j] * x[j]
            acc += (part * sc[r][g] + 2048) >> 12
        rnd = (1 << (shift - 1)) if shift > 0 else 0
        y.append(sat8((acc * mult + rnd) >> shift))
    return y


def mvm_raw(nib, sc, x, m, k, groups_k=64):
    """int32 raw accumulators (score / logits argmax paths)."""
    out = []
    for r in range(m):
        acc = 0
        row = nib[r]
        for g in range((k + groups_k - 1) // groups_k):
            part = 0
            for j in range(g * groups_k, min((g + 1) * groups_k, k)):
                part += row[j] * x[j]
            acc += (part * sc[r][g] + 2048) >> 12
        out.append(acc)
    return out


def rmsnorm(x, gain_q, gain_frac=14):
    sumsq = sum(v * v for v in x)
    root = math.isqrt(sumsq)
    den = root if root > 0 else 1
    inv = min(131072 // den, 16383)
    gain_rnd = 1 << (gain_frac - 1)
    return [sat8(((((v * gain_q[i] + gain_rnd) >> gain_frac) * inv + 1024) >> 11))
            for i, v in enumerate(x)]


def rope(vec, pos, cos_t, sin_t):
    out = list(vec)
    for h in range(len(vec) // HD):
        for i in range(0, HD, 2):
            pi = i // 2
            a, b = out[h * HD + i], out[h * HD + i + 1]
            c, s = cos_t[pos][pi], sin_t[pos][pi]
            out[h * HD + i] = sat8((a * c - b * s + 8192) >> 14)
            out[h * HD + i + 1] = sat8((a * s + b * c + 8192) >> 14)
    return out


def q14_table(fn, npos):
    tab = []
    for p in range(npos):
        row = []
        for pi in range(4):
            theta = p * (10000.0 ** (-2.0 * pi / 8.0))
            row.append(max(-32768, min(32767, round(fn(theta) * 16384.0))))
        tab.append(row)
    return tab


def quant_gain(v, frac=14):
    """Packer-exact signed 16-bit gain conversion."""
    return max(-32768, min(32767, round(v * (1 << frac))))


def trace_vec(pos, layer, tag, vals):
    words = []
    for w in range((len(vals) + 7) // 8):
        word = 0
        for i, v in enumerate(vals[w * 8:(w + 1) * 8]):
            word |= (v & 0xFF) << (8 * i)
        words.append(f"{word:016x}")
    print(f"[trace p={pos} l={layer} tag={tag}] " + " ".join(words))


def kv_quant(vals, bits=4):
    """INT8 -> signed low-bit KV with power-of-two scale per 8 elements."""
    qmax = (1 << (bits - 1)) - 1
    qmin = -(1 << (bits - 1))
    out, scs = [], []
    for h in range(len(vals) // 8):
        seg = vals[h * 8:(h + 1) * 8]
        mx = max(abs(v) for v in seg)
        s = max(0, msb7(mx) - (bits - 2))
        scs.append(1 << (s + 9))
        # Parentheses are deliberate: for s==0 the data must pass through,
        # not collapse to the conditional expression's zero branch.
        out.extend(max(qmin, min(qmax,
                       (v + ((1 << (s - 1)) if s > 0 else 0)) >> s))
                   for v in seg)
    return out, scs


def emulate(ck, dims, k_x=3, sm_shift=6, steps=32, trace=False,
            int8_ops=(), gain_frac=14, kv_bits=4, weight_clip=1.0,
            prequant=None, mse_scale=False, start_token=1,
            rep_pen=None, adapt_en=None, norep_win=None):
    int8_ops = set(int8_ops)
    prequant = {} if prequant is None else prequant
    if rep_pen is None:
        rep_pen = DEFAULT_REP_PEN
    if adapt_en is None:
        adapt_en = DEFAULT_ADAPT_EN
    if norep_win is None:
        norep_win = DEFAULT_NOREP_WIN
    adapt_en = int(adapt_en) & 1
    norep_win = max(0, min(15, int(norep_win)))
    def qmat(name, layer, vals, m, k, emb=False):
        key = name if name == "emb" else f"{name}{layer}"
        if key in prequant:
            return prequant[key]
        use_i8 = name in int8_ops or f"{name}{layer}" in int8_ops
        return quant_matrix(vals, m, k, k_x=(k_x if emb else 0),
                            bits=(8 if use_i8 else 4), clip=weight_clip,
                            mse_scale=mse_scale)
    emb_nib, emb_sc = qmat("emb", 0, ck["emb"], VLEN, DIM, emb=True)
    wq = [qmat("wq", l, ck["wq"][l], DIM, DIM) for l in range(NL)]
    wk = [qmat("wk", l, ck["wk"][l], KVDIM, DIM) for l in range(NL)]
    wv = [qmat("wv", l, ck["wv"][l], KVDIM, DIM) for l in range(NL)]
    wo = [qmat("wo", l, ck["wo"][l], DIM, DIM) for l in range(NL)]
    w1 = [qmat("w1", l, ck["w1"][l], HID, DIM) for l in range(NL)]
    w2 = [qmat("w2", l, ck["w2"][l], DIM, HID) for l in range(NL)]
    w3 = [qmat("w3", l, ck["w3"][l], HID, DIM) for l in range(NL)]
    gains = []
    for l in range(NL):
        gains.append([quant_gain(g, gain_frac) for g in ck["rms_att"][l * DIM:(l + 1) * DIM]])
        gains.append([quant_gain(g, gain_frac) for g in ck["rms_ffn"][l * DIM:(l + 1) * DIM]])
    gains.append([quant_gain(g, gain_frac) for g in ck["rms_final"]])
    cos_t = q14_table(math.cos, SEQ_CAP)
    sin_t = q14_table(math.sin, SEQ_CAP)

    kc = [[None] * SEQ_CAP for _ in range(NL)]
    v4c = [[None] * SEQ_CAP for _ in range(NL)]
    ksc = [[None] * SEQ_CAP for _ in range(NL)]
    vsc = [[None] * SEQ_CAP for _ in range(NL)]

    tokens = []
    tok_freq = [0] * VLEN
    recent = []  # newest first; mirrors RTL recent_tok[0..14]
    token, pos = int(start_token) & 0x1FF, 0
    for _ in range(steps):
        x = mvm(emb_nib, emb_sc, [0] * DIM, 0, 0)  # placeholder unused
        # EMBED: dequant the token row (round-half-up)
        x = [sat8((emb_nib[token][i] * emb_sc[token][0] + 2048) >> 12) for i in range(DIM)]
        for l in range(NL):
            xb = rmsnorm(x, gains[2 * l], gain_frac)
            if trace:
                trace_vec(pos, l, "XB", xb)
            q = mvm(*wq[l], xb, DIM, DIM, mult=5793, shift=14)
            k = mvm(*wk[l], xb, KVDIM, DIM)
            v = mvm(*wv[l], xb, KVDIM, DIM)
            q = rope(q, pos, cos_t, sin_t)
            k = rope(k, pos, cos_t, sin_t)
            if trace:
                trace_vec(pos, l, "Q", q)
                trace_vec(pos, l, "KT", k)
                trace_vec(pos, l, "V", v)
            if kv_bits == 8:
                k4, kss = list(k), [512] * NKVH
                v4, vss = list(v), [512] * NKVH
            else:
                k4, kss = kv_quant(k, kv_bits)
                v4, vss = kv_quant(v, kv_bits)
            kc[l][pos], ksc[l][pos] = k4, kss
            v4c[l][pos], vsc[l][pos] = v4, vss
            att = [0] * DIM
            for h in range(NH):
                g = h // (NH // NKVH)
                svals = []
                smax = None
                for t in range(pos + 1):
                    sc = sum(q[h * HD + i] * kc[l][t][g * HD + i] for i in range(HD))
                    sv = (sc * ksc[l][t][g] + 1024) >> 11
                    svals.append(sv)
                    smax = sv if smax is None else max(smax, sv)
                sum_exp = 0
                pp = []
                for t in range(pos + 1):
                    z = max(-128, min(0, (svals[t] - smax) >> sm_shift))
                    e = EXP_TAB[z + 128]
                    sum_exp += e
                    pp.append(sat8((e * vsc[l][t][g] + 16384) >> 15))
                recip = (1 << 28) // max(sum_exp, 1)
                for i in range(HD):
                    acc = sum(pp[t] * v4c[l][t][g * HD + i] for t in range(pos + 1))
                    att[h * HD + i] = sat8((acc * recip + (1 << 21)) >> 22)
            if trace:
                trace_vec(pos, l, "ATT", att)
            y = mvm(*wo[l], att, DIM, DIM)
            x = [sat8(x[i] + y[i]) for i in range(DIM)]
            if trace:
                trace_vec(pos, l, "RES1", x)
            xb = rmsnorm(x, gains[2 * l + 1], gain_frac)
            h1 = mvm(*w1[l], xb, HID, DIM, mult=2)
            h3 = mvm(*w3[l], xb, HID, DIM, mult=2)
            hb = []
            for i in range(HID):
                xv = h1[i]
                sg = SIG_TAB[abs(xv)] if xv >= 0 else 32767 - SIG_TAB[abs(xv)]
                silu = (xv * sg + 16384) >> 15
                hb.append(sat8((silu * h3[i] + 64) >> 7))
            y = mvm(*w2[l], hb, DIM, HID, mult=4)
            x = [sat8(x[i] + y[i]) for i in range(DIM)]
            if trace:
                trace_vec(pos, l, "RES2", x)
        x = rmsnorm(x, gains[2 * NL], gain_frac)
        if trace:
            trace_vec(pos, NL, "RMSF", x)
        logits = mvm_raw(emb_nib, emb_sc, x, VLEN, DIM)
        # Match RTL DEC_CFG: pen_eff, 4-bit sat count, optional last-K ban.
        # pos == tokens completed so far (mirrors tok_cnt at argmax time).
        pen_eff = (rep_pen + (pos >> 4)) if adapt_en else rep_pen
        banned = set(recent[:norep_win]) if norep_win else set()

        def score(i):
            if i in banned:
                return None  # hard exclude
            return logits[i] - pen_eff * min(15, tok_freq[i])

        best_i, best_s = 0, None
        for i in range(VLEN):
            s = score(i)
            if s is None:
                continue
            # Lowest-index argmax on adjusted scores (strict > keeps first).
            if best_s is None or s > best_s:
                best_s, best_i = s, i
        token = best_i
        tokens.append(token)
        if tok_freq[token] < 15:
            tok_freq[token] += 1
        recent = [token] + recent[:14]
        pos += 1
    return tokens


def float_trace(ck, dims, steps=32, start_token=1):
    """FP32 greedy argmax trail (numpy if available, pure Python fallback)."""
    try:
        import numpy as np
    except ImportError:
        return float_trace_pure(ck, dims, steps, start_token=start_token)
    emb = np.array(ck["emb"]).reshape(VLEN, DIM)
    rms_att = np.array(ck["rms_att"]).reshape(NL, DIM)
    rms_ffn = np.array(ck["rms_ffn"]).reshape(NL, DIM)
    rms_final = np.array(ck["rms_final"])
    w = {n: [np.array(ck[n][l]).reshape(dims[n]) for l in range(NL)] for n in dims}
    rms = lambda x, g: x / np.sqrt(np.mean(x * x) + 1e-5) * g
    kc = np.zeros((NL, NKVH, SEQ_CAP, HD))
    vc = np.zeros_like(kc)
    toks, token, pos = [], int(start_token) & 0x1FF, 0
    for _ in range(steps):
        x = emb[token].copy()
        for l in range(NL):
            xb = rms(x, rms_att[l])
            q, k, v = w["wq"][l] @ xb, w["wk"][l] @ xb, w["wv"][l] @ xb
            for hh in range(NH):
                for i in range(0, HD, 2):
                    f = 10000.0 ** (-(i % HD) / HD)
                    c, s = math.cos(pos * f), math.sin(pos * f)
                    vecs = [q] if hh >= NKVH else [q, k]
                    for vec_ in vecs:
                        a, b = vec_[hh * HD + i], vec_[hh * HD + i + 1]
                        vec_[hh * HD + i] = a * c - b * s
                        vec_[hh * HD + i + 1] = a * s + b * c
            kc[l, :, pos, :] = k.reshape(NKVH, HD)
            vc[l, :, pos, :] = v.reshape(NKVH, HD)
            att = np.zeros(DIM)
            for hh in range(NH):
                g = hh // (NH // NKVH)
                t = kc[l, g, :pos + 1, :] @ q[hh * HD:(hh + 1) * HD] / math.sqrt(HD)
                t = np.exp(t - t.max())
                att[hh * HD:(hh + 1) * HD] = (t / t.sum()) @ vc[l, g, :pos + 1, :]
            x = x + w["wo"][l] @ att
            xb = rms(x, rms_ffn[l])
            h1, h3 = w["w1"][l] @ xb, w["w3"][l] @ xb
            x = x + w["w2"][l] @ ((h1 / (1.0 + np.exp(-h1))) * h3)
        x = rms(x, rms_final)
        token = int(np.argmax(emb @ x))
        toks.append(token)
        pos += 1
    return toks


def float_trace_pure(ck, dims, steps=32, start_token=1):
    """Pure-Python FP32 greedy trail (slower; no numpy dependency)."""
    def matvec(vals, m, k, x):
        return [sum(vals[r * k + j] * x[j] for j in range(k)) for r in range(m)]

    def rms(x, g):
        mean_sq = sum(v * v for v in x) / len(x)
        inv = 1.0 / math.sqrt(mean_sq + 1e-5)
        return [x[i] * inv * g[i] for i in range(len(x))]

    emb = [ck["emb"][i * DIM:(i + 1) * DIM] for i in range(VLEN)]
    rms_att = [ck["rms_att"][l * DIM:(l + 1) * DIM] for l in range(NL)]
    rms_ffn = [ck["rms_ffn"][l * DIM:(l + 1) * DIM] for l in range(NL)]
    rms_final = ck["rms_final"]
    w = {n: ck[n] for n in dims}
    kc = [[[0.0] * HD for _ in range(SEQ_CAP)] for _ in range(NL * NKVH)]
    vc = [[[0.0] * HD for _ in range(SEQ_CAP)] for _ in range(NL * NKVH)]
    toks, token, pos = [], int(start_token) & 0x1FF, 0
    for _ in range(steps):
        x = list(emb[token])
        for l in range(NL):
            xb = rms(x, rms_att[l])
            q = matvec(w["wq"][l], DIM, DIM, xb)
            k = matvec(w["wk"][l], KVDIM, DIM, xb)
            v = matvec(w["wv"][l], KVDIM, DIM, xb)
            for hh in range(NH):
                for i in range(0, HD, 2):
                    f = 10000.0 ** (-(i % HD) / HD)
                    c, s = math.cos(pos * f), math.sin(pos * f)
                    for vec_ in ([q] if hh >= NKVH else [q, k]):
                        a, b = vec_[hh * HD + i], vec_[hh * HD + i + 1]
                        vec_[hh * HD + i] = a * c - b * s
                        vec_[hh * HD + i + 1] = a * s + b * c
            for g in range(NKVH):
                base = l * NKVH + g
                kc[base][pos] = k[g * HD:(g + 1) * HD]
                vc[base][pos] = v[g * HD:(g + 1) * HD]
            att = [0.0] * DIM
            for hh in range(NH):
                g = hh // (NH // NKVH)
                base = l * NKVH + g
                scores = []
                for t in range(pos + 1):
                    sc = sum(q[hh * HD + i] * kc[base][t][i] for i in range(HD))
                    scores.append(sc / math.sqrt(HD))
                mscore = max(scores)
                exps = [math.exp(s - mscore) for s in scores]
                denom = sum(exps)
                for i in range(HD):
                    att[hh * HD + i] = sum(
                        (exps[t] / denom) * vc[base][t][i] for t in range(pos + 1))
            y = matvec(w["wo"][l], DIM, DIM, att)
            x = [x[i] + y[i] for i in range(DIM)]
            xb = rms(x, rms_ffn[l])
            h1 = matvec(w["w1"][l], HID, DIM, xb)
            h3 = matvec(w["w3"][l], HID, DIM, xb)
            hb = [(h1[i] / (1.0 + math.exp(-h1[i]))) * h3[i] for i in range(HID)]
            y = matvec(w["w2"][l], DIM, HID, hb)
            x = [x[i] + y[i] for i in range(DIM)]
        x = rms(x, rms_final)
        logits = [sum(emb[r][j] * x[j] for j in range(DIM)) for r in range(VLEN)]
        token = max(range(VLEN), key=lambda i: logits[i])
        toks.append(token)
        pos += 1
    return toks


def load_tokenizer(path):
    """Minimal llama2.c tok512.bin decoder (512 pieces)."""
    pieces = []
    with open(path, "rb") as f:
        _max_len = struct.unpack("<I", f.read(4))[0]
        for _ in range(VLEN):
            score_len = f.read(8)
            if len(score_len) != 8:
                raise ValueError("truncated tokenizer")
            _score, length = struct.unpack("<fI", score_len)
            piece = f.read(length)
            if len(piece) != length:
                raise ValueError("truncated tokenizer piece")
            pieces.append(piece)
    return pieces


def detokenize(pieces, tokens):
    """Detokenize tok512 ids. BOS/EOS skipped; pieces used as in llama2.c."""
    out = bytearray()
    for token in tokens:
        if token in (1, 2):
            continue
        if token < 0 or token >= len(pieces):
            continue
        piece = pieces[token]
        if piece in (b"<unk>",):
            continue
        if piece in (b"\n<s>\n", b"\n</s>\n"):
            out.extend(b"\n")
            continue
        if piece.startswith(b"<0x") and piece.endswith(b">") and len(piece) == 6:
            try:
                out.append(int(piece[3:5], 16))
                continue
            except ValueError:
                pass
        out.extend(piece)
    return out.decode("utf-8", errors="replace")


def prefix_match_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def first_mismatch(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i, x, y
    if len(a) != len(b):
        return min(len(a), len(b)), None, None
    return None, None, None


def report_trail(label, toks, ref, pieces=None):
    pref = prefix_match_len(toks, ref)
    pos_match = sum(1 for x, y in zip(toks, ref) if x == y)
    mm_i, mm_fix, mm_ref = first_mismatch(toks, ref)
    print(f"{label}: {toks}")
    print(f"  prefix_match_vs_fp32={pref}/{len(ref)}  position_match={pos_match}/{len(ref)}")
    if mm_i is not None:
        print(f"  first_mismatch_step={mm_i}  fixed={mm_fix}  fp32={mm_ref}")
    if pieces is not None:
        print(f"  detok: {detokenize(pieces, toks)!r}")
    return pref, pos_match


def parse_int8_ops(text):
    if not text:
        return ()
    return tuple(s.strip() for s in text.split(",") if s.strip())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("checkpoint", help="llama2.c stories260K.bin")
    ap.add_argument("steps_pos", nargs="?", type=int, default=None,
                    help="positional steps (compat)")
    ap.add_argument("k_x_pos", nargs="?", type=int, default=None,
                    help="positional k_x (compat)")
    ap.add_argument("sm_shift_pos", nargs="?", type=int, default=None,
                    help="positional sm_shift (compat)")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--k-x", type=int, default=None)
    ap.add_argument("--sm-shift", type=int, default=None)
    ap.add_argument("--int8-ops", default=",".join(DEFAULT_INT8_OPS),
                    help="comma list e.g. wq1,wk1,wv1 (default design-B QKV)")
    ap.add_argument("--weight-clip", type=float, default=1.0)
    ap.add_argument("--kv-bits", type=int, default=4)
    ap.add_argument("--mse-scale", action="store_true",
                    help="per-group MSE-optimal weight scale (vs max-abs)")
    ap.add_argument("--tokenizer", default="",
                    help="optional tok512.bin for detokenized story")
    ap.add_argument("--sweep", action="store_true",
                    help="sweep sm_shift (and report best position match)")
    ap.add_argument("--sweep-clip", action="store_true",
                    help="also sweep weight_clip in {1.0,0.95,0.9,0.85}")
    args = ap.parse_args(argv)

    steps = args.steps if args.steps is not None else (
        args.steps_pos if args.steps_pos is not None else 64)
    k_x = args.k_x if args.k_x is not None else (
        args.k_x_pos if args.k_x_pos is not None else DEFAULT_K_X)
    sm_shift = args.sm_shift if args.sm_shift is not None else (
        args.sm_shift_pos if args.sm_shift_pos is not None else DEFAULT_SM_SHIFT)
    int8_ops = parse_int8_ops(args.int8_ops)

    ck, dims = load(args.checkpoint)
    pieces = load_tokenizer(args.tokenizer) if args.tokenizer else None
    ref = float_trace(ck, dims, steps)
    print(f"config: steps={steps} k_x={k_x} sm_shift={sm_shift} "
          f"int8_ops={int8_ops or '(none/all-W4)'} weight_clip={args.weight_clip} "
          f"kv_bits={args.kv_bits} mse_scale={args.mse_scale}")
    print("float:", ref)
    if pieces is not None:
        print(f"  detok: {detokenize(pieces, ref)!r}")

    if args.sweep:
        clips = (1.0, 0.95, 0.9, 0.85) if args.sweep_clip else (args.weight_clip,)
        mse_opts = (False, True)
        best = None
        for mse in mse_opts:
            for clip in clips:
                for sm in range(0, 5):
                    toks = emulate(ck, dims, k_x=k_x, sm_shift=sm, steps=steps,
                                   int8_ops=int8_ops, weight_clip=clip,
                                   kv_bits=args.kv_bits, mse_scale=mse)
                    pref = prefix_match_len(toks, ref)
                    pos = sum(1 for a, b in zip(toks, ref) if a == b)
                    print(f"sweep k_x={k_x} sm_shift={sm} clip={clip} "
                          f"mse={mse}: prefix {pref}/{steps} pos {pos}/{steps} "
                          f"{toks[:12]}")
                    key = (pref, pos)
                    if best is None or key > best[0]:
                        best = (key, sm, clip, mse, toks)
        print("BEST_SWEEP:", f"sm_shift={best[1]} clip={best[2]} mse={best[3]} "
              f"prefix={best[0][0]}/{steps} pos={best[0][1]}/{steps}")
        report_trail("best_fixed", best[4], ref, pieces)
        return

    toks = emulate(ck, dims, k_x=k_x, sm_shift=sm_shift, steps=steps,
                   int8_ops=int8_ops, weight_clip=args.weight_clip,
                   kv_bits=args.kv_bits, mse_scale=args.mse_scale)
    report_trail(
        f"fixed(k_x={k_x},sm={sm_shift},i8={','.join(int8_ops) or 'none'},"
        f"clip={args.weight_clip},mse={args.mse_scale})",
        toks, ref, pieces)


if __name__ == "__main__":
    main()
