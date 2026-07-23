#!/usr/bin/env python3
"""Generate stub LEF + Liberty for the stories260k_spm PD macro.

The behavioral SPM is a SYNTHESIS blackbox; ORFS needs a LEF macro for
floorplan and a Liberty model so STA covers paths crossing the macro
boundary. Physical size is derived from on-chip capacity matching RTL:

  WBUF 4736×32B + KV 3968×32B + ACT 512×8B + VEC 1024×8B = 284 KiB

Bit density is taken from the platform fakeram45_1024x32 LEF
(~0.5007 um^2/bit including periphery), so the single SPM macro footprint
is area-equivalent to packing the same bits as discrete fakeram macros
(~1.165 mm^2). Timing arcs remain conservative stubs, not silicon.
"""

import math
import os

MACRO = "stories260k_spm"

# --- Capacity (must stay in sync with de/rtl/stories260k_spm.v) ---
WBUF_WORDS = 4736   # 32-byte words
KV_WORDS = 3968     # 32-byte words
ACT_WORDS = 512     # 8-byte words
VEC_WORDS = 1024    # 8-byte words
SPM_BYTES = WBUF_WORDS * 32 + KV_WORDS * 32 + ACT_WORDS * 8 + VEC_WORDS * 8
SPM_BITS = SPM_BYTES * 8  # 2_326_528 bits = 284 KiB

# Platform fakeram45_1024x32: SIZE 152.190 x 107.800 → 0.50067 um^2/bit
FAKERAM_UM2_PER_BIT = (152.190 * 107.800) / (1024 * 32)

# Square macro footprint area-equivalent to discrete fakeram packing
AREA_UM2 = SPM_BITS * FAKERAM_UM2_PER_BIT  # ≈ 1_164_832 um^2
SIZE_UM = math.sqrt(AREA_UM2)  # ≈ 1079.3 um

# (name, width, dir, group)
PORTS = [
    ("clk", 1, "INPUT", "clock"),
    ("host_sel_i", 4, "INPUT", "control"),
    ("host_we_i", 1, "INPUT", "control"),
    ("host_addr_i", 16, "INPUT", "addr"),
    ("host_wdata_i", 32, "INPUT", "wdata"),
    ("host_wstrb_i", 4, "INPUT", "control"),
    ("host_wbuf_rdata_o", 32, "OUTPUT", "rdata:host_addr_i"),
    ("host_kv_rdata_o", 32, "OUTPUT", "rdata:host_addr_i"),
    ("host_act_rdata_o", 32, "OUTPUT", "rdata:host_addr_i"),
    ("host_vec_rdata_o", 32, "OUTPUT", "rdata:host_addr_i"),
    ("wbuf_raddr_i", 13, "INPUT", "addr"),
    ("wbuf_rdata_o", 256, "OUTPUT", "rdata:wbuf_raddr_i"),
    ("wbuf_saddr_i", 13, "INPUT", "addr"),
    ("wbuf_sdata_o", 256, "OUTPUT", "rdata:wbuf_saddr_i"),
    ("wbuf_i8_raddr_i", 13, "INPUT", "addr"),
    ("wbuf_i8_rdata_o", 256, "OUTPUT", "rdata:wbuf_i8_raddr_i"),
    ("kv_raddr_i", 12, "INPUT", "addr"),
    ("kv_rdata_o", 256, "OUTPUT", "rdata:kv_raddr_i"),
    ("kv_vdata_o", 256, "OUTPUT", "rdata:kv_raddr_i"),
    ("kv_scale_raddr_i", 12, "INPUT", "addr"),
    ("kv_scale_rdata_o", 256, "OUTPUT", "rdata:kv_scale_raddr_i"),
    ("kv_we_i", 1, "INPUT", "control"),
    ("kv_waddr_i", 12, "INPUT", "addr"),
    ("kv_wdata_i", 256, "INPUT", "wdata"),
    ("kv_wstrb_i", 32, "INPUT", "control"),
    ("act_raddr_i", 9, "INPUT", "addr"),
    ("act_rdata_o", 64, "OUTPUT", "rdata:act_raddr_i"),
    ("act_we_i", 1, "INPUT", "control"),
    ("act_waddr_i", 9, "INPUT", "addr"),
    ("act_wdata_i", 64, "INPUT", "wdata"),
    ("act_wstrb_i", 8, "INPUT", "control"),
    ("vec_raddr_i", 10, "INPUT", "addr"),
    ("vec_rdata_o", 64, "OUTPUT", "rdata:vec_raddr_i"),
    ("vec_we_i", 1, "INPUT", "control"),
    ("vec_waddr_i", 10, "INPUT", "addr"),
    ("vec_wdata_i", 64, "INPUT", "wdata"),
    ("vec_wstrb_i", 8, "INPUT", "control"),
]


