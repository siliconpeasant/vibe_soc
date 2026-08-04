#!/usr/bin/env python3
"""YAML → JSON/CSV regmap export for scripts / cocotb / coverage tools."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from yml_model import all_flat_registers, default_output_dir, hex_int, load_yml_model, stem_name


def model_to_dict(model: dict) -> dict:
    regs = []
    for r in all_flat_registers(model):
        regs.append(
            {
                "name": r["name"],
                "offset": r["offset"],
                "offset_int": hex_int(r["offset"]),
                "access": r.get("access", "RW"),
                "reset": r.get("reset", "0x0"),
                "reset_int": hex_int(r.get("reset", 0)),
                "description": r.get("description", ""),
                "fields": [
                    {
                        "name": f["name"],
                        "lsb": int(f["bit_offset"]),
                        "bits": int(f["bit_width"]),
                        "access": f.get("access", "RW"),
                        "reset": f.get("reset", "0x0"),
                        "description": f.get("description", ""),
                    }
                    for f in (r.get("fields") or [])
                ],
            }
        )
    return {
        "name": stem_name(model),
        "base_address": model.get("base_address"),
        "range": model.get("range"),
        "width": model.get("width"),
        "protocol": model.get("protocol"),
        "description": model.get("description"),
        "hdl_path": model.get("hdl_path"),
        "hdl_path_prefix": model.get("hdl_path_prefix"),
        "registers": regs,
    }


def write_json(model: dict, path: Path) -> None:
    path.write_text(json.dumps(model_to_dict(model), indent=2) + "\n", encoding="utf-8")


def write_csv(model: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "register",
                "offset",
                "reg_access",
                "reg_reset",
                "field",
                "lsb",
                "bits",
                "field_access",
                "field_reset",
                "description",
            ]
        )
        for r in all_flat_registers(model):
            fields = r.get("fields") or [{"name": "", "bit_offset": 0, "bit_width": 0, "access": "", "reset": "", "description": r.get("description", "")}]
            for f in fields:
                w.writerow(
                    [
                        r["name"],
                        r["offset"],
                        r.get("access", ""),
                        r.get("reset", ""),
                        f.get("name", ""),
                        f.get("bit_offset", ""),
                        f.get("bit_width", ""),
                        f.get("access", ""),
                        f.get("reset", ""),
                        f.get("description", r.get("description", "")),
                    ]
                )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export regmap JSON/CSV from YAML")
    parser.add_argument("yaml_file")
    parser.add_argument("-o", "--output-dir", default="")
    args = parser.parse_args(argv)

    yaml_path = Path(args.yaml_file)
    model = load_yml_model(yaml_path)
    out_dir = default_output_dir(yaml_path, args.output_dir or None)
    stem = stem_name(model)
    jpath = out_dir / f"{stem}_regmap.json"
    cpath = out_dir / f"{stem}_regmap.csv"
    write_json(model, jpath)
    write_csv(model, cpath)
    print(f"Generated: {jpath}")
    print(f"Generated: {cpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
