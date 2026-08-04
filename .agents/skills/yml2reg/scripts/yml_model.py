#!/usr/bin/env python3
"""Shared YAML register-map model for yml2reg deliverables.

Normalizes the existing yml2reg YAML (RTL source) into a structure that matches
the Spirit/IP-XACT XML converter I/O used by xml_reg_converter:
  - Excel register tables
  - C register headers
  - sysmap fragments
  - Spirit XML

Access tokens accept both lowercase (yml2reg) and uppercase (XML/C) forms.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


ACCESS_MAP = {
    "rw": "RW",
    "ro": "RO",
    "wo": "WO",
    "w1t": "W1T",
    "wc": "WC",
    "rsvd": "RSVD",
}

INTERRUPT_SUFFIXES = [
    ("RAW", 0x00),
    ("STAT", 0x04),
    ("MASK", 0x08),
    ("SET", 0x0C),
    ("CLR", 0x10),
    ("MODE", 0x14),
    ("POLAR", 0x18),
]


def normalize_access(access: Any, default: str = "RW") -> str:
    if access is None:
        return default
    text = str(access).strip()
    if not text:
        return default
    key = text.lower()
    if key in ACCESS_MAP:
        return ACCESS_MAP[key]
    return text.upper()


def fmt_hex(value: Any, width: Optional[int] = None) -> str:
    """Format an int/str as 0x... hex without forcing fixed width."""
    if value is None:
        return "0x0"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return "0x0"
        if text.lower().startswith("0x"):
            num = int(text, 0)
        elif text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            num = int(text, 0)
        else:
            try:
                num = int(text, 0)
            except ValueError:
                return text
    else:
        num = int(value)
    if width is not None and width > 0:
        nibbles = max(1, (width + 3) // 4)
        return f"0x{num:0{nibbles}x}"
    return f"0x{num:x}"


def _field_from_yaml(field: dict, reg_access: str) -> dict:
    lsb = int(field.get("lsb", field.get("bit_offset", 0)))
    bits = int(field.get("bits", field.get("bit_width", 1)))
    out = {
        "name": str(field["name"]).strip(),
        "bit_offset": lsb,
        "bit_width": bits,
        "access": normalize_access(field.get("access"), reg_access),
        "description": str(field.get("description", "") or ""),
        "reset": fmt_hex(field.get("reset", 0)),
    }
    # lock_* keys used by yml2reg demo YAML / CRG flows
    if "lock_lsb" in field or "lockOffset" in field:
        out["lockOffset"] = int(field.get("lock_lsb", field.get("lockOffset")))
    if "lock_bits" in field or "lockWidth" in field:
        out["lockWidth"] = int(field.get("lock_bits", field.get("lockWidth", 1)))
    if "lock_value" in field or "lockValue" in field:
        out["lockValue"] = fmt_hex(field.get("lock_value", field.get("lockValue", 0)))
    return out


def _infer_reg_access(fields: list, explicit: Any = None) -> str:
    """Prefer explicit access; else infer RO when every field is RO."""
    if explicit is not None and str(explicit).strip():
        return normalize_access(explicit, "RW")
    if fields and all(f.get("access") == "RO" for f in fields):
        return "RO"
    return "RW"


def _register_from_yaml(reg: dict) -> dict:
    # Field access may be parsed first with a temporary default, then re-normalized
    # after register-level access is known.
    provisional = "RW"
    fields = [_field_from_yaml(f, provisional) for f in (reg.get("fields") or [])]
    fields.sort(key=lambda f: f["bit_offset"])
    reg_access = _infer_reg_access(fields, reg.get("access"))
    # Prefer explicit register reset; else OR field resets into a word.
    if "reset" in reg and reg["reset"] is not None:
        reset_val = fmt_hex(reg["reset"])
    else:
        word = 0
        for f in fields:
            try:
                freset = int(f["reset"], 0)
            except ValueError:
                freset = 0
            word |= (freset & ((1 << f["bit_width"]) - 1)) << f["bit_offset"]
        reset_val = fmt_hex(word)

    return {
        "name": str(reg["name"]).strip(),
        "description": str(reg.get("description", "") or ""),
        "offset": fmt_hex(reg.get("offset", 0)),
        "size": int(reg.get("size", 32)),
        "access": reg_access,
        "reset": reset_val,
        "fields": fields,
    }


def _interrupt_from_yaml(intp: dict) -> dict:
    access = normalize_access(intp.get("access"), "RO")
    fields = [_field_from_yaml(f, access) for f in (intp.get("fields") or [])]
    fields.sort(key=lambda f: f["bit_offset"])
    base_offset = fmt_hex(intp.get("offset", 0))
    bit_offset = fields[0]["bit_offset"] if fields else 0
    reset_val = fmt_hex(intp.get("reset", 0))

    int_registers = []
    for suffix, delta in INTERRUPT_SUFFIXES:
        # rals: RAW=RO, STAT=RO, MASK/MODE/POLAR=RW, SET=WO, CLR=WC
        if suffix == "RAW":
            reg_access = "RO"
        elif suffix == "STAT":
            reg_access = "RO"
        elif suffix == "SET":
            reg_access = "WO"
        elif suffix == "CLR":
            reg_access = "WC"
        else:
            reg_access = "RW"
        reg_offset = fmt_hex(int(base_offset, 0) + delta)
        reg_name = f"{intp['name']}_{suffix.lower()}"
        synth_fields = []
        for f in fields:
            synth_fields.append(
                {
                    "name": f"{f['name']}_{suffix.lower()}",
                    "description": f["description"],
                    "bit_offset": f["bit_offset"],
                    "bit_width": f["bit_width"],
                    "access": reg_access,
                    "reset": f["reset"],
                }
            )
        int_registers.append(
            {
                "name": reg_name,
                "description": str(intp.get("description", "") or ""),
                "offset": reg_offset,
                "size": int(intp.get("size", 32)),
                "access": reg_access,
                "reset": reset_val,
                "fields": synth_fields,
            }
        )

    return {
        "name": str(intp["name"]).strip(),
        "description": str(intp.get("description", "") or ""),
        "base_offset": base_offset,
        "bit_offset": bit_offset,
        "reset": reset_val,
        "size": int(intp.get("size", 32)),
        "access": access,
        "fields": fields,
        "registers": int_registers,
    }


def load_yml_model(yaml_path: Path) -> Dict[str, Any]:
    """Load and normalize a yml2reg YAML into the shared register model."""
    path = Path(yaml_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"yaml file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    if not isinstance(raw, dict) or "name" not in raw:
        raise ValueError("YAML must be a mapping with at least 'name'")

    name = str(raw["name"]).strip()
    protocol = str(raw.get("protocol", "apb")).strip().lower()
    base_address = fmt_hex(raw.get("base_address", raw.get("offset", 0)))
    range_val = fmt_hex(raw.get("range", 0x1000))
    width = int(raw.get("width", (int(raw.get("bytes", 4)) * 8)))

    registers = [_register_from_yaml(r) for r in (raw.get("registers") or [])]
    registers.sort(key=lambda r: int(r["offset"], 0))

    interrupts = [_interrupt_from_yaml(i) for i in (raw.get("interrupts") or [])]
    interrupts.sort(key=lambda i: int(i["base_offset"], 0))

    return {
        "source_path": str(path),
        "component_name": name,
        "version": str(raw.get("version", "1.0")),
        "block_name": str(raw.get("block_name", name)),
        "base_address": base_address,
        "range": range_val,
        "width": width,
        "bytes": int(raw.get("bytes", width // 8)),
        "protocol": protocol,
        "description": str(raw.get("description", f"{name} regfile") or f"{name} regfile"),
        "parent_base": raw.get("parent_base"),  # e.g. AP_BASE for sysmap
        "parent_offset": raw.get("parent_offset"),  # absolute offset from parent
        # DV / RAL options
        "hdl_path": str(raw.get("hdl_path", "") or ""),
        "hdl_path_prefix": str(raw.get("hdl_path_prefix", "") or ""),
        "coverage": bool(raw.get("coverage", False)),
        "is_top": bool(raw.get("type") == "top" or raw.get("blocks")),
        "registers": registers,
        "interrupts": interrupts,
        "raw": raw,
    }


def default_output_dir(yaml_path: Path, output_dir: Optional[str] = None) -> Path:
    """Write beside the YAML by default; optional override directory."""
    ypath = Path(yaml_path).expanduser().resolve()
    if output_dir:
        out = Path(output_dir).expanduser().resolve()
    else:
        out = ypath.parent
    out.mkdir(parents=True, exist_ok=True)
    return out


def stem_name(model: Dict[str, Any]) -> str:
    return str(model["component_name"]).strip()


def hex_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    return int(str(value).strip(), 0)


def all_flat_registers(model: Dict[str, Any]) -> List[dict]:
    """Registers + expanded interrupt bank registers, sorted by offset."""
    regs = list(model.get("registers") or [])
    for intp in model.get("interrupts") or []:
        regs.extend(intp.get("registers") or [])
    regs.sort(key=lambda r: hex_int(r["offset"]))
    return regs


def field_hdl_slice_name(reg: dict, field: dict, model: Dict[str, Any]) -> str:
    """Best-effort HDL slice name for backdoor paths.

    yml2reg RTL uses bare field names for normal regs and
    <int>_<field> for interrupt source ports; interrupt bank
    fields use expanded names in the model.
    """
    # Optional per-field override
    if field.get("hdl_path"):
        return str(field["hdl_path"])
    if reg.get("hdl_path_slice_prefix"):
        return f"{reg['hdl_path_slice_prefix']}_{field['name']}"
    return str(field["name"])


def resolve_hdl_root(model: Dict[str, Any]) -> str:
    """Combine hdl_path_prefix + hdl_path for block root."""
    prefix = str(model.get("hdl_path_prefix") or "").strip()
    path = str(model.get("hdl_path") or "").strip()
    if prefix and path:
        return f"{prefix}.{path}"
    return path or prefix


def load_top_model(yaml_path: Path) -> Dict[str, Any]:
    """Load a top YAML that lists child blocks for multi-block RAL/sysmap.

    Top YAML example::

        name: SOC_TOP
        type: top
        base_address: 0x0
        protocol: apb
        coverage: true
        blocks:
          - yaml: demo_docs.yml
            base_address: 0x1000
            instance: u_sys_ctrl
            hdl_path: tb.dut.u_sys_ctrl
    """
    path = Path(yaml_path).expanduser().resolve()
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict) or "name" not in raw:
        raise ValueError("top YAML must be a mapping with 'name'")
    if not raw.get("blocks"):
        raise ValueError("top YAML requires non-empty 'blocks' list")

    children: List[Dict[str, Any]] = []
    for entry in raw["blocks"]:
        if not isinstance(entry, dict) or "yaml" not in entry:
            raise ValueError(f"each blocks[] entry needs 'yaml': {entry}")
        child_path = (path.parent / str(entry["yaml"])).resolve()
        child = load_yml_model(child_path)
        # overrides
        if "base_address" in entry:
            child["base_address"] = fmt_hex(entry["base_address"])
        if "name" in entry:
            child["component_name"] = str(entry["name"]).strip()
        if "instance" in entry:
            child["instance"] = str(entry["instance"]).strip()
        else:
            child["instance"] = stem_name(child).lower()
        if "hdl_path" in entry:
            child["hdl_path"] = str(entry["hdl_path"])
        if "hdl_path_prefix" in entry:
            child["hdl_path_prefix"] = str(entry["hdl_path_prefix"])
        if "protocol" in entry:
            child["protocol"] = str(entry["protocol"]).lower()
        children.append(child)

    return {
        "source_path": str(path),
        "component_name": str(raw["name"]).strip(),
        "version": str(raw.get("version", "1.0")),
        "base_address": fmt_hex(raw.get("base_address", 0)),
        "range": fmt_hex(raw.get("range", 0x10000000)),
        "width": int(raw.get("width", 32)),
        "protocol": str(raw.get("protocol", "apb")).lower(),
        "description": str(raw.get("description", "top regmap") or "top regmap"),
        "coverage": bool(raw.get("coverage", False)),
        "hdl_path": str(raw.get("hdl_path", "") or ""),
        "hdl_path_prefix": str(raw.get("hdl_path_prefix", "") or ""),
        "is_top": True,
        "blocks": children,
        "raw": raw,
    }