def pins():
    for name, width, direction, group in PORTS:
        if width == 1:
            yield name, direction, group
        else:
            for i in range(width):
                yield f"{name}[{i}]", direction, group


def snap_um(v: float) -> float:
    """Snap microns to FreePDK45 manufacturing grid (10 dbu @ 2000 dbu/um = 0.005 um)."""
    grid = 0.005
    return round(v / grid) * grid


def gen_lef(path):
    groups = {"clock": [], "control": [], "addr": [], "wdata": [], "rdata": []}
    for pname, direction, group in pins():
        key = group.split(":")[0]
        groups[key].append((pname, direction))

    def edge_pins(items, edge, layer1, layer2):
        out = []
        n = len(items)
        pitch = SIZE_UM / (n + 1)
        for idx, (pname, direction) in enumerate(items):
            layer = layer1 if idx % 2 == 0 else layer2
            pos = (idx + 1) * pitch
            if edge == "left":
                rect = (0.0, pos - 0.07, 0.14, pos + 0.07)
            elif edge == "right":
                rect = (SIZE_UM - 0.14, pos - 0.07, SIZE_UM, pos + 0.07)
            elif edge == "bottom":
                rect = (pos - 0.07, 0.0, pos + 0.07, 0.14)
            else:
                rect = (pos - 0.07, SIZE_UM - 0.14, pos + 0.07, SIZE_UM)
            out.append((pname, direction, layer, rect))
        return out

    blocks = []
    blocks += edge_pins(groups["clock"] + groups["control"], "top", "metal3", "metal4")
    blocks += edge_pins(groups["addr"], "left", "metal1", "metal2")
    blocks += edge_pins(groups["wdata"], "bottom", "metal3", "metal4")
    blocks += edge_pins(groups["rdata"], "right", "metal2", "metal4")

    with open(path, "w") as f:
        f.write("VERSION 5.7 ;\nBUSBITCHARS \"[]\" ;\nDIVIDERCHAR \"/\" ;\n")
        f.write("UNITS\n  DATABASE MICRONS 2000 ;\nEND UNITS\n\n")
        f.write(f"MACRO {MACRO}\n")
        f.write("  CLASS BLOCK ;\n")
        f.write(f"  FOREIGN {MACRO} 0 0 ;\n")
        f.write(f"  SIZE {SIZE_UM:.1f} BY {SIZE_UM:.1f} ;\n")
        f.write("  SYMMETRY X Y ;\n")
        f.write("  SITE FreePDK45_38x28_10R_NP_162NW_34O ;\n")
        for pname, direction, layer, (x1, y1, x2, y2) in blocks:
            x1, y1, x2, y2 = (snap_um(x1), snap_um(y1), snap_um(x2), snap_um(y2))
            f.write(f"  PIN {pname}\n")
            f.write(f"    DIRECTION {direction} ;\n")
            f.write("    USE SIGNAL ;\n")
            f.write("    PORT\n")
            f.write(f"      LAYER {layer} ;\n")
            f.write(f"      RECT {x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f} ;\n")
            f.write("    END\n")
            f.write(f"  END {pname}\n")
        f.write("  OBS\n")
        for layer in ("metal1", "metal2", "metal3", "metal4"):
            f.write(f"    LAYER {layer} ;\n")
            o1, o2 = snap_um(0.19), snap_um(SIZE_UM - 0.19)
            f.write(f"    RECT {o1:.3f} {o1:.3f} {o2:.3f} {o2:.3f} ;\n")
        f.write("  END\n")
        f.write(f"END {MACRO}\n\nEND LIBRARY\n")
    print(f"wrote {path}: {len(blocks)} pins")


