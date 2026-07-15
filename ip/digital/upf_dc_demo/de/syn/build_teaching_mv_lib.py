#!/usr/bin/env python3
"""Derive non-signoff Sky130 voltage-map variants for this UPF exercise."""

from __future__ import annotations

import argparse
from pathlib import Path


SOURCE_LIBRARY = 'library ("sky130_fd_sc_hd__tt_025C_1v80") {'
SOURCE_OC = '"tt_025C_1v80"'
VOLTAGE_18 = "1.8000000000"
VOLTAGE_12 = "1.2000000000"
BASE_ISO_CELL = '    cell ("sky130_fd_sc_hd__lpflow_inputiso0p_1") {'
BASE_LH_CELL = '    cell ("sky130_fd_sc_hd__lpflow_lsbuf_lh_isowell_tap_1") {'
BASE_HL_CELL = '    cell ("sky130_fd_sc_hd__lpflow_lsbuf_lh_hl_isowell_tap_1") {'
ELS_CELL = "upf_dc_demo_els_lh_1v2_1v8"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one {label}, found {count}")
    return text.replace(old, new, 1)


def group_span(text: str, header: str, label: str) -> tuple[int, int]:
    if text.count(header) != 1:
        raise RuntimeError(f"expected one {label} group")
    start = text.index(header)
    brace = text.index("{", start)
    depth = 0
    for offset in range(brace, len(text)):
        char = text[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, offset + 1
    raise RuntimeError(f"unterminated {label} group")


def derive_enabled_level_shifter(text: str) -> str:
    """Convert one copied isolation cell into a teaching-only LH ELS."""
    start, end = group_span(text, BASE_ISO_CELL, "base isolation cell")
    cell = text[start:end]
    cell = replace_once(
        cell,
        BASE_ISO_CELL,
        f'    cell ("{ELS_CELL}") {{',
        "ELS cell name",
    )
    cell = replace_once(
        cell,
        '        is_isolation_cell : "true";',
        '        is_isolation_cell : "true";\n'
        '        is_level_shifter : "true";\n'
        '        level_shifter_type : "LH";\n'
        '        input_voltage_range(1.2000000000, 2.1000000000);\n'
        '        output_voltage_range(1.2000000000, 2.1000000000);',
        "ELS cell attributes",
    )
    cell = replace_once(
        cell,
        '        pg_pin ("VGND") {',
        '        pg_pin ("LOWLVPWR") {\n'
        '            pg_type : "primary_power";\n'
        '            voltage_name : "LOWLVPWR";\n'
        '        }\n'
        '        pg_pin ("VGND") {',
        "ELS low-voltage PG pin",
    )

    a_start, a_end = group_span(cell, '        pin ("A") {', "ELS data pin")
    a_pin = cell[a_start:a_end]
    a_pin = replace_once(
        a_pin,
        '            isolation_cell_data_pin : "true";',
        '            isolation_cell_data_pin : "true";\n'
        '            input_signal_level : "LOWLVPWR";\n'
        '            level_shifter_data_pin : "true";',
        "ELS data attributes",
    )
    a_pin = replace_once(
        a_pin,
        '            related_power_pin : "VPWR";',
        '            related_power_pin : "LOWLVPWR";',
        "ELS data supply",
    )
    cell = cell[:a_start] + a_pin + cell[a_end:]

    sleep_start, sleep_end = group_span(
        cell, '        pin ("SLEEP") {', "ELS enable pin"
    )
    sleep_pin = cell[sleep_start:sleep_end]
    sleep_pin = replace_once(
        sleep_pin,
        '            isolation_cell_enable_pin : "true";',
        '            isolation_cell_enable_pin : "true";\n'
        '            level_shifter_enable_pin : "true";',
        "ELS enable attributes",
    )
    cell = cell[:sleep_start] + sleep_pin + cell[sleep_end:]
    return text[:start] + cell + text[end:]


def derive(source: Path, output: Path, variant: str) -> None:
    text = source.read_text(encoding="utf-8")
    if text.count(SOURCE_LIBRARY) != 1:
        raise RuntimeError("source is not the expected Sky130 HD 1.8 V library")
    if text.count(SOURCE_OC) != 2:
        raise RuntimeError("unexpected source operating-condition structure")

    if variant == "lh":
        lib_name = "sky130_fd_sc_hd__teaching_lh_1v2_1v8"
        oc_name = "tt_025C_teaching_lh_1v2_1v8"
        text = replace_once(
            text,
            BASE_HL_CELL,
            '    cell ("upf_dc_demo_ls_lh_1v2_1v8") {',
            "bidirectional level-shifter cell for the LH teaching map",
        )
        for supply in ("LOWLVPWR", "VPWRIN"):
            text = replace_once(
                text,
                f'voltage_map("{supply}", {VOLTAGE_18});',
                f'voltage_map("{supply}", {VOLTAGE_12});',
                f"{supply} voltage map",
            )
    elif variant == "hl":
        lib_name = "sky130_fd_sc_hd__teaching_hl_1v8_1v2"
        oc_name = "tt_025C_teaching_hl_1v8_1v2"
        text = replace_once(
            text,
            BASE_HL_CELL,
            '    cell ("upf_dc_demo_ls_hl_1v8_1v2") {',
            "HL level-shifter cell",
        )
        for supply in ("KAPWR", "LOWLVPWR", "VPB", "VPWR"):
            text = replace_once(
                text,
                f'voltage_map("{supply}", {VOLTAGE_18});',
                f'voltage_map("{supply}", {VOLTAGE_12});',
                f"{supply} voltage map",
            )
        text = replace_once(
            text,
            f"        voltage : {VOLTAGE_18};",
            f"        voltage : {VOLTAGE_12};",
            "operating voltage",
        )
        text = replace_once(
            text,
            f"    nom_voltage : {VOLTAGE_18};",
            f"    nom_voltage : {VOLTAGE_12};",
            "nominal voltage",
        )
        # VPWRIN deliberately remains at 1.8 V so the bidirectional LS cell
        # has a 1.8 V input rail and a 1.2 V output rail in this variant.
    else:
        raise ValueError(f"unsupported variant: {variant}")

    # The source library is loaded beside both teaching variants.  This
    # Power Compiler release accepts only an unqualified Liberty cell name in
    # map_*_cell, so duplicate low-power names are ambiguous (MV-086).
    # Rename the unused isolation copy in each teaching library and give the
    # direction-specific mapped LS above a unique name.
    if variant == "lh":
        text = derive_enabled_level_shifter(text)
    else:
        text = replace_once(
            text,
            BASE_ISO_CELL,
            f'    cell ("upf_dc_demo_unused_iso0p_{variant}") {{',
            "teaching isolation copy",
        )

    text = text.replace(
        SOURCE_LIBRARY,
        f'library ("{lib_name}") {{\n'
        "    /* TEACHING ONLY: voltage maps relabeled; timing/power tables are not recharacterized. */",
        1,
    )
    text = text.replace(SOURCE_OC, f'"{oc_name}"')
    if SOURCE_OC in text or SOURCE_LIBRARY in text:
        raise RuntimeError("source library identifiers remain after derivation")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("lh", "hl"), required=True)
    args = parser.parse_args()
    derive(args.source, args.output, args.variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
