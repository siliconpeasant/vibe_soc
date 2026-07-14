#!/usr/bin/env python3
"""Deterministically fill upf-gen gaps for macro extra supplies and IO intent."""

from pathlib import Path
import copy
import json
import re


HERE = Path(__file__).resolve().parent
UPF = HERE / "upf" / "upf_dc_demo.upf"
LEGACY_RUNTIME_UPF = HERE / "upf" / "upf_dc_demo_runtime.upf"
SUMMARY = HERE / "upf" / "upf_dc_demo.summary.md"
DRAWIO = HERE / "upf" / "upf_dc_demo.drawio"
EXCALIDRAW = HERE / "upf" / "upf_dc_demo.excalidraw"

text = UPF.read_text(encoding="utf-8")

# The template generator owns primary domain creation. Associate macro rails
# with the same PD_AO extent using the Power Compiler numbered extra supplies.
domain_pattern = re.compile(
    r"create_power_domain PD_AO \\\n+    -elements \{\.\} \\\n+    -supply \{primary SS_VDD_AO_VSS\}"
)
domain_replacement = """create_power_domain PD_AO \\
    -include_scope \\
    -supply {primary SS_VDD_AO_VSS} \\
    -supply {extra_supplies_1 SS_VDD_PLL_VSS} \\
    -supply {extra_supplies_2 SS_VDD_MEM_VSS} \\
    -supply {extra_supplies_3 SS_VDDIO_VSS} \\
    -supply {extra_supplies_4 SS_VDD_SW_IN_VSS} \\
    -supply {extra_supplies_5 SS_VDD_SW_VSS}"""
text, count = domain_pattern.subn(domain_replacement, text)
if count != 1:
    raise RuntimeError("expected one generated PD_AO command")

# Generated switch/control names must match the reviewed RTL interface.
text = text.replace(
    "-control_port {NSLEEPIN sw_en}",
    "-control_port {NSLEEPIN u_aon_ctrl/sw_en_o}",
)
text = text.replace("iso_pd_sw_n", "sw_iso_n")
text = text.replace("-isolation_supply SS_VDD_SW_IN_VSS", "-isolation_supply SS_VDD_AO_VSS")
# Keep the generated self placement for SW-to-AO level shifting.  The combined
# isolation/level-shifter cell must see the PD_SW primary rail at its location;
# its 1.8 V output/control rail is supplied explicitly by the isolation supply.
ls_start = text.find("set_level_shifter LS_SW ")
if ls_start < 0:
    raise RuntimeError("missing generated LS_SW strategy")
ls_end = text.find("\n\n", ls_start)
if ls_end < 0:
    raise RuntimeError("unterminated generated LS_SW strategy")
ls_block = text[ls_start:ls_end]
if ls_block.count("-location self") != 1:
    raise RuntimeError("expected one self location in generated LS_SW strategy")
if "-rule " in ls_block:
    raise RuntimeError("generated LS_SW unexpectedly has an explicit rule")
ls_block = ls_block.replace(
    "    -sink SS_VDD_AO_VSS \\\n",
    "    -sink SS_VDD_AO_VSS \\\n    -rule low_to_high \\\n",
)
text = text[:ls_start] + ls_block + text[ls_end:]
text = text.replace(
    "-state ALL_ON {-logic_expr {SS_VDD_AO_VSS == ON && PD_SW == RUN}}",
    "-state ALL_ON {-logic_expr {SS_VDD_AO_VSS == ON && SS_VDD_PLL_VSS == ON && SS_VDD_MEM_VSS == ON && SS_VDDIO_VSS == ON && PD_SW == RUN}}",
)
text = text.replace(
    "-state SW_OFF {-logic_expr {SS_VDD_AO_VSS == ON && PD_SW == OFF}}",
    "-state SW_OFF {-logic_expr {SS_VDD_AO_VSS == ON && SS_VDD_PLL_VSS == ON && SS_VDD_MEM_VSS == ON && SS_VDDIO_VSS == ON && PD_SW == OFF}}",
)

