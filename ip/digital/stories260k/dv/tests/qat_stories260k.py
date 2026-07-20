#!/usr/bin/env python3
"""Hardware-format-aware QAT for the fixed stories260K accelerator.

The script starts from the public llama2.c FP32 checkpoint and fine-tunes it
with straight-through fake quantization matching the chip's immutable weight
format:

* signed INT4, symmetric per-output-row/per-64-input group weights;
* layer-1 WQ in signed INT8, as implemented by the RTL/packer;
* Q4.12 stored weight scales; and
* the principal W4A8 activation grids used by the fixed-point datapath.

It exports another llama2.c-format FP32 checkpoint.  The existing
pack_stories260k.py remains the single owner of WBUF/VECBUF packing, so QAT
does not change the RTL interface, SRAM map, bit widths, or cycle count.

This is intentionally a small, deterministic CPU-capable training utility.
It uses the checkpoint's matching 512-piece tokenizer and a local TinyStories
text file.  No training data or optimizer state is written into the repo.
"""

import argparse
import array
import json
import math
import random
import struct
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


DIM, HID, NL, NH, NKVH, VLEN, SEQ_LEN = 64, 172, 5, 8, 4, 512, 512
HD = DIM // NH
KV_MUL = NH // NKVH
CONSUMED_FLOATS = 260032


class BinTokenizer:
    """Minimal llama2.c tokenizer.bin encoder/decoder."""

    def __init__(self, path):
        self.path = Path(path)
        self.pieces = []
        self.scores = []
        with self.path.open("rb") as f:
            raw = f.read(4)
            if len(raw) != 4:
                raise ValueError("truncated tokenizer header")
            self.max_piece_len = struct.unpack("<I", raw)[0]
            for _ in range(VLEN):
                raw = f.read(8)
                if len(raw) != 8:
                    raise ValueError("truncated tokenizer entry")
                score, length = struct.unpack("<fI", raw)
                piece = f.read(length)
                if len(piece) != length:
                    raise ValueError("truncated tokenizer piece")
                self.scores.append(score)
                self.pieces.append(piece)
            if f.read(1):
                raise ValueError("tokenizer has more than 512 entries")
        self.lookup = {piece: i for i, piece in enumerate(self.pieces)}

    def encode(self, text, bos=True):
        data = text.encode("utf-8")
        tokens = [1] if bos else []
        if data:
            space = self.lookup.get(b" ")
            if space is None:
                raise ValueError("tokenizer is missing the dummy-prefix space")
            tokens.append(space)

        pos = 0
        while pos < len(data):
            length = 1
            while (pos + length < len(data) and length < 4 and
                   (data[pos + length] & 0xC0) == 0x80):
                length += 1
            piece = data[pos:pos + length]
            token = self.lookup.get(piece)
            if token is not None:
                tokens.append(token)
            else:
                tokens.extend(byte + 3 for byte in piece)
            pos += length

        # SentencePiece BPE: repeatedly merge the highest-score adjacent pair.
        while True:
            best_score = -1.0e30
            best_id = -1
            best_pos = -1
            for i in range(len(tokens) - 1):
                merged = self.pieces[tokens[i]] + self.pieces[tokens[i + 1]]
                token = self.lookup.get(merged)
                if token is not None and self.scores[token] > best_score:
                    best_score = self.scores[token]
                    best_id = token
                    best_pos = i
            if best_pos < 0:
                break
            tokens[best_pos] = best_id
            del tokens[best_pos + 1]
        return tokens

    def decode(self, tokens):
        out = bytearray()
        for token in tokens:
            if token in (1, 2):
                continue
            if 3 <= token <= 258:
                out.append(token - 3)
            else:
                out.extend(self.pieces[token])
        return out.decode("utf-8", errors="replace")


def take_tensor(values, offset, shape):
    count = math.prod(shape)
    tensor = torch.tensor(values[offset[0]:offset[0] + count], dtype=torch.float32)
    offset[0] += count
    return tensor.reshape(shape)


