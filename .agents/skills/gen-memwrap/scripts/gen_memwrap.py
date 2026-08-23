#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen-memwrap: Excel memory table → SoC wrap RTL + open-source macro lib/lef.

Backends:
  - sky130     : OpenRAM prebuilt catalog OR online OpenRAM generate
  - nangate45  : FakeRAM catalog OR bsg_fakeram / builtin black-box generate

CLI:
  python3 gen_memwrap.py <excel> <sheet_name> <output_dir> [platform]
           [--generate|--no-generate] [--relaxed]
  platform: sky130 | nangate45 | auto (per-row PLATFORM column, default sky130)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except ImportError as e:  # pragma: no cover
    raise SystemExit("pandas required; run make mcp-setup") from e

# Local generators (OpenRAM / bsg_fakeram / builtin FakeRAM)
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from mem_generators import (  # noqa: E402
    GeneratedMacro,
    generate_builtin_fakerom,
    generate_macro,
    generator_status,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REF_DIR = SKILL_DIR / "references"

SUPPORTED_PLATFORMS = ("sky130", "nangate45")
TYPE_ALIASES = {
    "spram": "spram",
    "sram": "spram",
    "sp": "spram",
    "tpram": "tpram",
    "tpram(synchronous)": "tpram",
    "tpram(asynchronous)": "tpram_async",
    "tpram_async": "tpram_async",
    "dpram": "tpram",
    "sfifo": "sfifo",
    "sfifo(synchronous)": "sfifo",
    "asfifo": "asfifo",
    "asfifo(asynchronous)": "asfifo",
    "rom": "rom",
}


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@dataclass
class Macro:
    name: str
    depth: int
    width: int
    ports: str
    write_size: int
    family: str
    assets: Dict[str, Optional[Path]]

    @property
    def key(self) -> Tuple[int, int]:
        return (self.depth, self.width)


def _resolve_orfs_root(catalog: dict) -> Path:
    env_key = catalog.get("orfs_platforms_env", "ORFS_PLATFORMS")
    candidates = [os.environ.get(env_key, "").strip()]
    for var in ("SILICON_CREW_ORFS_DIR", "OPENROAD_FLOW_HOME"):
        base = os.environ.get(var, "").strip()
        if base:
            candidates.append(str(Path(base) / "platforms"))
    candidates.append(catalog.get("default_orfs_platforms", ""))
    root = Path("").resolve()
    for cand in candidates:
        if cand:
            root = Path(cand).expanduser().resolve()
            if root.is_dir():
                return root
    raise FileNotFoundError(
        f"ORFS platforms root not found: {root}\n"
        f"Set ${env_key} (or SILICON_CREW_ORFS_DIR / OPENROAD_FLOW_HOME)."
    )


def load_catalog(platform: str) -> Tuple[Path, List[Macro]]:
    path = REF_DIR / f"catalog_{platform}.json"
    if not path.is_file():
        raise FileNotFoundError(f"catalog missing: {path}")
    catalog = json.loads(path.read_text(encoding="utf-8"))
    root = _resolve_orfs_root(catalog)
    macros: List[Macro] = []
    for m in catalog.get("macros", []):
        assets: Dict[str, Optional[Path]] = {}
        for k, rel in (m.get("assets") or {}).items():
            if not rel:
                assets[k] = None
            else:
                p = (root / rel).resolve()
                assets[k] = p if p.is_file() else None
        macros.append(
            Macro(
                name=m["name"],
                depth=int(m["depth"]),
                width=int(m["width"]),
                ports=str(m.get("ports", "1rw")),
                write_size=int(m.get("write_size", 1)),
                family=str(m.get("family", platform)),
                assets=assets,
            )
        )
    return root, macros


def match_macro(
    macros: List[Macro],
    depth: int,
    width: int,
    want_ports: Optional[str] = None,
    exact_name: Optional[str] = None,
    strict: bool = True,
) -> Macro:
    if exact_name:
        for m in macros:
            if m.name == exact_name:
                return m
        raise ValueError(f"ExactMacro not in catalog: {exact_name}")

    candidates = list(macros)
    if want_ports:
        filtered = [m for m in candidates if m.ports == want_ports]
        if filtered:
            candidates = filtered

    exact = [m for m in candidates if m.depth == depth and m.width == width]
    if exact:
        return exact[0]

    if strict:
        avail = ", ".join(f"{m.name}({m.depth}x{m.width},{m.ports})" for m in macros)
        raise ValueError(
            f"No catalog macro for depth={depth} width={width} ports={want_ports or '*'}. "
            f"Available: {avail}"
        )

    # Prefer same width, depth >= requested, smallest depth
    same_w = [m for m in candidates if m.width == width and m.depth >= depth]
    if same_w:
        return sorted(same_w, key=lambda m: m.depth)[0]
    # else closest area
    return min(candidates, key=lambda m: abs(m.depth * m.width - depth * width))


def generated_to_macro(g: GeneratedMacro) -> Macro:
    return Macro(
        name=g.name,
        depth=g.depth,
        width=g.width,
        ports=g.ports,
        write_size=g.write_size,
        family=g.family,
        assets=dict(g.assets),
    )


def match_or_generate_macro(
    macros: List[Macro],
    platform: str,
    depth: int,
    width: int,
    want_ports: Optional[str],
    write_size: int,
    exact_name: Optional[str],
    work_dir: Path,
    strict: bool,
    do_generate: bool,
) -> Tuple[Macro, str]:
    """Return (macro, notes). On catalog miss, optionally run online generators."""
    try:
        m = match_macro(
            macros,
            depth,
            width,
            want_ports=want_ports,
            exact_name=exact_name,
            strict=True,  # always try exact first
        )
        return m, "catalog hit"
    except ValueError as catalog_err:
        if not do_generate:
            if not strict:
                m = match_macro(
                    macros,
                    depth,
                    width,
                    want_ports=want_ports,
                    exact_name=exact_name,
                    strict=False,
                )
                return m, "catalog nearest (--relaxed, generate disabled)"
            raise catalog_err

        print(
            f"Info: catalog miss {platform} {depth}x{width} "
            f"ports={want_ports or '*'} → online generate"
        )
        g = generate_macro(
            platform=platform,
            depth=depth,
            width=width,
            ports=want_ports or ("1rw1r" if platform == "sky130" else "1rw"),
            write_size=write_size,
            work_dir=work_dir,
            prefer_external=True,
        )
        m = generated_to_macro(g)
        macros.append(m)  # reuse within this run
        return m, g.notes


# ---------------------------------------------------------------------------
# Excel rows
# ---------------------------------------------------------------------------


@dataclass
class MemReq:
    sheet: str
    row: int
    mem_type: str
    depth: int
    width: int
    platform: str
    ports: str
    bit_write: bool
    write_size: int
    name: str
    exact_macro: str
    async_clk: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)


