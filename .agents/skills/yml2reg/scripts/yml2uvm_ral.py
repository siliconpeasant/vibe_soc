#!/usr/bin/env python3
"""YAML → UVM register model (regmodel), aligned with rals_parser *_ral.svh.

Generates:
  - class reg_<BLK>_<REG> extends uvm_reg  (per register, incl. interrupt banks)
  - class reg_<BLK> extends uvm_reg_block
  - apb/ahb/dab maps + default_map
  - optional GET/SET helpers (rals-style RMW)
  - add_hdl_path_slice for backdoor (best-effort, matches yml2reg field names)

Does not emit full chip multi-block hierarchy (memoryMap); module-level only.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from yml_model import (
    all_flat_registers,
    default_output_dir,
    field_hdl_slice_name,
    load_yml_model,
    resolve_hdl_root,
    stem_name,
)


def _hex_int(v) -> int:
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    return int(str(v).strip(), 0)


def _cov_flag(model: dict) -> str:
    return "UVM_CVR_ALL" if model.get("coverage") else "UVM_NO_COVERAGE"


def _uvm_access(acc: str) -> str:
    a = str(acc).upper()
    # Map yml2reg / Spirit tokens to UVM field access strings
    mapping = {
        "RW": "RW",
        "RO": "RO",
        "WO": "WO",
        "WC": "WC",
        "W1T": "W1T",
        "W1C": "W1C",
        "RC": "RC",
        "RS": "RS",
        "RSVD": "RO",
    }
    return mapping.get(a, "RW")


def _field_mask(width: int, lsb: int, bits: int) -> str:
    """Return binary mask string with underscores every 4 bits (msb left)."""
    chars = []
    for i in range(width):
        if i and i % 4 == 0:
            chars.append("_")
        bit = width - 1 - i
        chars.append("1" if lsb <= bit < lsb + bits else "0")
    return "".join(chars)


def _all_regs(model: dict) -> list:
    return all_flat_registers(model)


def _emit_reg_class(lines: list, blk: str, reg: dict, width: int, coverage: str) -> None:
    rname = reg["name"]
    fields = reg["fields"]
    acc = str(reg.get("access", "RW")).upper()
    lines.append("")
    lines.append("//////////////////////////////////////////////////////////////////////////////////////////////")
    lines.append(f"// Definition of {blk}_{rname} Register")
    lines.append("//////////////////////////////////////////////////////////////////////////////////////////////")
    lines.append(f"class reg_{blk}_{rname} extends uvm_reg;")
    for f in fields:
        lines.append(f"  rand uvm_reg_field {f['name']};")
    lines.append("")
    lines.append("  // masks for read-modify-write helpers")
    lines.append(f"  const bit[{width - 1}:0] ALL_MASK = {width}'b{_field_mask(width, 0, width)};")
    for f in fields:
        lines.append(
            f"  const bit[{width - 1}:0] {f['name']}_MASK = "
            f"{width}'b{_field_mask(width, int(f['bit_offset']), int(f['bit_width']))};"
        )
    lines.append("")
    for f in fields:
        lines.append(f"  const int {f['name']}_LSB = {int(f['bit_offset'])};")
    lines.append("")
    lines.append(f"  static logic[{width - 1}:0] ALL_TMP = {width}'hz;")
    for f in fields:
        lines.append(f"  static logic[{width - 1}:0] {f['name']}_TMP = {width}'hz;")
    lines.append("  static uvm_status_e STATUS_TMP;")
    lines.append("")

    # GET
    lines.append("  task GET(ref   uvm_status_e status = STATUS_TMP,")
    lines.append(f"           ref   logic[{width - 1}:0] ALL = ALL_TMP,")
    for f in fields:
        lines.append(
            f"           ref   logic[{width - 1}:0] {f['name']} = {f['name']}_TMP,"
        )
    lines.append("           input uvm_path_e path = UVM_DEFAULT_PATH,")
    lines.append("           input uvm_reg_map map = null,")
    lines.append("           input uvm_sequence_base parent = null,")
    lines.append("           input int prior = -1,")
    lines.append("           input uvm_object extension = null,")
    lines.append('           input string fname = "",')
    lines.append("           input int lineno = 0);")
    lines.append("    uvm_reg_data_t rd_all;")
    lines.append("    if (parent == null) begin")
    lines.append('      uvm_reg_sequence#() reg_parent = new("default_parent_seq");')
    lines.append("      parent = reg_parent;")
    lines.append("    end")
    lines.append("    this.read(status, rd_all, path, map, parent, prior, extension, fname, lineno);")
    lines.append(f"    if (ALL !== {width}'hz) ALL = rd_all;")
    for f in fields:
        lines.append(
            f"    if ({f['name']} !== {width}'hz) "
            f"{f['name']} = (rd_all & {f['name']}_MASK) >> {f['name']}_LSB;"
        )
    lines.append("  endtask : GET")
    lines.append("")

    # SET (RMW)
    lines.append("  task SET(ref   uvm_status_e status = STATUS_TMP,")
    lines.append(f"           input logic[{width - 1}:0] ALL = {width}'hz,")
    for f in fields:
        lines.append(
            f"           input logic[{width - 1}:0] {f['name']} = {width}'hz,"
        )
    lines.append("           input uvm_path_e path = UVM_DEFAULT_PATH,")
    lines.append("           input uvm_reg_map map = null,")
    lines.append("           input uvm_sequence_base parent = null,")
    lines.append("           input int prior = -1,")
    lines.append("           input uvm_object extension = null,")
    lines.append('           input string fname = "",')
    lines.append("           input int lineno = 0);")
    lines.append("    uvm_reg_data_t write_data = 0;")
    lines.append("    uvm_reg_data_t write_mask = 0;")
    lines.append("    uvm_reg_data_t read_data = 0;")
    lines.append(f"    if (ALL !== {width}'hz) begin")
    lines.append("      write_data = ALL;")
    lines.append("      write_mask = ALL_MASK;")
    lines.append("    end else begin")
    for f in fields:
        lines.append(
            f"      if ({f['name']} !== {width}'hz) begin "
            f"write_mask |= {f['name']}_MASK; "
            f"write_data |= (({f['name']} << {f['name']}_LSB) & {f['name']}_MASK); end"
        )
    lines.append("    end")
    lines.append("    if (parent == null) begin")
    lines.append('      uvm_reg_sequence#() reg_parent = new("default_parent_seq");')
    lines.append("      parent = reg_parent;")
    lines.append("    end")
    lines.append("    if (ALL_MASK != write_mask) begin")
    lines.append(
        "      this.read(status, read_data, path, map, parent, prior, extension, fname, lineno);"
    )
    lines.append("      read_data = (read_data & (~write_mask)) | write_data;")
    lines.append("    end else begin")
    lines.append("      read_data = write_data;")
    lines.append("    end")
    lines.append(
        "    this.write(status, read_data, path, map, parent, prior, extension, fname, lineno);"
    )
    lines.append("  endtask : SET")
    lines.append("")

    lines.append(f'  function new(string name = "{rname}");')
    lines.append(f"    super.new(name, {width}, {coverage});")
    lines.append("  endfunction : new")
    lines.append("")
    lines.append("  virtual function void build();")
    for f in fields:
        facc = _uvm_access(f.get("access", acc))
        bits = int(f["bit_width"])
        lsb = int(f["bit_offset"])
        reset = _hex_int(f.get("reset", 0))
        # configure(parent, size, lsb_pos, access, volatile, reset, has_reset, is_rand, individually_accessible)
        indv = 1 if (bits % 8 == 0 and lsb % 8 == 0) else 0
        lines.append(
            f'    this.{f["name"]} = uvm_reg_field::type_id::create("{f["name"]}",, get_full_name());'
        )
        lines.append(
            f'    this.{f["name"]}.configure(this, {bits}, {lsb}, "{facc}", '
            f"0, {bits}'h{reset:x}, 1, 1, {indv});"
        )
    lines.append("  endfunction : build")
    lines.append("")
    lines.append(f"  `uvm_object_utils(reg_{blk}_{rname})")
    lines.append(f"endclass : reg_{blk}_{rname}")


def generate_uvm_ral(model: dict) -> str:
    blk = stem_name(model)
    width = int(model.get("width", 32))
    base = model.get("base_address", "0x0")
    protocol = str(model.get("protocol", "apb")).lower()
    regs = _all_regs(model)
    nbytes = max(1, width // 8)
    year = datetime.now().year
    coverage = _cov_flag(model)
    hdl_root = resolve_hdl_root(model)

    lines: list[str] = []
    lines.append("// ---------------------------------------------------------------------------")
    lines.append(f"// Generated by yml2reg (yml2uvm_ral) — UVM regmodel for {blk}")
    lines.append(f"// Copyright (c) {year} Silicon Peasant.")
    lines.append(f"// Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("// Aligned with rals_parser.rb *_ral.svh style (module-level block).")
    if hdl_root:
        lines.append(f"// hdl_path root: {hdl_root}")
    lines.append(f"// coverage: {coverage}")
    lines.append("// ---------------------------------------------------------------------------")
    lines.append(f"`ifndef __{blk}_RAL_SVH__")
    lines.append(f"`define __{blk}_RAL_SVH__")
    lines.append("")
    lines.append("// Optional: provide project sysmap.svh in include path if needed")
    lines.append("// `include \"sysmap.svh\"")
    lines.append("")

    for reg in regs:
        _emit_reg_class(lines, blk, reg, width, coverage)

    # Block
    lines.append("")
    lines.append("//////////////////////////////////////////////////////////////////////////////////////////////")
    lines.append(f"// Definition of {blk} register block")
    lines.append("//////////////////////////////////////////////////////////////////////////////////////////////")
    lines.append(f"class reg_{blk} extends uvm_reg_block;")
    for reg in regs:
        lines.append(f"  rand reg_{blk}_{reg['name']} {reg['name']};")
    lines.append("")
    lines.append("  uvm_reg_map apb_map;")
    lines.append("  uvm_reg_map ahb_map;")
    lines.append("  uvm_reg_map dab_map;")
    lines.append("")
    lines.append(f"  int {blk}_BASE;")
    lines.append("")
    base_sv = f"32'h{_hex_int(base):x}"
    lines.append(
        f'  function new(string name = "{blk}", bit is_top_blk = 1, '
        f"int base_address = {base_sv});"
    )
    lines.append(f"    super.new(name, {coverage});")
    lines.append(f"    this.{blk}_BASE = base_address;")
    lines.append("    if (is_top_blk) begin")
    lines.append("      this.build();")
    lines.append("      this.lock_model();")
    lines.append("      this.reset();")
    lines.append("    end")
    lines.append("  endfunction : new")
    lines.append("")
    lines.append(f"  function void initialize(int base_address = {base_sv});")
    lines.append(f"    this.{blk}_BASE = base_address;")
    lines.append("    this.lock_model();")
    lines.append("    this.reset();")
    lines.append("  endfunction : initialize")
    lines.append("")
    lines.append("  virtual function void build();")
    for reg in regs:
        r = reg["name"]
        lines.append(
            f'    {r} = reg_{blk}_{r}::type_id::create("{r}",, get_full_name());'
        )
    lines.append("")
    for reg in regs:
        lines.append(f"    {reg['name']}.configure(this);")
    lines.append("")
    for reg in regs:
        lines.append(f"    {reg['name']}.build();")
    lines.append("")
    if hdl_root:
        lines.append(f'    // block-level HDL root for backdoor')
        lines.append(f'    this.add_hdl_path("{hdl_root}", -1);')
        lines.append("")
    lines.append("    // field slices (override via field.hdl_path in YAML if needed)")
    for reg in regs:
        r = reg["name"]
        for f in reg["fields"]:
            slice_name = field_hdl_slice_name(reg, f, model)
            lines.append(
                f'    {r}.add_hdl_path_slice("{slice_name}", '
                f"{int(f['bit_offset'])}, {int(f['bit_width'])});"
            )
    lines.append("")
    lines.append(
        f'    apb_map = create_map("apb_map", {blk}_BASE, {nbytes}, UVM_LITTLE_ENDIAN);'
    )
    for reg in regs:
        off = _hex_int(reg["offset"])
        facc = _uvm_access(reg.get("access", "RW"))
        rights = "RO" if facc == "RO" else ("WO" if facc == "WO" else "RW")
        lines.append(f"    apb_map.add_reg({reg['name']}, 'h{off:x}, \"{rights}\");")
    lines.append("")
    lines.append(
        f'    ahb_map = create_map("ahb_map", {blk}_BASE, {nbytes}, UVM_LITTLE_ENDIAN);'
    )
    for reg in regs:
        off = _hex_int(reg["offset"])
        facc = _uvm_access(reg.get("access", "RW"))
        rights = "RO" if facc == "RO" else ("WO" if facc == "WO" else "RW")
        lines.append(f"    ahb_map.add_reg({reg['name']}, 'h{off:x}, \"{rights}\");")
    lines.append("")
    lines.append(
        f'    dab_map = create_map("dab_map", {blk}_BASE, {nbytes}, UVM_LITTLE_ENDIAN);'
    )
    for reg in regs:
        off = _hex_int(reg["offset"])
        facc = _uvm_access(reg.get("access", "RW"))
        rights = "RO" if facc == "RO" else ("WO" if facc == "WO" else "RW")
        lines.append(f"    dab_map.add_reg({reg['name']}, 'h{off:x}, \"{rights}\");")
    lines.append("")
    if protocol == "ahb":
        lines.append("    default_map = ahb_map;")
    elif protocol == "dab":
        lines.append("    default_map = dab_map;")
    else:
        lines.append("    default_map = apb_map;")
    lines.append("  endfunction : build")
    lines.append("")
    lines.append("  // Use with generated yml2reg_bus_adapters.svh")
    lines.append("  virtual function void connect(uvm_sequencer_base sqr);")
    lines.append("    string tname;")
    lines.append("    if (sqr == null) return;")
    lines.append("    tname = sqr.get_type_name();")
    lines.append("    // Match by substring so project sequencer class names stay flexible.")
    lines.append('    if (tname.tolower().find("apb") != -1) begin')
    lines.append('      reg2apb_adapter adp = reg2apb_adapter::type_id::create("reg2apb");')
    lines.append("      apb_map.set_sequencer(sqr, adp);")
    lines.append("      apb_map.set_auto_predict(1);")
    lines.append("      default_map = apb_map;")
    lines.append('    end else if (tname.tolower().find("ahb") != -1) begin')
    lines.append('      reg2ahb_adapter adp = reg2ahb_adapter::type_id::create("reg2ahb");')
    lines.append("      ahb_map.set_sequencer(sqr, adp);")
    lines.append("      ahb_map.set_auto_predict(1);")
    lines.append("      default_map = ahb_map;")
    lines.append('    end else if (tname.tolower().find("dab") != -1) begin')
    lines.append('      reg2dab_adapter adp = reg2dab_adapter::type_id::create("reg2dab");')
    lines.append("      dab_map.set_sequencer(sqr, adp);")
    lines.append("      dab_map.set_auto_predict(1);")
    lines.append("      default_map = dab_map;")
    lines.append("    end else begin")
    lines.append(
        '      `uvm_warning("RegModel", '
        '$sformatf("No adapter matched sequencer type %s; set maps manually", tname))'
    )
    lines.append("    end")
    lines.append("  endfunction : connect")
    lines.append("")
    lines.append(f"  `uvm_object_utils(reg_{blk})")
    lines.append(f"endclass : reg_{blk}")
    lines.append("")
    lines.append(f"`endif // __{blk}_RAL_SVH__")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate UVM regmodel (*_ral.svh) from YAML")
    parser.add_argument("yaml_file")
    parser.add_argument("-o", "--output-dir", default="")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Force UVM_CVR_ALL even if YAML coverage:false",
    )
    args = parser.parse_args(argv)

    yaml_path = Path(args.yaml_file)
    model = load_yml_model(yaml_path)
    if args.coverage:
        model["coverage"] = True
    out_dir = default_output_dir(yaml_path, args.output_dir or None)
    out_path = out_dir / f"{stem_name(model)}_ral.svh"
    out_path.write_text(generate_uvm_ral(model), encoding="utf-8")
    print(f"Generated: {out_path}")
    return 0



if __name__ == "__main__":
    sys.exit(main())
