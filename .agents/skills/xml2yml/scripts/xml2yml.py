#!/usr/bin/env python3
"""IP-XACT / Spirit XML → yml2reg YAML.

Supports:
  1. Project Spirit dialect emitted by yml2reg ``yml2xml``
     (xmlns spirit=http://www.siliconpeasant.com, optional ``interrupt`` nodes,
     optional field lockOffset/lockWidth/lockValue).
  2. Common IEEE Spirit 1.4/1.5 and IP-XACT 1685 memoryMap / addressBlock trees
     (``spirit:`` / ``ipxact:`` namespaces; local-name matching).

One addressBlock → one YAML file. Multiple blocks write multiple YAML files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


ACCESS_TO_YML = {
    "rw": "rw",
    "ro": "ro",
    "wo": "wo",
    "w1t": "w1t",
    "wc": "wc",
    "rsvd": "rsvd",
    "read-write": "rw",
    "read-only": "ro",
    "write-only": "wo",
    "read-writeonce": "rw",
    "writeonce": "wo",
    "readwrite": "rw",
    "readonly": "ro",
    "writeonly": "wo",
    "readwriteclear": "wc",
    "write1toclear": "wc",
    "w1c": "wc",
    "w1s": "w1t",
}

# Interrupt bank suffixes produced by yml2reg expansion (for optional fold).
_IRQ_BANK_SUFFIXES = ("_raw", "_stat", "_mask", "_set", "_clr", "_mode", "_polar")


def local_name(tag: str) -> str:
    if tag is None:
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    if ":" in tag:
        return tag.split(":", 1)[-1]
    return tag


def child_text(parent: ET.Element, *names: str, default: str = "") -> str:
    wanted = {n.lower() for n in names}
    for child in list(parent):
        if local_name(child.tag).lower() in wanted:
            text = (child.text or "").strip()
            if text:
                return text
    return default


def children_named(parent: ET.Element, *names: str) -> List[ET.Element]:
    wanted = {n.lower() for n in names}
    return [c for c in list(parent) if local_name(c.tag).lower() in wanted]


def find_all(root: ET.Element, *names: str) -> List[ET.Element]:
    wanted = {n.lower() for n in names}
    return [el for el in root.iter() if local_name(el.tag).lower() in wanted]


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    # Strip units like "'h" Verilog styles that sometimes leak into XML.
    text = text.replace("'", "")
    try:
        return int(text, 0)
    except ValueError:
        # Binary/hex with prefixes like 32'h0a
        m = re.search(r"(0x[0-9a-fA-F]+|\d+)", text)
        if m:
            return int(m.group(1), 0)
        return default


def fmt_hex(value: Any) -> str:
    return f"0x{parse_int(value):x}"


def normalize_access(raw: Any, default: str = "rw") -> str:
    if raw is None:
        return default
    key = str(raw).strip().lower().replace("_", "").replace(" ", "")
    if not key:
        return default
    if key in ACCESS_TO_YML:
        return ACCESS_TO_YML[key]
    # Already short form?
    if key in {"rw", "ro", "wo", "w1t", "wc", "rsvd"}:
        return key
    return default


def _field_reset(field_el: ET.Element, reg_reset: int, bit_offset: int, bit_width: int) -> str:
    # Prefer field-local reset.
    for resets in children_named(field_el, "resets", "reset"):
        if local_name(resets.tag).lower() == "reset":
            val = child_text(resets, "value")
            if val:
                return fmt_hex(val)
        for reset in children_named(resets, "reset"):
            val = child_text(reset, "value")
            if val:
                return fmt_hex(val)
    direct = child_text(field_el, "reset", "resets")
    if direct:
        return fmt_hex(direct)
    # Slice from register reset when no field reset is present.
    if bit_width <= 0:
        return "0x0"
    mask = (1 << bit_width) - 1
    return fmt_hex((reg_reset >> bit_offset) & mask)


def _parse_field(field_el: ET.Element, reg_reset: int) -> Dict[str, Any]:
    name = child_text(field_el, "name")
    if not name:
        raise ValueError("field missing <name>")
    bit_offset = parse_int(
        child_text(field_el, "bitOffset", "bitoffset", "bit_offset", default="0")
    )
    bit_width = parse_int(
        child_text(field_el, "bitWidth", "bitwidth", "bit_width", default="1"),
        default=1,
    )
    access = normalize_access(child_text(field_el, "access"), "rw")
    # IEEE modifiedWriteValue can refine access.
    mwv = child_text(field_el, "modifiedWriteValue", "modifiedwritevalue").lower()
    if mwv in {"oneToClear", "onetoclear", "clear", "zeroToClear", "zerotoclear"}:
        access = "wc"
    elif mwv in {"oneToSet", "onetoset", "set"}:
        access = "w1t"

    out: Dict[str, Any] = {
        "name": name,
        "lsb": bit_offset,
        "bits": bit_width,
        "access": access,
        "reset": _field_reset(field_el, reg_reset, bit_offset, bit_width),
    }
    desc = child_text(field_el, "description")
    if desc:
        out["description"] = desc

    # Project dialect lock bits (yml2xml).
    lock_off = child_text(field_el, "lockOffset", "lockoffset", "lock_lsb")
    lock_w = child_text(field_el, "lockWidth", "lockwidth", "lock_bits")
    lock_v = child_text(field_el, "lockValue", "lockvalue", "lock_value")
    if lock_off:
        out["lock_lsb"] = parse_int(lock_off)
    if lock_w:
        out["lock_bits"] = parse_int(lock_w, default=1)
    if lock_v:
        out["lock_value"] = fmt_hex(lock_v)
    return out


def _register_reset(reg_el: ET.Element) -> int:
    for resets in children_named(reg_el, "resets", "reset"):
        if local_name(resets.tag).lower() == "reset":
            val = child_text(resets, "value")
            if val:
                return parse_int(val)
        for reset in children_named(resets, "reset"):
            val = child_text(reset, "value")
            if val:
                return parse_int(val)
    return 0


def _parse_register_like(reg_el: ET.Element) -> Dict[str, Any]:
    name = child_text(reg_el, "name")
    if not name:
        raise ValueError(f"{local_name(reg_el.tag)} missing <name>")
    offset = parse_int(
        child_text(reg_el, "addressOffset", "addressoffset", "offset", default="0")
    )
    size = parse_int(child_text(reg_el, "size", default="32"), default=32)
    reg_reset = _register_reset(reg_el)
    fields = [_parse_field(f, reg_reset) for f in children_named(reg_el, "field")]
    fields.sort(key=lambda f: f["lsb"])
    out: Dict[str, Any] = {"name": name}
    desc = child_text(reg_el, "description")
    if desc:
        out["description"] = desc
    out["offset"] = fmt_hex(offset)
    # Keep size only when non-default 32-bit word.
    if size and size != 32:
        out["size"] = size
    access = child_text(reg_el, "access")
    if access:
        out["access"] = normalize_access(access)
    out["fields"] = fields
    return out


def _parse_interrupt(int_el: ET.Element) -> Dict[str, Any]:
    """Project dialect compact interrupt group (not expanded banks)."""
    name = child_text(int_el, "name")
    if not name:
        raise ValueError("interrupt missing <name>")
    offset = parse_int(
        child_text(int_el, "addressOffset", "addressoffset", "offset", default="0")
    )
    reg_reset = _register_reset(int_el)
    fields = [_parse_field(f, reg_reset) for f in children_named(int_el, "field")]
    fields.sort(key=lambda f: f["lsb"])
    out: Dict[str, Any] = {
        "name": name,
        "offset": fmt_hex(offset),
        "fields": fields,
    }
    desc = child_text(int_el, "description")
    if desc:
        out["description"] = desc
    access = child_text(int_el, "access")
    if access:
        out["access"] = normalize_access(access, "ro")
    return out


def _parse_address_block(block_el: ET.Element, component_name: str, version: str) -> Dict[str, Any]:
    block_name = child_text(block_el, "name") or component_name
    description = child_text(block_el, "description")
    base_address = fmt_hex(child_text(block_el, "baseAddress", "baseaddress", default="0x0"))
    range_val = fmt_hex(child_text(block_el, "range", default="0x1000"))
    width = parse_int(child_text(block_el, "width", default="32"), default=32)
    protocol = child_text(block_el, "protocol", default="apb").lower() or "apb"
    if protocol not in {"apb", "ahb", "dab"}:
        # IP-XACT may use busInterface names; default apb for regfile.
        protocol = "apb"

    registers = [_parse_register_like(r) for r in children_named(block_el, "register")]
    interrupts = [_parse_interrupt(i) for i in children_named(block_el, "interrupt")]

    # IEEE IP-XACT sometimes nests registerFile → register.
    for regfile in children_named(block_el, "registerFile", "registerfile"):
        for r in children_named(regfile, "register"):
            registers.append(_parse_register_like(r))

    registers.sort(key=lambda r: parse_int(r["offset"]))
    interrupts.sort(key=lambda i: parse_int(i["offset"]))

    data: Dict[str, Any] = {
        "name": component_name or block_name,
        "version": version or "1.0",
        "bytes": max(1, width // 8),
        "base_address": base_address,
        "range": range_val,
        "protocol": protocol,
    }
    if block_name and block_name != data["name"]:
        data["block_name"] = block_name
    if description:
        data["description"] = description
    data["registers"] = registers
    if interrupts:
        data["interrupts"] = interrupts
    return data


def _iter_address_blocks(root: ET.Element) -> Iterable[Tuple[str, str, ET.Element]]:
    """Yield (component_name, version, addressBlock element)."""
    components = find_all(root, "component")
    if not components and local_name(root.tag).lower() == "component":
        components = [root]

    if components:
        for comp in components:
            cname = child_text(comp, "name") or "UNNAMED"
            version = child_text(comp, "version", default="1.0") or "1.0"
            # Direct children (project dialect).
            blocks = children_named(comp, "addressBlock", "addressblock")
            # Nested memoryMaps / memoryMap.
            for mmap in find_all(comp, "memoryMap", "memorymap"):
                blocks.extend(children_named(mmap, "addressBlock", "addressblock"))
            # Also search flat under component.
            if not blocks:
                blocks = [
                    el
                    for el in find_all(comp, "addressBlock", "addressblock")
                    if el is not comp
                ]
            # De-dup while preserving order.
            seen: set[int] = set()
            unique: List[ET.Element] = []
            for b in blocks:
                key = id(b)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(b)
            if not unique:
                raise ValueError(f"component '{cname}' has no addressBlock")
            for block in unique:
                yield cname, version, block
        return

    # Bare addressBlock document.
    blocks = find_all(root, "addressBlock", "addressblock")
    if not blocks:
        raise ValueError("no spirit/ipxact component or addressBlock found in XML")
    for block in blocks:
        bname = child_text(block, "name") or "UNNAMED"
        yield bname, "1.0", block


def fold_interrupt_banks(data: Dict[str, Any]) -> Dict[str, Any]:
    """Optionally collapse expanded *_raw/_stat/... register banks into interrupts[].

    Only folds when a full RAW..POLAR set is present with aligned offsets.
    """
    regs: List[Dict[str, Any]] = list(data.get("registers") or [])
    by_name = {r["name"].lower(): r for r in regs}
    used: set[str] = set()
    folded: List[Dict[str, Any]] = list(data.get("interrupts") or [])

    for reg in regs:
        name = reg["name"]
        low = name.lower()
        if not low.endswith("_raw"):
            continue
        base = name[: -len("_raw")]
        members = []
        ok = True
        for suf in _IRQ_BANK_SUFFIXES:
            key = f"{base}{suf}".lower()
            if key not in by_name:
                ok = False
                break
            members.append(by_name[key])
        if not ok:
            continue
        # Offset stride check: raw, +4, +8, ...
        base_off = parse_int(members[0]["offset"])
        for idx, m in enumerate(members):
            if parse_int(m["offset"]) != base_off + idx * 4:
                ok = False
                break
        if not ok:
            continue
        # Use RAW fields, strip _raw suffix from field names when present.
        raw_fields = []
        for f in members[0].get("fields") or []:
            fname = f["name"]
            if fname.lower().endswith("_raw"):
                fname = fname[: -len("_raw")]
            nf = dict(f)
            nf["name"] = fname
            nf["access"] = "ro"
            raw_fields.append(nf)
        entry: Dict[str, Any] = {
            "name": base,
            "offset": members[0]["offset"],
            "fields": raw_fields,
        }
        if members[0].get("description"):
            entry["description"] = members[0]["description"]
        folded.append(entry)
        for m in members:
            used.add(m["name"].lower())

    if not used:
        return data
    data = dict(data)
    data["registers"] = [r for r in regs if r["name"].lower() not in used]
    data["interrupts"] = folded
    return data


def xml_to_models(
    xml_path: Path,
    *,
    name_override: str = "",
    protocol_override: str = "",
    fold_interrupts: bool = False,
) -> List[Dict[str, Any]]:
    path = Path(xml_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"xml file not found: {path}")
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {path}: {exc}") from exc
    root = tree.getroot()

    models: List[Dict[str, Any]] = []
    for cname, version, block in _iter_address_blocks(root):
        data = _parse_address_block(block, cname, version)
        if name_override:
            data["name"] = name_override
        if protocol_override:
            proto = protocol_override.strip().lower()
            if proto not in {"apb", "ahb", "dab"}:
                raise ValueError("protocol must be apb, ahb, or dab")
            data["protocol"] = proto
        if fold_interrupts:
            data = fold_interrupt_banks(data)
        if not data.get("registers") and not data.get("interrupts"):
            raise ValueError(
                f"addressBlock '{data.get('block_name', data['name'])}' has no registers/interrupts"
            )
        models.append(data)
    return models


class _FlowFieldDumper(yaml.SafeDumper):
    """Dump compact field mappings on one line when small."""


def _represent_field_dict(dumper: yaml.SafeDumper, data: dict) -> Any:
    # Flow style only for leaf field dicts (have lsb/bits).
    if "lsb" in data and "bits" in data and "name" in data:
        return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=False)


_FlowFieldDumper.add_representer(dict, _represent_field_dict)


def dump_yml2reg_yaml(data: Dict[str, Any]) -> str:
    header = (
        "# Generated by xml2yml / ipxact2yml from IP-XACT/Spirit XML.\n"
        "# Do not hand-edit for production; re-run the converter after XML changes.\n"
        "# Feed this YAML to yml2reg tools (yml2reg, yml2docs, ...).\n"
    )
    body = yaml.dump(
        data,
        Dumper=_FlowFieldDumper,
        sort_keys=False,
        allow_unicode=True,
        width=120,
        default_flow_style=False,
    )
    return header + body


def convert_file(
    xml_file: str | Path,
    output_dir: str = "",
    *,
    name: str = "",
    protocol: str = "",
    fold_interrupts: bool = False,
) -> List[Path]:
    xml_path = Path(xml_file).expanduser().resolve()
    models = xml_to_models(
        xml_path,
        name_override=name,
        protocol_override=protocol,
        fold_interrupts=fold_interrupts,
    )
    if output_dir:
        out_dir = Path(output_dir).expanduser().resolve()
    else:
        out_dir = xml_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    multi = len(models) > 1
    for idx, model in enumerate(models):
        stem = str(model["name"]).strip() or xml_path.stem
        if multi:
            block = str(model.get("block_name") or stem)
            fname = f"{stem}_{block}.yml" if block != stem else f"{stem}_{idx}.yml"
        else:
            fname = f"{stem}.yml"
        # Sanitize path-hostile characters.
        fname = re.sub(r"[^\w.\-]+", "_", fname)
        out_path = out_dir / fname
        out_path.write_text(dump_yml2reg_yaml(model), encoding="utf-8")
        written.append(out_path)
    return written


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert IP-XACT / Spirit XML register maps to yml2reg YAML"
    )
    parser.add_argument("xml_file", help="Input Spirit/IP-XACT XML")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="",
        help="Output directory (default: beside XML)",
    )
    parser.add_argument("--name", default="", help="Override component name in YAML")
    parser.add_argument(
        "--protocol",
        default="",
        help="Override bus protocol: apb|ahb|dab",
    )
    parser.add_argument(
        "--fold-interrupts",
        action="store_true",
        help="Collapse expanded *_raw/_stat/... banks into interrupts[]",
    )
    args = parser.parse_args(argv)

    try:
        paths = convert_file(
            args.xml_file,
            args.output_dir,
            name=args.name,
            protocol=args.protocol,
            fold_interrupts=args.fold_interrupts,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for path in paths:
        print(f"Generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