def load_checkpoint(path):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < 28:
        raise ValueError("truncated checkpoint")
    header = struct.unpack("<7i", raw[:28])
    expected = (DIM, HID, NL, NH, NKVH, VLEN, SEQ_LEN)
    if header != expected:
        raise ValueError("unexpected checkpoint header %r, expected %r" %
                         (header, expected))
    values = array.array("f")
    values.frombytes(raw[28:])
    if values.itemsize != 4:
        raise RuntimeError("host float size is not 32 bits")
    if len(values) < CONSUMED_FLOATS:
        raise ValueError("checkpoint tensor payload is truncated")

    off = [0]
    state = {}
    state["emb"] = take_tensor(values, off, (VLEN, DIM))
    state["rms_att"] = take_tensor(values, off, (NL, DIM))
    shapes = {
        "wq": (DIM, DIM),
        "wk": (DIM // KV_MUL, DIM),
        "wv": (DIM // KV_MUL, DIM),
        "wo": (DIM, DIM),
    }
    for name in ("wq", "wk", "wv", "wo"):
        state[name] = [take_tensor(values, off, shapes[name]) for _ in range(NL)]
    state["rms_ffn"] = take_tensor(values, off, (NL, DIM))
    shapes.update({"w1": (HID, DIM), "w2": (DIM, HID), "w3": (HID, DIM)})
    for name in ("w1", "w2", "w3"):
        state[name] = [take_tensor(values, off, shapes[name]) for _ in range(NL)]
    state["rms_final"] = take_tensor(values, off, (DIM,))
    if off[0] != CONSUMED_FLOATS:
        raise AssertionError("checkpoint parser consumed %d floats" % off[0])
    suffix = raw[28 + CONSUMED_FLOATS * 4:]
    return state, raw[:28], suffix


def fake_quant_weight(weight, bits):
    """Packer-equivalent group-64 fake quantization with an identity STE."""
    rows, cols = weight.shape
    groups = (cols + 63) // 64
    pad = groups * 64 - cols
    work = F.pad(weight, (0, pad)) if pad else weight
    work = work.reshape(rows, groups, 64)
    qmax = 7 if bits == 4 else 127
    qmin = -8 if bits == 4 else -128
    scale = work.detach().abs().amax(dim=-1, keepdim=True) / qmax
    scale = torch.where(scale > 0, scale, torch.ones_like(scale))
    quant = torch.clamp(torch.round(work / scale), qmin, qmax)
    # This rounding is present in WBUF: each scale is stored as unsigned Q4.12.
    scale_hw = torch.clamp(torch.round(scale * 4096.0), 1, 32767) / 4096.0
    dequant = (quant * scale_hw).reshape(rows, groups * 64)[:, :cols]
    return weight + (dequant - weight).detach()


def fake_quant_activation(value, units_per_real):
    quant = torch.clamp(torch.round(value * units_per_real), -128, 127)
    dequant = quant / units_per_real
    return value + (dequant - value).detach()


def fake_quant_kv(value):
    """Power-of-two signed-INT4 KV fake quantization per token/head."""
    # The RTL first holds K/V at 8 integer units per real unit.
    integer = torch.clamp(torch.round(value.detach() * 8.0), -128, 127)
    maximum = integer.abs().amax(dim=-1, keepdim=True)
    # kv_quant(): shift=max(0, floor(log2(maximum))-2).
    shift = torch.clamp(torch.floor(torch.log2(torch.clamp(maximum, min=1.0))) - 2.0,
                        min=0.0)
    step = torch.pow(2.0, shift)
    quant = torch.clamp(torch.round(integer / step), -8, 7)
    dequant = quant * step / 8.0
    return value + (dequant - value).detach()


class Stories260K(nn.Module):
    def __init__(self, initial, qat):
        super().__init__()
        self.qat = qat
        self.emb = nn.Parameter(initial["emb"].clone())
        self.rms_att = nn.Parameter(initial["rms_att"].clone())
        self.rms_ffn = nn.Parameter(initial["rms_ffn"].clone())
        self.rms_final = nn.Parameter(initial["rms_final"].clone())
        for name in ("wq", "wk", "wv", "wo", "w1", "w2", "w3"):
            setattr(self, name, nn.ParameterList(
                nn.Parameter(item.clone()) for item in initial[name]))

        pos = torch.arange(SEQ_LEN, dtype=torch.float32)
        freq = 1.0 / (10000.0 ** (torch.arange(0, HD, 2).float() / HD))
        angles = torch.outer(pos, freq)
        self.register_buffer("rope_cos", torch.cos(angles), persistent=False)
        self.register_buffer("rope_sin", torch.sin(angles), persistent=False)
        self.register_buffer("causal_mask", torch.triu(
            torch.ones(SEQ_LEN, SEQ_LEN, dtype=torch.bool), diagonal=1),
            persistent=False)

    @staticmethod
    def rmsnorm(value, gain):
        return value * torch.rsqrt(value.square().mean(dim=-1, keepdim=True) + 1.0e-5) * gain

    def weight(self, name, layer=None):
        value = self.emb if name == "emb" else getattr(self, name)[layer]
        if not self.qat:
            return value
        bits = 8 if name == "wq" and layer == 1 else 4
        return fake_quant_weight(value, bits)

    def aq(self, value, units):
        return fake_quant_activation(value, units) if self.qat else value

    def rope(self, value):
        length = value.shape[1]
        cos = self.rope_cos[:length].view(1, length, 1, HD // 2)
        sin = self.rope_sin[:length].view(1, length, 1, HD // 2)
        even, odd = value[..., 0::2], value[..., 1::2]
        return torch.stack((even * cos - odd * sin,
                            even * sin + odd * cos), dim=-1).flatten(-2)

    def forward(self, tokens):
        batch, length = tokens.shape
        if length > SEQ_LEN:
            raise ValueError("sequence length exceeds the 512-token model limit")
        emb = self.weight("emb")
        x = F.embedding(tokens, emb)
        x = self.aq(x, 8.0)

        for layer in range(NL):
            xb = self.rmsnorm(x, self.rms_att[layer])
            xb = self.aq(xb, 8.0)
            q = F.linear(xb, self.weight("wq", layer))
            k = F.linear(xb, self.weight("wk", layer))
            v = F.linear(xb, self.weight("wv", layer))
            q = self.aq(q, math.sqrt(8.0))
            k = self.aq(k, 8.0)
            v = self.aq(v, 8.0)
            q = self.rope(q.reshape(batch, length, NH, HD))
            k = self.rope(k.reshape(batch, length, NKVH, HD))
            if self.qat:
                k = fake_quant_kv(k)
                v = fake_quant_kv(v.reshape(batch, length, NKVH, HD))
            else:
                v = v.reshape(batch, length, NKVH, HD)
            k = k.repeat_interleave(KV_MUL, dim=2).transpose(1, 2)
            v = v.repeat_interleave(KV_MUL, dim=2).transpose(1, 2)
            q = q.transpose(1, 2)
            score = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(HD)
            score = score.masked_fill(self.causal_mask[:length, :length], -float("inf"))
            att = torch.matmul(F.softmax(score, dim=-1), v)
            att = att.transpose(1, 2).contiguous().reshape(batch, length, DIM)
            att = self.aq(att, 8.0)
            x = self.aq(x + F.linear(att, self.weight("wo", layer)), 8.0)

            xb = self.rmsnorm(x, self.rms_ffn[layer])
            xb = self.aq(xb, 8.0)
            h1 = self.aq(F.linear(xb, self.weight("w1", layer)), 16.0)
            h3 = self.aq(F.linear(xb, self.weight("w3", layer)), 16.0)
            hidden = self.aq(F.silu(h1) * h3, 2.0)
            x = self.aq(x + F.linear(hidden, self.weight("w2", layer)), 8.0)

        x = self.aq(self.rmsnorm(x, self.rms_final), 8.0)
        return F.linear(x, emb)

    def export_state(self):
        return {
            "emb": self.emb.detach().cpu(),
            "rms_att": self.rms_att.detach().cpu(),
            "rms_ffn": self.rms_ffn.detach().cpu(),
            "rms_final": self.rms_final.detach().cpu(),
            **{name: [item.detach().cpu() for item in getattr(self, name)]
               for name in ("wq", "wk", "wv", "wo", "w1", "w2", "w3")},
        }


def flatten_state(state):
    order = [state["emb"], state["rms_att"]]
    for name in ("wq", "wk", "wv", "wo"):
        order.extend(state[name])
    order.append(state["rms_ffn"])
    for name in ("w1", "w2", "w3"):
        order.extend(state[name])
    order.append(state["rms_final"])
    values = array.array("f")
    for tensor in order:
        values.extend(tensor.contiguous().view(-1).tolist())
    if len(values) != CONSUMED_FLOATS:
        raise AssertionError("export contains %d floats" % len(values))
    return values.tobytes()


def load_corpus(path, tokenizer, max_chars):
    text = Path(path).read_text(encoding="utf-8")
    if max_chars > 0:
        text = text[:max_chars]
    stories = [story.strip() for story in text.split("<|endoftext|>") if story.strip()]
    if not stories:
        raise ValueError("corpus contains no stories")
    all_tokens = []
    for story in stories:
        all_tokens.extend(tokenizer.encode(story, bos=True))
    return torch.tensor(all_tokens, dtype=torch.long), len(stories)


def batch_from(tokens, batch_size, seq_len, generator):
    high = tokens.numel() - seq_len - 1
    if high <= 0:
        raise ValueError("tokenized corpus is shorter than one training sequence")
    starts = torch.randint(high, (batch_size,), generator=generator)
    offsets = torch.arange(seq_len + 1)
    chunk = tokens[starts[:, None] + offsets[None, :]]
    return chunk[:, :-1], chunk[:, 1:]


@torch.no_grad()
def evaluate(model, teacher, tokens, batch_size, seq_len, batches, generator):
    model.eval()
    losses = []
    teacher_losses = []
    for _ in range(batches):
        x, y = batch_from(tokens, batch_size, seq_len, generator)
        logits = model(x)
        teacher_logits = teacher(x)
        losses.append(F.cross_entropy(logits.reshape(-1, VLEN), y.reshape(-1)).item())
        teacher_losses.append(F.cross_entropy(
            teacher_logits.reshape(-1, VLEN), y.reshape(-1)).item())
    model.train()
    return sum(losses) / len(losses), sum(teacher_losses) / len(teacher_losses)


@torch.no_grad()
def greedy_tokens(model, steps):
    model.eval()
    tokens = [1]
    for _ in range(steps):
        inp = torch.tensor(tokens, dtype=torch.long).unsqueeze(0)
        token = int(torch.argmax(model(inp)[0, -1]).item())
        tokens.append(token)
        if token == 1:
            break
    return tokens[1:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", help="input llama2.c stories260K.bin")
    parser.add_argument("tokenizer", help="matching tok512.bin")
    parser.add_argument("corpus", help="local TinyStories text corpus")
    parser.add_argument("output", help="output QAT llama2.c checkpoint")
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seq-len", type=int, default=128)
    parser.add_argument("--max-chars", type=int, default=2000000)
    parser.add_argument("--eval-batches", type=int, default=8)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=3.0e-4)
    parser.add_argument("--distill-weight", type=float, default=0.5)
    parser.add_argument("--temperature", type=float, default=2.0)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed", type=int, default=260512)
    parser.add_argument("--metrics", help="optional JSON metrics output")
    args = parser.parse_args()
    if not (1 <= args.seq_len <= SEQ_LEN):
        parser.error("--seq-len must be in [1, 512]")
    if args.steps < 1:
        parser.error("--steps must be positive")

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    tokenizer = BinTokenizer(args.tokenizer)
    initial, header, suffix = load_checkpoint(args.checkpoint)
    corpus, story_count = load_corpus(args.corpus, tokenizer, args.max_chars)
    print("corpus: %d stories, %d tokens" % (story_count, corpus.numel()), flush=True)

    teacher = Stories260K(initial, qat=False).eval()
    for parameter in teacher.parameters():
        parameter.requires_grad_(False)
    model = Stories260K(initial, qat=True).train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate,
                                  betas=(0.9, 0.99), weight_decay=0.001)
    train_gen = torch.Generator().manual_seed(args.seed)
    eval_gen = torch.Generator().manual_seed(args.seed + 1)

    initial_loss, teacher_loss = evaluate(
        model, teacher, corpus, args.batch_size, args.seq_len,
        args.eval_batches, eval_gen)
    print("initial: qat_ce=%.5f teacher_ce=%.5f" % (initial_loss, teacher_loss),
          flush=True)
    best_loss = initial_loss
    best_state = {key: value.detach().cpu().clone()
                  for key, value in model.state_dict().items()}
    history = []
    started = time.monotonic()

    for step in range(1, args.steps + 1):
        x, y = batch_from(corpus, args.batch_size, args.seq_len, train_gen)
        with torch.no_grad():
            teacher_logits = teacher(x)
        logits = model(x)
        ce = F.cross_entropy(logits.reshape(-1, VLEN), y.reshape(-1))
        temp = args.temperature
        kl = F.kl_div(F.log_softmax(logits / temp, dim=-1),
                      F.softmax(teacher_logits / temp, dim=-1),
                      reduction="none").sum(dim=-1).mean() * temp * temp
        loss = (1.0 - args.distill_weight) * ce + args.distill_weight * kl
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % args.eval_interval == 0 or step == args.steps:
            val_loss, _ = evaluate(model, teacher, corpus, args.batch_size,
                                   args.seq_len, args.eval_batches, eval_gen)
            elapsed = time.monotonic() - started
            item = {"step": step, "train_loss": float(loss.item()),
                    "ce": float(ce.item()), "kl": float(kl.item()),
                    "grad_norm": float(grad_norm), "qat_ce": val_loss,
                    "elapsed_s": elapsed}
            history.append(item)
            print("step %4d: loss=%.5f ce=%.5f kl=%.5f val=%.5f %.2f step/s" %
                  (step, loss.item(), ce.item(), kl.item(), val_loss,
                   step / max(elapsed, 1.0e-9)), flush=True)
            if val_loss < best_loss:
                best_loss = val_loss
                best_state = {key: value.detach().cpu().clone()
                              for key, value in model.state_dict().items()}

    model.load_state_dict(best_state)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(header + flatten_state(model.export_state()) + suffix)
    if output.stat().st_size != Path(args.checkpoint).stat().st_size:
        raise AssertionError("QAT checkpoint size differs from the source checkpoint")

    sample_tokens = greedy_tokens(model, 128)
    sample_text = tokenizer.decode(sample_tokens)
    print("best qat_ce=%.5f; output=%s" % (best_loss, output), flush=True)
    print("QAT-surrogate greedy tokens:", sample_tokens, flush=True)
    print("QAT-surrogate story:", sample_text, flush=True)
    metrics = {
        "format": "stories260k-hardware-qat-v1",
        "input_checkpoint": str(Path(args.checkpoint).resolve()),
        "output_checkpoint": str(output.resolve()),
        "seed": args.seed,
        "steps": args.steps,
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "corpus_stories": story_count,
        "corpus_tokens": int(corpus.numel()),
        "teacher_ce": teacher_loss,
        "initial_qat_ce": initial_loss,
        "best_qat_ce": best_loss,
        "sample_tokens": sample_tokens,
        "sample_text": sample_text,
        "history": history,
    }
    if args.metrics:
        metrics_path = Path(args.metrics)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
