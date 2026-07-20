#!/usr/bin/env python3
"""Compare original vs QAT checkpoints under design-B fixed-point vs original FP32."""

import argparse
import sys
from pathlib import Path

import fixed_point_model as fpm


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("orig_ckpt")
    ap.add_argument("qat_ckpt")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--steps", type=int, default=32)
    args = ap.parse_args()

    ck0, dims = fpm.load(args.orig_ckpt)
    ck1, _ = fpm.load(args.qat_ckpt)
    pieces = fpm.load_tokenizer(args.tokenizer)
    ref = fpm.float_trace(ck0, dims, args.steps)
    print("orig_fp32:", ref)
    print("  detok:", repr(fpm.detokenize(pieces, ref)))
    base = fpm.emulate(ck0, dims, k_x=3, sm_shift=2, steps=args.steps,
                       int8_ops=("wq1",))
    qat = fpm.emulate(ck1, dims, k_x=3, sm_shift=2, steps=args.steps,
                      int8_ops=("wq1",))
    bp, _ = fpm.report_trail("baseline_fixed", base, ref, pieces)
    qp, _ = fpm.report_trail("qat_fixed", qat, ref, pieces)
    print(f"prefix_gain={qp - bp}  (qat_prefix={qp} baseline_prefix={bp})")
    return 0 if qp >= bp else 1


if __name__ == "__main__":
    sys.exit(main())