# Rails not used as a domain primary are intentionally absent from the generic
# generator output. Define their supply sets before associating them to PD_AO.
extra_supply_sets = """
create_supply_set SS_VDD_PLL_VSS \\
    -function {power VDD_PLL} \\
    -function {ground VSS}

create_supply_set SS_VDD_MEM_VSS \\
    -function {power VDD_MEM} \\
    -function {ground VSS}

create_supply_set SS_VDDIO_VSS \\
    -function {power VDDIO} \\
    -function {ground VSS}

add_power_state SS_VDD_PLL_VSS \\
    -state ON {-supply_expr {power == {FULL_ON 1.8} && ground == {FULL_ON 0.0}}}
add_power_state SS_VDD_MEM_VSS \\
    -state ON {-supply_expr {power == {FULL_ON 1.8} && ground == {FULL_ON 0.0}}}
add_power_state SS_VDDIO_VSS \\
    -state ON {-supply_expr {power == {FULL_ON 3.3} && ground == {FULL_ON 0.0}}}
add_power_state SS_VDD_SW_IN_VSS \\
    -state ON {-supply_expr {power == {FULL_ON 1.2} && ground == {FULL_ON 0.0}}}

"""
section_anchor = "# ----------------------------------------------------------------------\n# 3. Power Domains"
if text.count(section_anchor) != 1:
    raise RuntimeError("missing generated supply-set section anchor")
text = text.replace(section_anchor, extra_supply_sets + section_anchor, 1)

# These wrappers represent hard PLL/SRAM/pad macros.  DC links their
# synthesis views from macro_pg_stub.db, whose supplies are Liberty pg_pin
# objects; the behavioral RTL views are intentionally excluded under
# SYNTHESIS.  No port-function workaround is needed or valid here.
hard_macro_block = """
set_design_attributes -models {
    upf_dc_demo_power_switch_macro
    upf_dc_demo_pll_macro
    upf_dc_demo_sram_16x8
    upf_dc_demo_pad_in
    upf_dc_demo_pad_out
} -is_hard_macro true
"""
scope_anchor = "set_scope .\n"
if text.count(scope_anchor) != 1:
    raise RuntimeError("missing generated scope anchor")
text = text.replace(scope_anchor, scope_anchor + hard_macro_block, 1)

# Explicit macro PG bindings are required and must not be inferred by name.
pg_block = """
# Hierarchical macro PG bindings: all macros remain in PD_AO. The switch
# macro is a pre-instantiated leaf PG anchor; PSW_SW remains the abstract
# switch that defines behavior.
connect_supply_net VDD_SW_IN -ports {u_power_switch_macro/VIN}
connect_supply_net VDD_SW -ports {u_power_switch_macro/VOUT}
connect_supply_net VSS -ports {u_power_switch_macro/VSS}
connect_supply_net VDD_PLL -ports {u_pll_macro/VDD}
connect_supply_net VSS -ports {u_pll_macro/VSS}
connect_supply_net VDD_MEM -ports {u_sram_macro/VDD}
connect_supply_net VSS -ports {u_sram_macro/VSS}
connect_supply_net VDDIO -ports {u_pad_in/VDDIO}
connect_supply_net VSS -ports {u_pad_in/VSSIO}
connect_supply_net VDDIO -ports {u_pad_out/VDDIO}
connect_supply_net VSS -ports {u_pad_out/VSSIO}
"""
anchor = "# 3. Power Domains"
if text.count(anchor) != 1:
    raise RuntimeError("missing generated power-domain section")
text = text.replace(anchor, pg_block + "\n" + anchor, 1)

