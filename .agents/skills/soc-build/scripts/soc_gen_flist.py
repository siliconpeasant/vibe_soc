#!/usr/bin/env python3
"""
SoC Gen Filelist - 一键扫描目录生成 Verilog filelist
支持递归搜索 *.v / *.sv / *.vhd，自动过滤注释和空行
"""

import os
import sys
import argparse
from pathlib import Path


def gen_flist(search_path, output="filelist.f", recursive=True, extensions=None):
    if extensions is None:
        extensions = ["*.v", "*.sv", "*.vhd"]

    path = Path(search_path).resolve()
    if not path.exists():
        print(f"[ERROR] Path not found: {path}")
        return 1

    files = []
    glob_func = path.rglob if recursive else path.glob
    for ext in extensions:
        files.extend(sorted(glob_func(ext)))

    # 去重并保持顺序
    seen = set()
    unique_files = []
    for f in files:
        s = str(f.resolve())
        if s not in seen:
            seen.add(s)
            unique_files.append(s)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Auto-generated filelist: {out_path.name}\n")
        f.write(f"# Source path: {path}\n")
        f.write(f"# Total files: {len(unique_files)}\n")
        for file in unique_files:
            f.write(file + "\n")

    print(f"[OK] Filelist generated: {out_path} ({len(unique_files)} files)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate Verilog/SystemVerilog filelist (.f)"
    )
    parser.add_argument("path", nargs="?", default=".", help="搜索目录 (默认: 当前目录)")
    parser.add_argument("-o", "--output", default="filelist.f", help="输出文件名 (默认: filelist.f)")
    parser.add_argument("-r", "--recursive", action="store_true", default=True, help="递归搜索 (默认)")
    parser.add_argument("-n", "--no-recursive", dest="recursive", action="store_false", help="非递归搜索")
    parser.add_argument("-e", "--ext", default="v,sv,vhd", help="文件扩展名，逗号分隔 (默认: v,sv,vhd)")
    args = parser.parse_args()

    extensions = [f"*.{e.strip()}" for e in args.ext.split(",")]
    return gen_flist(args.path, args.output, args.recursive, extensions)


if __name__ == "__main__":
    sys.exit(main())
