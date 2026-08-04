#!/usr/bin/env python3
"""One-shot YAML → docs + full DV artifact pack (no RTL)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from yml_model import default_output_dir, load_yml_model, load_top_model, stem_name
from yml2bus_adapters import generate_adapters
from yml2excel import generate_excel
from yml2ral_lib import generate_ral_lib
from yml2reg_c import generate_c_header
from yml2regmap_export import write_csv, write_json
from yml2regs_init import generate_c_init, generate_c_init_h, generate_sv_init
from yml2sv_define import generate_c_define, generate_sv_define
from yml2sysmap import generate_sysmap
from yml2uvm_ral import generate_uvm_ral
from yml2uvm_ral_top import generate_top_ral
from yml2xml import generate_xml


def _emit_module_pack(model: dict, out_dir: Path, targets: set, guard: str, fill_gaps: bool) -> list:
    name = stem_name(model)
    lower = name.lower()
    generated = []

    if "xml" in targets:
        path = out_dir / f"{name}.xml"
        path.write_text(generate_xml(model), encoding="utf-8")
        generated.append(str(path))
    if "excel" in targets or "xlsx" in targets or "table" in targets:
        path = out_dir / f"{name}.xlsx"
        generate_excel(model, path)
        generated.append(str(path))
    if "h" in targets or "header" in targets or "c" in targets:
        path = out_dir / f"{lower}.h"
        path.write_text(
            generate_c_header(model, header_guard=guard or None, fill_gaps=fill_gaps),
            encoding="utf-8",
        )
        generated.append(str(path))
    if "sysmap" in targets:
        path = out_dir / f"{lower}_sysmap.h"
        path.write_text(generate_sysmap(model), encoding="utf-8")
        generated.append(str(path))
    if "ral" in targets or "regmodel" in targets or "uvm" in targets:
        path = out_dir / f"{name}_ral.svh"
        path.write_text(generate_uvm_ral(model), encoding="utf-8")
        generated.append(str(path))
    if "define" in targets or "svh" in targets:
        c_path = out_dir / f"{lower}_regs_define.h"
        sv_path = out_dir / f"{lower}_regs_define.svh"
        c_path.write_text(generate_c_define(model), encoding="utf-8")
        sv_path.write_text(generate_sv_define(model), encoding="utf-8")
        generated.extend([str(c_path), str(sv_path)])
    if "init" in targets:
        for fname, text in (
            (f"{lower}_regs_init.sv", generate_sv_init(model)),
            (f"{lower}_regs_init.h", generate_c_init_h(model)),
            (f"{lower}_regs_init.c", generate_c_init(model)),
        ):
            path = out_dir / fname
            path.write_text(text, encoding="utf-8")
            generated.append(str(path))
    if "ral_lib" in targets or "rallib" in targets:
        path = out_dir / f"{name}_regs_ral_lib.svh"
        path.write_text(generate_ral_lib(model), encoding="utf-8")
        generated.append(str(path))
    if "json" in targets or "csv" in targets or "regmap" in targets:
        if "json" in targets or "regmap" in targets:
            path = out_dir / f"{name}_regmap.json"
            write_json(model, path)
            generated.append(str(path))
        if "csv" in targets or "regmap" in targets:
            path = out_dir / f"{name}_regmap.csv"
            write_csv(model, path)
            generated.append(str(path))
    if "adapter" in targets or "adapters" in targets:
        path = out_dir / "yml2reg_bus_adapters.svh"
        path.write_text(generate_adapters(model), encoding="utf-8")
        generated.append(str(path))
    return generated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate full docs/DV pack from yml2reg YAML (module or top)"
    )
    parser.add_argument("yaml_file", help="Module YAML or top YAML with blocks:[]")
    parser.add_argument("-o", "--output-dir", default="")
    parser.add_argument(
        "--targets",
        default="xml,excel,h,sysmap,ral,define,init,ral_lib,regmap,adapter",
        help="Comma-separated targets (default: full pack)",
    )
    parser.add_argument("-g", "--guard", default="")
    parser.add_argument("--no-fill-gaps", action="store_true")
    args = parser.parse_args(argv)

    yaml_path = Path(args.yaml_file)
    out_dir = default_output_dir(yaml_path, args.output_dir or None)
    targets = {t.strip().lower() for t in args.targets.split(",") if t.strip()}

    # detect top YAML
    is_top = False
    try:
        import yaml as _yaml

        raw = _yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        is_top = bool(raw.get("type") == "top" or raw.get("blocks"))
    except Exception:
        is_top = False

    generated = []
    if is_top:
        top = load_top_model(yaml_path)
        # emit each child pack
        for child in top["blocks"]:
            generated.extend(
                _emit_module_pack(
                    child, out_dir, targets, args.guard, not args.no_fill_gaps
                )
            )
        if "ral" in targets or "regmodel" in targets or "top" in targets:
            path = out_dir / f"{stem_name(top)}_ral_top.svh"
            path.write_text(generate_top_ral(top), encoding="utf-8")
            generated.append(str(path))
        if "adapter" in targets or "adapters" in targets:
            path = out_dir / "yml2reg_bus_adapters.svh"
            path.write_text(generate_adapters(top), encoding="utf-8")
            generated.append(str(path))
    else:
        model = load_yml_model(yaml_path)
        generated.extend(
            _emit_module_pack(
                model, out_dir, targets, args.guard, not args.no_fill_gaps
            )
        )

    if not generated:
        print("Error: no valid targets selected", file=sys.stderr)
        return 2
    for p in generated:
        print(f"Generated: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