# Ensure both voltage directions are explicit. IO strategies use supply
# attributes inside PD_AO; no IO-specific domain is introduced.
extra = """
# AO-to-switchable input level shifting.
set_level_shifter LS_AO_TO_SW -domain PD_SW -applies_to inputs \\
    -source SS_VDD_AO_VSS -sink SS_VDD_SW_VSS -rule high_to_low -location self \\
    -input_supply SS_VDD_AO_VSS -output_supply SS_VDD_SW_VSS

# Same-domain IO voltage boundary, expressed with port supply attributes.
set_port_attributes -ports {pad_in_i} -driver_supply SS_VDDIO_VSS
set_port_attributes -ports {pad_in_core_o} -receiver_supply SS_VDD_AO_VSS
set_port_attributes -ports {pad_out_core_i} -driver_supply SS_VDD_AO_VSS
set_port_attributes -ports {pad_out_o} -receiver_supply SS_VDDIO_VSS

# The pad-facing point-to-point nets terminate at hard IO macros. Mark them
# analog so Power Compiler does not insert core LS/repeaters where a real
# characterized IO library must own the voltage conversion.
set_port_attributes -ports {pad_in_i pad_in_core_o pad_out_core_i pad_out_o} \\
    -is_analog

# sw_clk enters directly at the switchable-domain voltage.
set_port_attributes -ports {sw_clk} -driver_supply SS_VDD_SW_VSS

# Teaching-cell mappings for the executable AO/SW experiment only.  The
# SW-to-AO cell is an enable level shifter that implements both strategies.
# IEEE 1801 maps this combined isolation/level-shifter cell through the
# isolation strategy; DC then uses it for the coincident LS_SW crossing.
map_isolation_cell ISO_SW -domain PD_SW \\
    -lib_cells {upf_dc_demo_els_lh_1v2_1v8}
map_level_shifter_cell LS_AO_TO_SW -domain PD_SW \\
    -lib_cells {upf_dc_demo_ls_hl_1v8_1v2}
"""
text += extra

if len(re.findall(r"^create_power_domain\s+", text, re.MULTILINE)) != 2:
    raise RuntimeError("final UPF must contain exactly two power domains")
for forbidden in ("set_retention", "map_retention_cell"):
    if forbidden in text:
        raise RuntimeError(f"unexpected retention command: {forbidden}")
for required in (
    "create_supply_set SS_VDD_PLL_VSS",
    "create_supply_set SS_VDD_MEM_VSS",
    "create_supply_set SS_VDDIO_VSS",
    "extra_supplies_1 SS_VDD_PLL_VSS",
    "extra_supplies_2 SS_VDD_MEM_VSS",
    "extra_supplies_3 SS_VDDIO_VSS",
    "extra_supplies_4 SS_VDD_SW_IN_VSS",
    "extra_supplies_5 SS_VDD_SW_VSS",
    "u_power_switch_macro/VIN", "u_power_switch_macro/VOUT",
    "u_power_switch_macro/VSS",
    "u_pll_macro/VDD", "u_pll_macro/VSS", "u_sram_macro/VDD",
    "u_sram_macro/VSS", "u_pad_in/VDDIO", "u_pad_in/VSSIO",
    "u_pad_out/VDDIO", "u_pad_out/VSSIO", "LS_AO_TO_SW",
    "set_design_attributes -models", "u_aon_ctrl/sw_en_o",
    "-isolation_supply SS_VDD_AO_VSS",
    "add_power_state SS_VDD_PLL_VSS", "add_power_state SS_VDD_SW_IN_VSS",
    "FULL_ON 3.3",
    "map_isolation_cell ISO_SW", "upf_dc_demo_els_lh_1v2_1v8",
    "upf_dc_demo_ls_hl_1v8_1v2",
    "-rule low_to_high", "-rule high_to_low",
    "set_port_attributes -ports {sw_clk}", "-is_analog",
    "SS_VDDIO_VSS == ON && PD_SW == RUN",
):
    if required not in text:
        raise RuntimeError(f"missing required final UPF token: {required}")
UPF.write_text(text, encoding="utf-8")
if LEGACY_RUNTIME_UPF.exists():
    LEGACY_RUNTIME_UPF.unlink()