def gen_lib(path):
    """Emit bus-grouped Liberty with clk-related timing (fakeram45 style).

    Yosys 0.66 asserts on pin names with brackets like ``foo[0]``
    (`count_id(wire->name) == 0` in rtlil.cc). Use Liberty bus groups
    instead; LEF remains bit-blasted for OpenROAD pin geometry.
    """
    widths = sorted({w for _, w, _, _ in PORTS if w > 1})
    with open(path, "w") as f:
        f.write("/* Stub Liberty model for the stories260k_spm PD blackbox macro.\n")
        f.write(" * PoC-only: conservative delays so STA covers macro-boundary paths;\n")
        f.write(" * NOT a silicon characterization.\n")
        f.write(" * Bus groups + setup_rising/rising_edge (Yosys-safe; no pin[i]). */\n")
        f.write("library (spm_min_lib) {\n")
        f.write("  technology (cmos);\n  delay_model : table_lookup;\n")
        f.write("  time_unit : \"1ns\";\n  voltage_unit : \"1V\";\n")
        f.write("  current_unit : \"1mA\";\n  capacitive_load_unit (1, ff);\n")
        f.write("  nom_process : 1.0;\n  nom_temperature : 25.0;\n  nom_voltage : 1.1;\n")
        f.write("  operating_conditions (tt) {\n")
        f.write("    process : 1;\n    temperature : 25;\n    voltage : 1.1;\n")
        f.write("    tree_type : balanced_tree;\n  }\n")
        f.write("  default_operating_conditions : tt;\n")
        f.write("  slew_derate_from_library : 1.0;\n")
        f.write("  slew_lower_threshold_pct_fall : 20.0;\n")
        f.write("  slew_upper_threshold_pct_fall : 80.0;\n")
        f.write("  slew_lower_threshold_pct_rise : 20.0;\n")
        f.write("  slew_upper_threshold_pct_rise : 80.0;\n")
        f.write("  input_threshold_pct_fall : 50.0;\n")
        f.write("  input_threshold_pct_rise : 50.0;\n")
        f.write("  output_threshold_pct_fall : 50.0;\n")
        f.write("  output_threshold_pct_rise : 50.0;\n")
        f.write("  default_fanout_load : 1.0;\n  default_inout_pin_cap : 0.005;\n")
        f.write("  default_input_pin_cap : 0.005;\n  default_output_pin_cap : 0.0;\n")

        for w in widths:
            f.write(
                f"  type (spm_bus_{w-1}_0) {{\n    base_type : array;\n"
                f"    data_type : bit;\n    bit_width : {w};\n"
                f"    bit_from : {w-1};\n    bit_to : 0;\n    downto : true;\n  }}\n"
            )
        f.write(f"  cell ({MACRO}) {{\n")
        f.write(f"    area : {int(round(AREA_UM2))};\n")
        f.write("    interface_timing : true;\n")

        def emit_input_body():
            # Setup is checked with a modest abstract margin. Hold is zero for this
            # PoC SPM blackbox: a non-zero hold (e.g. 0.1 ns) only models invent
            # short-path fails into the macro under large CTS skew, and OpenROAD
            # hold-buffer repair crashes on the post-route GRT state of this flow.
            # Replace with vendor SRAM liberty (real setup/hold tables) for signoff.
            f.write("      timing () {\n")
            f.write("        related_pin : \"clk\";\n")
            f.write("        timing_type : setup_rising;\n")
            f.write("        rise_constraint (scalar) { values (\"0.3\"); }\n")
            f.write("        fall_constraint (scalar) { values (\"0.3\"); }\n")
            f.write("      }\n")
            f.write("      timing () {\n")
            f.write("        related_pin : \"clk\";\n")
            f.write("        timing_type : hold_rising;\n")
            f.write("        rise_constraint (scalar) { values (\"0.0\"); }\n")
            f.write("        fall_constraint (scalar) { values (\"0.0\"); }\n")
            f.write("      }\n")

        def emit_output_body():
            f.write("      timing () {\n")
            f.write("        related_pin : \"clk\";\n")
            f.write("        timing_type : rising_edge;\n")
            f.write("        timing_sense : non_unate;\n")
            f.write("        cell_rise (scalar) { values (\"2.0\"); }\n")
            f.write("        cell_fall (scalar) { values (\"2.0\"); }\n")
            f.write("        rise_transition (scalar) { values (\"0.2\"); }\n")
            f.write("        fall_transition (scalar) { values (\"0.2\"); }\n")
            f.write("      }\n")

        for name, width, direction, _group in PORTS:
            if name == "clk":
                f.write("    pin (clk) {\n")
                f.write("      direction : input;\n      clock : true;\n")
                f.write("      capacitance : 0.020;\n    }\n")
                continue
            if direction == "INPUT":
                if width == 1:
                    f.write(f"    pin ({name}) {{\n")
                    f.write("      direction : input;\n      capacitance : 0.005;\n")
                    emit_input_body()
                    f.write("    }\n")
                else:
                    f.write(f"    bus ({name}) {{\n")
                    f.write(f"      bus_type : spm_bus_{width-1}_0;\n")
                    f.write("      direction : input;\n      capacitance : 0.005;\n")
                    emit_input_body()
                    f.write("    }\n")
            else:
                if width == 1:
                    f.write(f"    pin ({name}) {{\n")
                    f.write("      direction : output;\n      capacitance : 0.0;\n")
                    emit_output_body()
                    f.write("    }\n")
                else:
                    f.write(f"    bus ({name}) {{\n")
                    f.write(f"      bus_type : spm_bus_{width-1}_0;\n")
                    f.write("      direction : output;\n      capacitance : 0.0;\n")
                    emit_output_body()
                    f.write("    }\n")
        f.write("  }\n")
        f.write("}\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    gen_lef(os.path.join(out_dir, "stories260k_spm.lef"))
    gen_lib(os.path.join(out_dir, "stories260k_spm.lib"))