def _col(df, *names, default=None):
    cols = {str(c).strip(): c for c in df.columns}
    lower = {str(c).strip().lower(): c for c in df.columns}
    for n in names:
        if n in cols:
            return cols[n]
        if n.lower() in lower:
            return lower[n.lower()]
    return default


def _truthy(v) -> bool:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return False
    s = str(v).strip().upper()
    return s in {"1", "ON", "TRUE", "YES", "Y", "T"}


def _norm_type(v: str) -> str:
    s = str(v).strip().lower()
    if s in TYPE_ALIASES:
        return TYPE_ALIASES[s]
    # fuzzy
    if "asfifo" in s:
        return "asfifo"
    if "sfifo" in s or "sync" in s and "fifo" in s:
        return "sfifo"
    if "tpram" in s or "dpram" in s:
        return "tpram_async" if "async" in s else "tpram"
    if "spram" in s or s == "sram":
        return "spram"
    if "rom" in s:
        return "rom"
    raise ValueError(f"unsupported TYPE: {v}")


def read_excel_rows(
    excel_path: Path, sheet_name: str, default_platform: str
) -> List[MemReq]:
    xls = pd.ExcelFile(excel_path)
    sheets = [s for s in xls.sheet_names if sheet_name in s]
    if not sheets:
        raise ValueError(
            f"No sheet matching '{sheet_name}'. Available: {xls.sheet_names}"
        )
    rows: List[MemReq] = []
    for sheet in sheets:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        c_type = _col(df, "TYPE", "Type", "type")
        c_depth = _col(df, "NumberOfWords", "depth", "Depth", "DEPTH")
        c_width = _col(df, "BitsInWord", "width", "Width", "WIDTH")
        c_plat = _col(df, "PLATFORM", "Platform", "platform")
        c_ports = _col(df, "PORTS", "Ports", "ports")
        c_bw = _col(df, "BitWordWrite", "bit_write", "BitWrite")
        c_ws = _col(df, "WriteSize", "write_size", "WRITE_SIZE")
        c_name = _col(df, "Name", "name", "NAME", "LogicName")
        c_exact = _col(df, "ExactMacro", "exact_macro", "MACRO")
        if c_type is None or c_depth is None or c_width is None:
            raise ValueError(
                f"sheet '{sheet}' needs TYPE, NumberOfWords, BitsInWord columns"
            )
        for i, rec in df.iterrows():
            tv = rec[c_type]
            if tv is None or (isinstance(tv, float) and math.isnan(tv)):
                continue
            try:
                depth = int(rec[c_depth])
                width = int(rec[c_width])
            except Exception:
                continue
            if depth <= 0 or width <= 0:
                continue
            mtype = _norm_type(tv)
            plat = (
                str(rec[c_plat]).strip().lower()
                if c_plat is not None
                and rec[c_plat] is not None
                and not (isinstance(rec[c_plat], float) and math.isnan(rec[c_plat]))
                else default_platform
            )
            if plat not in SUPPORTED_PLATFORMS:
                raise ValueError(
                    f"row {i}: PLATFORM={plat} not in {SUPPORTED_PLATFORMS}"
                )
            ports = (
                str(rec[c_ports]).strip().lower()
                if c_ports is not None
                and rec[c_ports] is not None
                and not (isinstance(rec[c_ports], float) and math.isnan(rec[c_ports]))
                else ""
            )
            bit_write = _truthy(rec[c_bw]) if c_bw is not None else True
            write_size = (
                int(rec[c_ws])
                if c_ws is not None
                and rec[c_ws] is not None
                and not (isinstance(rec[c_ws], float) and math.isnan(rec[c_ws]))
                else (8 if plat == "sky130" else 1)
            )
            name = (
                str(rec[c_name]).strip()
                if c_name is not None
                and rec[c_name] is not None
                and not (isinstance(rec[c_name], float) and math.isnan(rec[c_name]))
                else ""
            )
            exact = (
                str(rec[c_exact]).strip()
                if c_exact is not None
                and rec[c_exact] is not None
                and not (isinstance(rec[c_exact], float) and math.isnan(rec[c_exact]))
                else ""
            )
            async_clk = mtype in {"tpram_async", "asfifo"}
            if mtype == "tpram_async":
                mtype = "tpram"
            if not ports:
                if mtype in {"tpram", "asfifo"} and plat == "sky130":
                    ports = "1rw1r"
                else:
                    ports = "1rw"
            rows.append(
                MemReq(
                    sheet=sheet,
                    row=int(i) + 2,
                    mem_type=mtype,
                    depth=depth,
                    width=width,
                    platform=plat,
                    ports=ports,
                    bit_write=bit_write,
                    write_size=write_size,
                    name=name,
                    exact_macro=exact,
                    async_clk=async_clk,
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Naming / helpers
# ---------------------------------------------------------------------------


def addr_width(depth: int) -> int:
    return max(1, math.ceil(math.log2(int(depth))))


def wrap_base_name(kind: str, depth: int, width: int, platform: str, bit_write: bool) -> str:
    tag = "1c"
    extra = "b" if bit_write else ""
    plat = "sky130" if platform == "sky130" else "n45"
    return f"{kind}_{depth}d{width}w_{tag}{extra}_{plat}"


def header_lines(filename: str) -> List[str]:
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    return [
        "// ============================================================================",
        f"// File Name    : {filename}",
        "// Description  : AUTO-GENERATED by gen-memwrap (open-source backend)",
        f"// Generated On : {now}",
        "// Do not hand-edit; regenerate from Excel.",
        "// ============================================================================",
        "",
    ]


def write_text(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_asset(src: Optional[Path], dst_dir: Path, label: str) -> Optional[Path]:
    if src is None or not src.is_file():
        return None
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.resolve() != src.resolve():
        shutil.copy2(src, dst)
    return dst


# ---------------------------------------------------------------------------
# Behavioral models (FakeRAM / NO_ASIC_MEM / dual-port when no macro)
# ---------------------------------------------------------------------------


def emit_beh_spram(path: Path, mod: str, depth: int, width: int, mask_bits: int) -> None:
    aw = addr_width(depth)
    lines = header_lines(path.name)
    lines += [
        f"// Behavioral 1RW SRAM model for simulation / FakeRAM stand-in",
        f"module {mod} (",
        f"  input                  clk,",
        f"  input                  ce_in,",
        f"  input                  we_in,",
        f"  input  [{aw-1}:0]      addr_in,",
        f"  input  [{width-1}:0]   wd_in,",
        f"  input  [{mask_bits-1}:0] w_mask_in,",
        f"  output reg [{width-1}:0] rd_out",
        ");",
        f"  reg [{width-1}:0] mem [0:{depth-1}];",
        f"  integer i;",
        f"  always @(posedge clk) begin",
        f"    if (ce_in) begin",
        f"      if (we_in) begin",
    ]
    if mask_bits == width:
        lines += [
            f"        for (i = 0; i < {width}; i = i + 1) begin",
            f"          if (w_mask_in[i]) mem[addr_in][i] <= wd_in[i];",
            f"        end",
        ]
    else:
        # byte-ish chunks
        chunk = max(1, width // mask_bits)
        lines += [
            f"        for (i = 0; i < {mask_bits}; i = i + 1) begin",
            f"          if (w_mask_in[i])",
            f"            mem[addr_in][i*{chunk} +: {chunk}] <= wd_in[i*{chunk} +: {chunk}];",
            f"        end",
        ]
    lines += [
        f"      end",
        f"      rd_out <= mem[addr_in];",
        f"    end",
        f"  end",
        f"endmodule",
        "",
    ]
    write_text(path, lines)


def emit_beh_tpram(
    path: Path, mod: str, depth: int, width: int, mask_bits: int, async_clk: bool
) -> None:
    aw = addr_width(depth)
    if async_clk:
        clk_a, clk_b = "clka", "clkb"
        port_clks = [
            "  input                  clka,",
            "  input                  clkb,",
        ]
    else:
        clk_a = clk_b = "clk"
        port_clks = ["  input                  clk,"]
    lines = header_lines(path.name) + [
        f"// Behavioral dual-port model (A write/read, B read)",
        f"module {mod} (",
        *port_clks,
        f"  input                  ena,",
        f"  input                  wea,",
        f"  input  [{aw-1}:0]      addra,",
        f"  input  [{width-1}:0]   dina,",
        f"  input  [{mask_bits-1}:0] wem,",
        f"  output reg [{width-1}:0] douta,",
        f"  input                  enb,",
        f"  input  [{aw-1}:0]      addrb,",
        f"  output reg [{width-1}:0] doutb",
        ");",
        f"  reg [{width-1}:0] mem [0:{depth-1}];",
        f"  integer i;",
        f"  always @(posedge {clk_a}) begin",
        f"    if (ena) begin",
        f"      if (wea) begin",
    ]
    if mask_bits >= width:
        lines += [
            f"        for (i = 0; i < {width}; i = i + 1)",
            f"          if (wem[i]) mem[addra][i] <= dina[i];",
        ]
    else:
        chunk = max(1, width // max(1, mask_bits))
        lines += [
            f"        for (i = 0; i < {mask_bits}; i = i + 1)",
            f"          if (wem[i]) mem[addra][i*{chunk} +: {chunk}] <= dina[i*{chunk} +: {chunk}];",
        ]
    lines += [
        "      end",
        "      douta <= mem[addra];",
        "    end",
        "  end",
        f"  always @(posedge {clk_b}) begin",
        "    if (enb) doutb <= mem[addrb];",
        "  end",
        "endmodule",
        "",
    ]
    write_text(path, lines)


# ---------------------------------------------------------------------------
# Wrap emitters
# ---------------------------------------------------------------------------


def emit_spram_wrap_openram(
    path: Path,
    wrap: str,
    macro: Macro,
    depth: int,
    width: int,
    bit_write: bool,
) -> None:
    """Unified spram wrap over sky130 OpenRAM 1rw or 1rw1r (port1 tied off)."""
    aw = addr_width(depth)
    nmask = max(1, width // max(1, macro.write_size)) if bit_write else 1
    lines = header_lines(path.name)
    lines += [
        f"// Unified SPRAM wrap → {macro.name} ({macro.ports})",
        f"module {wrap} (",
        f"  input                  clk,",
        f"  input                  me,",
        f"  input                  we,",
        f"  input  [{aw-1}:0]      addr,",
        f"  input  [{width-1}:0]   din,",
        f"  input  [{nmask-1}:0]   wem," if bit_write else f"  // no wem",
        f"  output [{width-1}:0]   dout",
        ");",
    ]
    # clean optional wem line
    lines = [ln for ln in lines if ln != "  // no wem"]
    if not bit_write:
        # re-emit without wem in port list - rebuild
        lines = header_lines(path.name) + [
            f"// Unified SPRAM wrap → {macro.name} ({macro.ports})",
            f"module {wrap} (",
            f"  input                  clk,",
            f"  input                  me,",
            f"  input                  we,",
            f"  input  [{aw-1}:0]      addr,",
            f"  input  [{width-1}:0]   din,",
            f"  output [{width-1}:0]   dout",
            ");",
        ]

    wmask_expr = "wem" if bit_write else f"{{{nmask}{{1'b1}}}}"
    if not bit_write:
        nmask = max(1, width // max(1, macro.write_size))
        wmask_expr = f"{{{nmask}{{1'b1}}}}"

    if macro.ports == "1rw1r":
        lines += [
            f"  {macro.name} u_mem (",
            f"    .clk0  (clk),",
            f"    .csb0  (~me),",
            f"    .web0  (~we),",
            f"    .wmask0({wmask_expr}),",
            f"    .addr0 (addr),",
            f"    .din0  (din),",
            f"    .dout0 (dout),",
            f"    .clk1  (clk),",
            f"    .csb1  (1'b1),",
            f"    .addr1 ({{{aw}{{1'b0}}}}),",
            f"    .dout1 ()",
            f"  );",
        ]
    else:
        # pure 1rw openram style (if present)
        lines += [
            f"  {macro.name} u_mem (",
            f"    .clk0  (clk),",
            f"    .csb0  (~me),",
            f"    .web0  (~we),",
            f"    .wmask0({wmask_expr}),",
            f"    .addr0 (addr),",
            f"    .din0  (din),",
            f"    .dout0 (dout)",
            f"  );",
        ]
    lines += ["endmodule", ""]
    write_text(path, lines)


def emit_spram_wrap_fakeram(
    path: Path,
    wrap: str,
    macro_name: str,
    depth: int,
    width: int,
    bit_write: bool,
) -> None:
    aw = addr_width(depth)
    lines = header_lines(path.name)
    if bit_write:
        lines += [
            f"// Unified SPRAM wrap → {macro_name} (FakeRAM 1rw)",
            f"module {wrap} (",
            f"  input                  clk,",
            f"  input                  me,",
            f"  input                  we,",
            f"  input  [{aw-1}:0]      addr,",
            f"  input  [{width-1}:0]   din,",
            f"  input  [{width-1}:0]   wem,",
            f"  output [{width-1}:0]   dout",
            ");",
            f"  {macro_name} u_mem (",
            f"    .clk       (clk),",
            f"    .ce_in     (me),",
            f"    .we_in     (we),",
            f"    .addr_in   (addr),",
            f"    .wd_in     (din),",
            f"    .w_mask_in (wem),",
            f"    .rd_out    (dout)",
            f"  );",
            f"endmodule",
            "",
        ]
    else:
        lines += [
            f"// Unified SPRAM wrap → {macro_name} (FakeRAM 1rw)",
            f"module {wrap} (",
            f"  input                  clk,",
            f"  input                  me,",
            f"  input                  we,",
            f"  input  [{aw-1}:0]      addr,",
            f"  input  [{width-1}:0]   din,",
            f"  output [{width-1}:0]   dout",
            ");",
            f"  {macro_name} u_mem (",
            f"    .clk       (clk),",
            f"    .ce_in     (me),",
            f"    .we_in     (we),",
            f"    .addr_in   (addr),",
            f"    .wd_in     (din),",
            f"    .w_mask_in ({{{width}{{1'b1}}}}),",
            f"    .rd_out    (dout)",
            f"  );",
            f"endmodule",
            "",
        ]
    write_text(path, lines)


def emit_tpram_wrap_openram(
    path: Path,
    wrap: str,
    macro: Macro,
    depth: int,
    width: int,
    bit_write: bool,
    async_clk: bool,
) -> None:
    """Map unified TPRAM ports onto OpenRAM 1rw1r (A=RW, B=R)."""
    aw = addr_width(depth)
    nmask = max(1, width // max(1, macro.write_size)) if bit_write else max(
        1, width // max(1, macro.write_size)
    )
    wmask_expr = "wem" if bit_write else f"{{{nmask}{{1'b1}}}}"
    lines = header_lines(path.name)
    if async_clk:
        clk_ports = ["  input                  clka,", "  input                  clkb,"]
        clk0, clk1 = "clka", "clkb"
    else:
        clk_ports = ["  input                  clk,"]
        clk0 = clk1 = "clk"
    port_list = [
        f"// Unified TPRAM wrap → {macro.name} (A RW / B R)",
        f"module {wrap} (",
        *clk_ports,
        f"  input                  ena,",
        f"  input                  wea,",
        f"  input  [{aw-1}:0]      addra,",
        f"  input  [{width-1}:0]   dina,",
    ]
    if bit_write:
        port_list.append(f"  input  [{nmask-1}:0]   wem,")
    port_list += [
        f"  output [{width-1}:0]   douta,",
        f"  input                  enb,",
        f"  input  [{aw-1}:0]      addrb,",
        f"  output [{width-1}:0]   doutb",
        ");",
        f"  // OpenRAM port0 is RW; douta mirrors dout0 (same-cycle model dependent)",
        f"  {macro.name} u_mem (",
        f"    .clk0  ({clk0}),",
        f"    .csb0  (~ena),",
        f"    .web0  (~wea),",
        f"    .wmask0({wmask_expr}),",
        f"    .addr0 (addra),",
        f"    .din0  (dina),",
        f"    .dout0 (douta),",
        f"    .clk1  ({clk1}),",
        f"    .csb1  (~enb),",
        f"    .addr1 (addrb),",
        f"    .dout1 (doutb)",
        f"  );",
        f"endmodule",
        "",
    ]
    write_text(path, header_lines(path.name) + port_list)


def emit_tpram_wrap_beh(
    path: Path,
    wrap: str,
    beh_mod: str,
    depth: int,
    width: int,
    bit_write: bool,
    async_clk: bool,
) -> None:
    aw = addr_width(depth)
    if async_clk:
        clk_ports = ["  input                  clka,", "  input                  clkb,"]
        clk_conn = ["    .clka (clka),", "    .clkb (clkb),"]
    else:
        clk_ports = ["  input                  clk,"]
        clk_conn = ["    .clk  (clk),"]
    ports = [
        f"// Unified TPRAM wrap → behavioral {beh_mod}",
        f"module {wrap} (",
        *clk_ports,
        "  input                  ena,",
        "  input                  wea,",
        f"  input  [{aw-1}:0]      addra,",
        f"  input  [{width-1}:0]   dina,",
    ]
    if bit_write:
        ports.append(f"  input  [{width-1}:0]   wem,")
    ports += [
        f"  output [{width-1}:0]   douta,",
        "  input                  enb,",
        f"  input  [{aw-1}:0]      addrb,",
        f"  output [{width-1}:0]   doutb",
        ");",
    ]
    wem_net = "wem" if bit_write else ("{" + str(width) + "{1'b1}}")
    ports += [
        f"  {beh_mod} u_mem (",
        *clk_conn,
        "    .ena   (ena),",
        "    .wea   (wea),",
        "    .addra (addra),",
        "    .dina  (dina),",
        f"    .wem   ({wem_net}),",
        "    .douta (douta),",
        "    .enb   (enb),",
        "    .addrb (addrb),",
        "    .doutb (doutb)",
        "  );",
        "endmodule",
        "",
    ]
    write_text(path, header_lines(path.name) + ports)


def emit_sfifo_wrap(
    path: Path,
    wrap: str,
    ram_wrap: str,
    depth: int,
    width: int,
    bit_write: bool,
) -> None:
    """Self-contained sync FIFO with FWFT-ish simple pointer logic + ram wrap."""
    aw = addr_width(depth)
    cw = addr_width(depth + 1)
    lines = header_lines(path.name)
    lines += [
        f"// Sync FIFO wrap (self-contained) over {ram_wrap}",
        f"module {wrap} #(",
        f"  parameter DATA_WIDTH = {width},",
        f"  parameter DATA_DEPTH = {depth},",
        f"  parameter ADDR_WIDTH = $clog2(DATA_DEPTH),",
        f"  parameter CNT_WIDTH  = $clog2(DATA_DEPTH+1)",
        f") (",
        f"  input                      clk,",
        f"  input                      rst_n,",
        f"  input                      srst,",
        f"  input                      w_en,",
        f"  input                      r_en,",
        f"  input  [DATA_WIDTH-1:0]    wdata,",
        f"  output reg [DATA_WIDTH-1:0] rdata,",
        f"  output                     fifo_full,",
        f"  output                     fifo_empty,",
        f"  output [CNT_WIDTH-1:0]     word_cnt",
        f");",
        f"  reg [ADDR_WIDTH-1:0] wptr, rptr;",
        f"  reg [CNT_WIDTH-1:0]  cnt;",
        f"  wire [ADDR_WIDTH-1:0] raddr = rptr;",
        f"  wire [ADDR_WIDTH-1:0] waddr = wptr;",
        f"  wire we = w_en && !fifo_full;",
        f"  wire re = r_en && !fifo_empty;",
        f"  // Show-ahead: keep reading rptr whenever not empty so dout is ready on re.",
        f"  wire ram_me = we | (~fifo_empty);",
        f"  wire ram_we = we;",
        f"  wire [ADDR_WIDTH-1:0] ram_addr = we ? waddr : raddr;",
        f"  wire [DATA_WIDTH-1:0] dout;",
        f"  assign fifo_full  = (cnt == DATA_DEPTH[CNT_WIDTH-1:0]);",
        f"  assign fifo_empty = (cnt == {{CNT_WIDTH{{1'b0}}}});",
        f"  assign word_cnt   = cnt;",
        f"",
        f"  {ram_wrap} u_ram (",
        f"    .clk  (clk),",
        f"    .me   (ram_me),",
        f"    .we   (ram_we),",
        f"    .addr (ram_addr),",
        f"    .din  (wdata),",
    ]
    if bit_write:
        lines.append(f"    .wem  ({{{width}{{1'b1}}}}),")
    lines += [
        f"    .dout (dout)",
        f"  );",
        f"",
        f"  always @(posedge clk or negedge rst_n) begin",
        f"    if (!rst_n) begin",
        f"      wptr  <= {{ADDR_WIDTH{{1'b0}}}};",
        f"      rptr  <= {{ADDR_WIDTH{{1'b0}}}};",
        f"      cnt   <= {{CNT_WIDTH{{1'b0}}}};",
        f"      rdata <= {{DATA_WIDTH{{1'b0}}}};",
        f"    end else if (srst) begin",
        f"      wptr  <= {{ADDR_WIDTH{{1'b0}}}};",
        f"      rptr  <= {{ADDR_WIDTH{{1'b0}}}};",
        f"      cnt   <= {{CNT_WIDTH{{1'b0}}}};",
        f"    end else begin",
        f"      if (we) wptr <= wptr + 1'b1;",
        f"      // dout already holds mem[rptr] from previous cycle when !we.",
        f"      if (re) begin",
        f"        rdata <= dout;",
        f"        rptr  <= rptr + 1'b1;",
        f"      end",
        f"      case ({{we, re}})",
        f"        2'b10: cnt <= cnt + 1'b1;",
        f"        2'b01: cnt <= cnt - 1'b1;",
        f"        default: cnt <= cnt;",
        f"      endcase",
        f"    end",
        f"  end",
        f"endmodule",
        "",
    ]
    write_text(path, lines)


def emit_asfifo_wrap(
    path: Path,
    wrap: str,
    ram_wrap: str,
    depth: int,
    width: int,
    bit_write: bool,
) -> None:
    """Async FIFO with gray pointers + dual-clock tpram wrap (or beh tpram)."""
    lines = header_lines(path.name)
    lines += [
        f"// Async FIFO wrap (gray sync) over {ram_wrap}",
        f"module {wrap} #(",
        f"  parameter DATA_WIDTH = {width},",
        f"  parameter DATA_DEPTH = {depth},",
        f"  parameter ADDR_WIDTH = $clog2(DATA_DEPTH)",
        f") (",
        f"  input                      w_clk,",
        f"  input                      r_clk,",
        f"  input                      w_rst_n,",
        f"  input                      r_rst_n,",
        f"  input                      w_en,",
        f"  input                      r_en,",
        f"  input  [DATA_WIDTH-1:0]    wdata,",
        f"  output reg [DATA_WIDTH-1:0] rdata,",
        f"  output                     fifo_full,",
        f"  output                     fifo_empty",
        f");",
        f"  reg [ADDR_WIDTH:0] wptr_bin, rptr_bin;",
        f"  reg [ADDR_WIDTH:0] wptr_gray, rptr_gray;",
        f"  reg [ADDR_WIDTH:0] wptr_gray_r1, wptr_gray_r2;",
        f"  reg [ADDR_WIDTH:0] rptr_gray_w1, rptr_gray_w2;",
        f"  wire [ADDR_WIDTH:0] wptr_bin_next = wptr_bin + (w_en & ~fifo_full);",
        f"  wire [ADDR_WIDTH:0] rptr_bin_next = rptr_bin + (r_en & ~fifo_empty);",
        f"  wire [ADDR_WIDTH:0] wptr_gray_next = (wptr_bin_next >> 1) ^ wptr_bin_next;",
        f"  wire [ADDR_WIDTH:0] rptr_gray_next = (rptr_bin_next >> 1) ^ rptr_bin_next;",
        f"  assign fifo_full  = (wptr_gray_next == {{~rptr_gray_w2[ADDR_WIDTH:ADDR_WIDTH-1], rptr_gray_w2[ADDR_WIDTH-2:0]}});",
        f"  assign fifo_empty = (rptr_gray == wptr_gray_r2);",
        f"  wire [DATA_WIDTH-1:0] doutb;",
        f"",
        f"  {ram_wrap} u_ram (",
        f"    .clka  (w_clk),",
        f"    .clkb  (r_clk),",
        f"    .ena   (w_en & ~fifo_full),",
        f"    .wea   (1'b1),",
        f"    .addra (wptr_bin[ADDR_WIDTH-1:0]),",
        f"    .dina  (wdata),",
    ]
    if bit_write:
        lines.append(f"    .wem   ({{{width}{{1'b1}}}}),")
    lines += [
        f"    .douta (),",
        f"    .enb   (r_en & ~fifo_empty),",
        f"    .addrb (rptr_bin[ADDR_WIDTH-1:0]),",
        f"    .doutb (doutb)",
        f"  );",
        f"",
        f"  always @(posedge w_clk or negedge w_rst_n) begin",
        f"    if (!w_rst_n) begin",
        f"      wptr_bin <= 0; wptr_gray <= 0; rptr_gray_w1 <= 0; rptr_gray_w2 <= 0;",
        f"    end else begin",
        f"      if (w_en & ~fifo_full) begin",
        f"        wptr_bin  <= wptr_bin_next;",
        f"        wptr_gray <= wptr_gray_next;",
        f"      end",
        f"      rptr_gray_w1 <= rptr_gray;",
        f"      rptr_gray_w2 <= rptr_gray_w1;",
        f"    end",
        f"  end",
        f"  always @(posedge r_clk or negedge r_rst_n) begin",
        f"    if (!r_rst_n) begin",
        f"      rptr_bin <= 0; rptr_gray <= 0; wptr_gray_r1 <= 0; wptr_gray_r2 <= 0; rdata <= 0;",
        f"    end else begin",
        f"      if (r_en & ~fifo_empty) begin",
        f"        rptr_bin  <= rptr_bin_next;",
        f"        rptr_gray <= rptr_gray_next;",
        f"        rdata     <= doutb;",
        f"      end",
        f"      wptr_gray_r1 <= wptr_gray;",
        f"      wptr_gray_r2 <= wptr_gray_r1;",
        f"    end",
        f"  end",
        f"endmodule",
        "",
    ]
    write_text(path, lines)


def emit_rom_wrap(
    path: Path, wrap: str, depth: int, width: int, init_hex: str = ""
) -> None:
    aw = addr_width(depth)
    lines = header_lines(path.name) + [
        "// Behavioral ROM wrap (sky130 / nangate45 open-source path)",
        f"module {wrap} (",
        "  input                  clk,",
        "  input                  me,",
        f"  input  [{aw-1}:0]      addr,",
        f"  output reg [{width-1}:0] dout",
        ");",
        f"  reg [{width-1}:0] mem [0:{depth-1}];",
        "  integer i;",
        "  initial begin",
        f"    for (i = 0; i < {depth}; i = i + 1) mem[i] = {{{width}{{1'b0}}}};",
    ]
    if init_hex:
        lines.append(f'    $readmemh("{init_hex}", mem);')
    lines += [
        "  end",
        "  always @(posedge clk) begin",
        "    if (me) dout <= mem[addr];",
        "  end",
        "endmodule",
        "",
    ]
    write_text(path, lines)


def emit_rom_wrap_fakerom(
    path: Path, wrap: str, macro_name: str, depth: int, width: int
) -> None:
    aw = addr_width(depth)
    lines = header_lines(path.name) + [
        f"// Unified ROM wrap → {macro_name} (FakeROM 1r)",
        f"module {wrap} (",
        "  input                  clk,",
        "  input                  me,",
        f"  input  [{aw-1}:0]      addr,",
        f"  output [{width-1}:0]   dout",
        ");",
        f"  {macro_name} u_mem (",
        "    .clk     (clk),",
        "    .ce_in   (me),",
        "    .addr_in (addr),",
        "    .rd_out  (dout)",
        "  );",
        "endmodule",
        "",
    ]
    write_text(path, lines)


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------


@dataclass
class GenResult:
    req: MemReq
    wrap_name: str
    wrap_path: Path
    macro_name: str
    assets: Dict[str, Optional[str]]
    notes: str = ""


def process_row(
    req: MemReq,
    catalogs: Dict[str, List[Macro]],
    out: Path,
    strict: bool,
    do_generate: bool = True,
) -> GenResult:
    rtl_dir = out / "rtl"
    lib_dir = out / "lib"
    lef_dir = out / "lef"
    beh_dir = out / "beh"
    rtl_dir.mkdir(parents=True, exist_ok=True)

    macros = catalogs[req.platform]
    bit_write = req.bit_write
    mtype = req.mem_type

    # --- ROM ---
    if mtype == "rom":
        base = req.name or wrap_base_name("rom", req.depth, req.width, req.platform, False)
        wrap = base if base.endswith("_wrap") else base + "_wrap"
        path = rtl_dir / f"{wrap}.v"
        if req.platform == "nangate45" and do_generate:
            macro = generate_builtin_fakerom(req.depth, req.width, out)
            assets_copied: Dict[str, Optional[str]] = {}
            for key, d in (("lib", lib_dir), ("lef", lef_dir), ("v", rtl_dir)):
                dst = copy_asset(macro.assets.get(key), d, key)
                assets_copied[key] = str(dst) if dst else None
            emit_rom_wrap_fakerom(path, wrap, macro.name, req.depth, req.width)
            return GenResult(
                req,
                wrap,
                path,
                macro.name,
                assets_copied,
                macro.notes,
            )
        emit_rom_wrap(path, wrap, req.depth, req.width)
        return GenResult(req, wrap, path, "(behavioral_rom)", {}, "behavioral ROM")

    # Desired ports for catalog match
    want_ports = req.ports
    if mtype in {"tpram", "asfifo"} and req.platform == "sky130":
        want_ports = "1rw1r"
    elif mtype in {"spram", "sfifo"}:
        # sky130 catalog is 1rw1r only; accept it
        want_ports = None if req.platform == "sky130" else "1rw"

    macro: Optional[Macro] = None
    notes: List[str] = []
    try:
        if mtype != "rom":
            # tpram/asfifo on n45: still no dual-port physical macro → behavioral
            if mtype in {"tpram", "asfifo"} and req.platform == "nangate45":
                macro = None
                notes.append("nangate45 has no dual-port FakeRAM; behavioral tpram")
            else:
                macro, src_note = match_or_generate_macro(
                    macros,
                    platform=req.platform,
                    depth=req.depth,
                    width=req.width,
                    want_ports=want_ports,
                    write_size=req.write_size,
                    exact_name=req.exact_macro or None,
                    work_dir=out,
                    strict=strict,
                    do_generate=do_generate,
                )
                notes.append(src_note)
    except Exception:
        if mtype in {"tpram", "asfifo"}:
            macro = None
            notes.append("macro resolve failed; behavioral fallback")
        else:
            raise

    assets_copied: Dict[str, Optional[str]] = {}

    if macro is not None:
        for key, d in (("lib", lib_dir), ("lef", lef_dir), ("v", rtl_dir)):
            dst = copy_asset(macro.assets.get(key), d, key)
            assets_copied[key] = str(dst) if dst else None
        if macro.assets.get("v") is None and req.platform == "nangate45":
            # emit FakeRAM behavioral model with macro name
            beh_path = beh_dir / f"{macro.name}.v"
            nmask = req.width if bit_write else req.width
            emit_beh_spram(beh_path, macro.name, macro.depth, macro.width, nmask)
            # also place under rtl for filelist convenience
            copy_asset(beh_path, rtl_dir, "v")
            assets_copied["v"] = str(rtl_dir / f"{macro.name}.v")
            notes.append("generated FakeRAM behavioral .v")

        # depth/width must match macro for wiring
        depth, width = macro.depth, macro.width
        if depth != req.depth or width != req.width:
            notes.append(
                f"macro resized match: requested {req.depth}x{req.width} → {depth}x{width}"
            )
    else:
        depth, width = req.depth, req.width

    # --- SPRAM ---
    if mtype == "spram":
        assert macro is not None
        base = req.name or wrap_base_name("spram", depth, width, req.platform, bit_write)
        wrap = base if base.endswith("_wrap") else base + "_wrap"
        path = rtl_dir / f"{wrap}.v"
        if req.platform == "sky130":
            emit_spram_wrap_openram(path, wrap, macro, depth, width, bit_write)
        else:
            emit_spram_wrap_fakeram(path, wrap, macro.name, depth, width, bit_write)
        return GenResult(req, wrap, path, macro.name, assets_copied, "; ".join(notes))

    # --- TPRAM ---
    if mtype == "tpram":
        base = req.name or wrap_base_name("tpram", depth, width, req.platform, bit_write)
        wrap = base if base.endswith("_wrap") else base + "_wrap"
        path = rtl_dir / f"{wrap}.v"
        if macro is not None and req.platform == "sky130":
            emit_tpram_wrap_openram(
                path, wrap, macro, depth, width, bit_write, req.async_clk
            )
            return GenResult(req, wrap, path, macro.name, assets_copied, "; ".join(notes))
        # behavioral dual-port
        beh_mod = f"tpram_{depth}d{width}w_beh"
        beh_path = rtl_dir / f"{beh_mod}.v"
        emit_beh_tpram(beh_path, beh_mod, depth, width, width if bit_write else width, req.async_clk)
        emit_tpram_wrap_beh(path, wrap, beh_mod, depth, width, bit_write, req.async_clk)
        assets_copied["v"] = str(beh_path)
        return GenResult(req, wrap, path, beh_mod, assets_copied, "; ".join(notes))

    # --- SFIFO ---
    if mtype == "sfifo":
        # need spram wrap first
        if macro is None:
            raise ValueError(f"sfifo requires catalog spram macro (row {req.row})")
        ram_base = wrap_base_name("spram", depth, width, req.platform, bit_write)
        ram_wrap = ram_base + "_wrap"
        ram_path = rtl_dir / f"{ram_wrap}.v"
        if not ram_path.is_file():
            if req.platform == "sky130":
                emit_spram_wrap_openram(ram_path, ram_wrap, macro, depth, width, bit_write)
            else:
                emit_spram_wrap_fakeram(ram_path, ram_wrap, macro.name, depth, width, bit_write)
        base = req.name or wrap_base_name("sfifo", depth, width, req.platform, bit_write)
        wrap = base if base.endswith("_wrap") else base + "_wrap"
        path = rtl_dir / f"{wrap}.v"
        emit_sfifo_wrap(path, wrap, ram_wrap, depth, width, bit_write)
        return GenResult(
            req, wrap, path, macro.name, assets_copied, "; ".join(notes + [f"ram={ram_wrap}"])
        )

    # --- ASFIFO ---
    if mtype == "asfifo":
        # need async tpram wrap
        t_base = wrap_base_name("tpram", depth, width, req.platform, bit_write)
        t_wrap = t_base + "_wrap"
        t_path = rtl_dir / f"{t_wrap}.v"
        if not t_path.is_file():
            if macro is not None and req.platform == "sky130":
                emit_tpram_wrap_openram(t_path, t_wrap, macro, depth, width, bit_write, True)
            else:
                beh_mod = f"tpram_{depth}d{width}w_beh"
                beh_path = rtl_dir / f"{beh_mod}.v"
                if not beh_path.is_file():
                    emit_beh_tpram(beh_path, beh_mod, depth, width, width, True)
                emit_tpram_wrap_beh(t_path, t_wrap, beh_mod, depth, width, bit_write, True)
                assets_copied["v"] = str(beh_path)
                notes.append(f"tpram={beh_mod}")
        base = req.name or wrap_base_name("asfifo", depth, width, req.platform, bit_write)
        wrap = base if base.endswith("_wrap") else base + "_wrap"
        path = rtl_dir / f"{wrap}.v"
        emit_asfifo_wrap(path, wrap, t_wrap, depth, width, bit_write)
        return GenResult(
            req,
            wrap,
            path,
            macro.name if macro else "(beh_tpram)",
            assets_copied,
            "; ".join(notes + [f"tpram={t_wrap}"]),
        )

    raise ValueError(f"unsupported type after normalize: {mtype}")


def write_report(out: Path, results: List[GenResult]) -> None:
    rep = out / "report"
    rep.mkdir(parents=True, exist_ok=True)
    # CSV
    lines = [
        "sheet,row,type,platform,depth,width,wrap,macro,lib,lef,v,notes"
    ]
    jlist = []
    flist = []
    for r in results:
        lib = r.assets.get("lib") or ""
        lef = r.assets.get("lef") or ""
        v = r.assets.get("v") or ""
        lines.append(
            f"{r.req.sheet},{r.req.row},{r.req.mem_type},{r.req.platform},"
            f"{r.req.depth},{r.req.width},{r.wrap_name},{r.macro_name},"
            f"{lib},{lef},{v},{r.notes.replace(',', ';')}"
        )
        jlist.append(
            {
                "sheet": r.req.sheet,
                "row": r.req.row,
                "type": r.req.mem_type,
                "platform": r.req.platform,
                "depth": r.req.depth,
                "width": r.req.width,
                "wrap": r.wrap_name,
                "wrap_path": str(r.wrap_path),
                "macro": r.macro_name,
                "assets": r.assets,
                "notes": r.notes,
            }
        )
        flist.append(str(r.wrap_path.resolve()))
        if v:
            flist.append(str(Path(v).resolve()))
    (rep / "selection.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (rep / "selection.json").write_text(json.dumps(jlist, indent=2) + "\n", encoding="utf-8")

    # filelist: unique
    seen = set()
    fl_lines = ["// gen-memwrap filelist"]
    for p in flist:
        if p not in seen:
            seen.add(p)
            fl_lines.append(p)
    # also all rtl/*.v
    for p in sorted((out / "rtl").glob("*.v")):
        sp = str(p.resolve())
        if sp not in seen:
            fl_lines.append(sp)
            seen.add(sp)
    (out / "filelist.f").write_text("\n".join(fl_lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="gen-memwrap open-source backend")
    ap.add_argument("excel", nargs="?", help="Excel path")
    ap.add_argument("sheet_name", nargs="?", help="sheet name substring to match")
    ap.add_argument("output_dir", nargs="?", help="output directory")
    ap.add_argument(
        "platform",
        nargs="?",
        default="auto",
        help="sky130 | nangate45 | auto (use PLATFORM column)",
    )
    ap.add_argument(
        "--relaxed",
        action="store_true",
        help="allow nearest larger catalog macro when exact size missing (if generate off)",
    )
    gen_grp = ap.add_mutually_exclusive_group()
    gen_grp.add_argument(
        "--generate",
        dest="generate",
        action="store_true",
        default=True,
        help="on catalog miss, run OpenRAM / bsg_fakeram / builtin FakeRAM (default)",
    )
    gen_grp.add_argument(
        "--no-generate",
        dest="generate",
        action="store_false",
        help="disable online generation; catalog-only (or --relaxed nearest)",
    )
    ap.add_argument(
        "--status",
        action="store_true",
        help="print generator discovery status and exit",
    )
    args = ap.parse_args(argv)

    if args.status:
        print(generator_status())
        return 0

    if not args.excel or not args.sheet_name or not args.output_dir:
        ap.error("excel, sheet_name, output_dir are required (unless --status)")

    excel = Path(args.excel).expanduser().resolve()
    if not excel.is_file():
        print(f"ERROR: excel not found: {excel}", file=sys.stderr)
        return 2
    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    default_platform = "sky130"
    if args.platform in SUPPORTED_PLATFORMS:
        default_platform = args.platform
    elif args.platform not in {"auto", ""}:
        print(f"ERROR: bad platform {args.platform}", file=sys.stderr)
        return 2

    print(generator_status())
    print(f"Info: online generate = {args.generate}")

    # preload catalogs used
    catalogs: Dict[str, List[Macro]] = {}
    for p in SUPPORTED_PLATFORMS:
        try:
            _, macros = load_catalog(p)
            catalogs[p] = macros
            print(f"Info: loaded catalog {p}: {len(macros)} macros")
        except Exception as e:
            print(f"WARN: catalog {p}: {e}")

    rows = read_excel_rows(excel, args.sheet_name, default_platform)
    if not rows:
        print("ERROR: no valid memory rows found", file=sys.stderr)
        return 2
    print(f"Info: {len(rows)} memory row(s) from sheet matching '{args.sheet_name}'")

    results: List[GenResult] = []
    errors: List[str] = []
    for req in rows:
        if req.platform not in catalogs:
            errors.append(f"row {req.row}: catalog {req.platform} unavailable")
            continue
        try:
            r = process_row(
                req,
                catalogs,
                out,
                strict=not args.relaxed,
                do_generate=args.generate,
            )
            results.append(r)
            print(
                f"OK  [{req.platform}] {req.mem_type} {req.depth}x{req.width} "
                f"→ {r.wrap_name} macro={r.macro_name} {r.notes}"
            )
        except Exception as e:
            errors.append(f"row {req.row} ({req.mem_type} {req.depth}x{req.width}): {e}")
            print(f"FAIL row {req.row}: {e}", file=sys.stderr)

    if results:
        write_report(out, results)
        print(f"Info: outputs under {out}")
        print(f"  rtl/ lib/ lef/ beh/ generated/ report/ filelist.f")

    if errors:
        print(f"ERROR: {len(errors)} failure(s)", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("## gen-memwrap successful ##")
    return 0


if __name__ == "__main__":
    sys.exit(main())