with SUMMARY.open("a", encoding="utf-8") as stream:
    stream.write("""

## Deterministic post-processing

- `PD_AO` retains the top extent and associates PLL, memory, IO, and both
  switch-macro rails as numbered extra supplies 1 through 5. The final two
  make `VDD_SW_IN` and `VDD_SW` available to the `PD_AO` boundary macro.
- All eleven macro PG pins are bound by explicit hierarchical
  `connect_supply_net` commands; the macros remain inside `PD_AO`. The three
  switch-macro pins retain `VDD_SW_IN` and `VDD_SW` in the PG netlist while
  abstract `PSW_SW` remains the authoritative switch behavior.
- AO-to-SW input LS intent and same-domain IO driver/receiver supply attributes
  are added. Pad-boundary signals are analog-exempt because the hard IO macro,
  powered by `VDDIO/VSS`, owns the 1.8 V/3.3 V conversion.
- The co-located SW-to-AO isolation and low-to-high strategies map to one
  dual-rail enable-level-shifter cell inside `PD_SW`.
- No retention strategy or additional power domain is introduced.
- Functional RTL contains no PG ports. DC loads this complete canonical UPF
  directly against the macro Liberty `pg_pin` objects and emits PG only in
  synthesis outputs.
""")

# Add explicit macro boxes inside the generated PD_AO container.
drawio = DRAWIO.read_text(encoding="utf-8")
drawio_cells = """
<mxCell id="AO_PLL_BOX" value="u_pll_macro" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2E7D32;" vertex="1" parent="1"><mxGeometry x="430" y="615" width="120" height="26" as="geometry" /></mxCell>
<mxCell id="AO_MEM_BOX" value="u_sram_macro" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2E7D32;" vertex="1" parent="1"><mxGeometry x="570" y="615" width="120" height="26" as="geometry" /></mxCell>
<mxCell id="AO_PAD_IN_BOX" value="u_pad_in" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2E7D32;" vertex="1" parent="1"><mxGeometry x="710" y="615" width="120" height="26" as="geometry" /></mxCell>
<mxCell id="AO_PAD_OUT_BOX" value="u_pad_out" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2E7D32;" vertex="1" parent="1"><mxGeometry x="850" y="615" width="120" height="26" as="geometry" /></mxCell>
<mxCell id="AO_PSW_BOX" value="u_power_switch_macro" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2E7D32;" vertex="1" parent="1"><mxGeometry x="990" y="615" width="130" height="26" as="geometry" /></mxCell>
"""
if drawio.count("</root>") != 1:
    raise RuntimeError("unexpected Draw.io root structure")
drawio = drawio.replace("</root>", drawio_cells + "</root>", 1)
DRAWIO.write_text(drawio, encoding="utf-8")

diagram = json.loads(EXCALIDRAW.read_text(encoding="utf-8"))
ao_rect = next((
    e for e in diagram.get("elements", [])
    if e.get("type") == "rectangle" and e.get("x") == 150
    and e.get("y") == 556 and e.get("width") == 980
), None)
text_template = next((e for e in diagram.get("elements", []) if e.get("type") == "text"), None)
if ao_rect is None or text_template is None:
    raise RuntimeError("cannot locate Excalidraw PD_AO templates")
for index, name in enumerate((
    "u_pll_macro", "u_sram_macro", "u_pad_in", "u_pad_out",
    "u_power_switch_macro",
)):
    box = copy.deepcopy(ao_rect)
    box.update({
        "id": f"AO_MACRO_BOX_{index}", "x": 430 + 140 * index,
        "y": 615, "width": 130 if index == 4 else 120, "height": 26,
        "backgroundColor": "#ffffff", "seed": 9100 + index,
        "versionNonce": 9200 + index,
    })
    label = copy.deepcopy(text_template)
    label.update({
        "id": f"AO_MACRO_TEXT_{index}", "x": 444 + 140 * index,
        "y": 620, "width": 116 if index == 4 else 92, "height": 18, "text": name,
        "originalText": name, "fontSize": 12, "seed": 9300 + index,
        "versionNonce": 9400 + index,
    })
    diagram["elements"].extend((box, label))
EXCALIDRAW.write_text(json.dumps(diagram, ensure_ascii=False, indent=2), encoding="utf-8")

print(UPF)
