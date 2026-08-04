#!/usr/bin/env python3
"""YAML → Spirit/IP-XACT XML (same schema as xml_reg_converter)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from yml_model import default_output_dir, load_yml_model, stem_name


def _emit_field(lines: list, f: dict, indent: str = "      ") -> None:
    pad = indent + "  "
    lines.append(f"{indent}<spirit:field>")
    lines.append(f"{pad}<spirit:name>{escape(f['name'])}</spirit:name>")
    if f.get("description"):
        lines.append(f"{pad}<spirit:description>{escape(f['description'])}</spirit:description>")
    lines.append(f"{pad}<spirit:bitOffset>{f['bit_offset']}</spirit:bitOffset>")
    lines.append(f"{pad}<spirit:bitWidth>{f['bit_width']}</spirit:bitWidth>")
    lines.append(f"{pad}<spirit:access>{f['access']}</spirit:access>")
    if "lockOffset" in f:
        lines.append(f"{pad}<spirit:lockOffset>{f['lockOffset']}</spirit:lockOffset>")
    if "lockWidth" in f:
        lines.append(f"{pad}<spirit:lockWidth>{f['lockWidth']}</spirit:lockWidth>")
    if "lockValue" in f:
        lines.append(f"{pad}<spirit:lockValue>{f['lockValue']}</spirit:lockValue>")
    lines.append(f"{indent}</spirit:field>")


def generate_xml(model: dict) -> str:
    lines: list[str] = []
    lines.append('<?xml version="1.0" ?>')
    lines.append('<spirit:component xmlns:spirit="http://www.siliconpeasant.com">')
    lines.append(f'  <spirit:name>{escape(model["component_name"])}</spirit:name>')
    lines.append(f'  <spirit:version>{escape(model["version"])}</spirit:version>')
    lines.append("  <spirit:addressBlock>")
    lines.append(f'    <spirit:name>{escape(model["block_name"])}</spirit:name>')
    if model.get("description"):
        lines.append(f'    <spirit:description>{escape(model["description"])}</spirit:description>')
    lines.append(f'    <spirit:baseAddress>{model["base_address"]}</spirit:baseAddress>')
    lines.append(f'    <spirit:range>{model["range"]}</spirit:range>')
    lines.append(f'    <spirit:width>{model["width"]}</spirit:width>')
    lines.append("    <spirit:byteVisit>1</spirit:byteVisit>")
    lines.append("    <spirit:usage>register</spirit:usage>")
    lines.append(f'    <spirit:protocol>{model["protocol"]}</spirit:protocol>')

    for reg in model["registers"]:
        lines.append("    <spirit:register>")
        lines.append(f'      <spirit:name>{escape(reg["name"])}</spirit:name>')
        if reg.get("description"):
            lines.append(
                f'      <spirit:description>{escape(reg["description"])}</spirit:description>'
            )
        lines.append(f'      <spirit:addressOffset>{reg["offset"]}</spirit:addressOffset>')
        lines.append(f'      <spirit:size>{reg["size"]}</spirit:size>')
        lines.append(f'      <spirit:access>{reg["access"]}</spirit:access>')
        lines.append("      <spirit:reset>")
        lines.append(f'        <spirit:value>{reg["reset"]}</spirit:value>')
        lines.append("      </spirit:reset>")
        for f in reg["fields"]:
            _emit_field(lines, f, indent="      ")
        lines.append("    </spirit:register>")

    for intp in model["interrupts"]:
        lines.append("    <spirit:interrupt>")
        lines.append(f'      <spirit:name>{escape(intp["name"])}</spirit:name>')
        if intp.get("description"):
            lines.append(
                f'      <spirit:description>{escape(intp["description"])}</spirit:description>'
            )
        lines.append(f'      <spirit:addressOffset>{intp["base_offset"]}</spirit:addressOffset>')
        lines.append(f'      <spirit:size>{intp["size"]}</spirit:size>')
        lines.append(f'      <spirit:access>{intp["access"]}</spirit:access>')
        lines.append("      <spirit:reset>")
        lines.append(f'        <spirit:value>{intp["reset"]}</spirit:value>')
        lines.append("      </spirit:reset>")
        for f in intp["fields"]:
            _emit_field(lines, f, indent="      ")
        lines.append("    </spirit:interrupt>")

    lines.append("  </spirit:addressBlock>")
    lines.append("</spirit:component>")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert yml2reg YAML to Spirit/IP-XACT XML")
    parser.add_argument("yaml_file", help="Input YAML register description")
    parser.add_argument("-o", "--output-dir", default="", help="Output directory (default: beside YAML)")
    args = parser.parse_args(argv)

    yaml_path = Path(args.yaml_file)
    model = load_yml_model(yaml_path)
    out_dir = default_output_dir(yaml_path, args.output_dir or None)
    out_path = out_dir / f"{stem_name(model)}.xml"
    out_path.write_text(generate_xml(model), encoding="utf-8")
    print(f"Generated: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
