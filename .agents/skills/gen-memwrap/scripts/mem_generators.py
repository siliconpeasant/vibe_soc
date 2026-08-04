#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Online memory macro generators for gen-memwrap.

Backends:
  * OpenRAM  (sky130)     — env OPENRAM_HOME / OPENRAM_COMPILER
  * bsg_fakeram (n45)     — env BSG_FAKERAM / FAKERAM_HOME
  * builtin FakeRAM       — always available for nangate45 (lib/lef/v)

OpenRAM is required for real sky130 macros; without it generation fails with
install instructions. nangate45 falls back to the builtin black-box emitter
when bsg_fakeram is missing.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class GeneratedMacro:
    name: str
    depth: int
    width: int
    ports: str
    write_size: int
    family: str
    assets: Dict[str, Optional[Path]]
    notes: str = ""


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _which(name: str) -> Optional[Path]:
    p = shutil.which(name)
    return Path(p).resolve() if p else None


def resolve_openram() -> Tuple[Optional[Path], str]:
    """Return (compiler_script, status_message)."""
    env_comp = os.environ.get("OPENRAM_COMPILER", "").strip()
    if env_comp:
        p = Path(env_comp).expanduser().resolve()
        if p.is_file():
            return p, f"OPENRAM_COMPILER={p}"
    home = os.environ.get("OPENRAM_HOME", "").strip()
    if home:
        h = Path(home).expanduser().resolve()
        # OPENRAM_HOME is usually .../compiler; sram_compiler.py sits one level up
        candidates = [
            h.parent / "sram_compiler.py",
            h / "sram_compiler.py",
            h / "openram.py",
            h.parent / "openram.py",
        ]
        for cand in candidates:
            if cand.is_file():
                return cand, f"OPENRAM_HOME → {cand}"
    w = _which("openram")
    if w:
        return w, f"PATH openram={w}"
    return None, (
        "OpenRAM not found. Set OPENRAM_HOME / OPENRAM_COMPILER / "
        "OPENRAM_TECH / PDK_ROOT (see gen-memwrap SKILL.md)."
    )


def _resolve_openram_python() -> str:
    """Prefer OpenRAM conda python; fall back to sys.executable."""
    env_py = os.environ.get("OPENRAM_PYTHON", "").strip()
    if env_py and Path(env_py).is_file():
        return env_py
    for cand in (
        Path(os.environ.get("OPENRAM_HOME", "")).expanduser().resolve().parent
        / "conda-env"
        / "bin"
        / "python",
    ):
        if cand.is_file():
            return str(cand)
    return sys.executable


def resolve_bsg_fakeram() -> Tuple[Optional[Path], str]:
    """Return (entry_script, status_message)."""
    for key in ("BSG_FAKERAM", "FAKERAM_HOME"):
        root = os.environ.get(key, "").strip()
        if not root:
            continue
        r = Path(root).expanduser().resolve()
        if r.is_file() and r.suffix == ".py":
            return r, f"{key}={r}"
        if r.is_dir():
            for name in (
                "generate.py",
                "run.py",
                "fakeram.py",
                "bsg_fakeram.py",
                "scripts/generate.py",
            ):
                f = r / name
                if f.is_file():
                    return f, f"{key} → {f}"
    w = _which("bsg_fakeram") or _which("fakeram")
    if w:
        return w, f"PATH {w}"
    return None, (
        "bsg_fakeram not found. Set BSG_FAKERAM to the repo root "
        "(https://github.com/bespoke-silicon-group/bsg_fakeram). "
        "Will use builtin FakeRAM emitter for nangate45."
    )


def generator_status() -> str:
    _, omsg = resolve_openram()
    _, fmsg = resolve_bsg_fakeram()
    return f"OpenRAM: {omsg}\nFakeRAM: {fmsg}\nBuiltin FakeRAM (nangate45): available"


# ---------------------------------------------------------------------------
# OpenRAM (sky130)
# ---------------------------------------------------------------------------


def _openram_config_text(
    name: str,
    depth: int,
    width: int,
    write_size: int,
    ports: str,
    out_dir: Path,
) -> str:
    num_rw, num_r, num_w = 1, 0, 0
    ports = (ports or "1rw").lower()
    if ports == "1rw1r":
        num_rw, num_r, num_w = 1, 1, 0
    elif ports == "1r1w":
        num_rw, num_r, num_w = 0, 1, 1
    elif ports == "2rw":
        num_rw, num_r, num_w = 2, 0, 0
    out_path = str(out_dir.resolve())
    return f'''# AUTO-GENERATED OpenRAM config by gen-memwrap
word_size = {width}
num_words = {depth}
write_size = {write_size}
num_rw_ports = {num_rw}
num_r_ports = {num_r}
num_w_ports = {num_w}
ports_human = "{ports}"
tech_name = "sky130"
nominal_corner_only = True
local_array_size = 16
route_supplies = False
check_lvsdrc = False
use_nix = False
output_name = "{name}"
output_path = r"{out_path}"
'''


def generate_openram(
    depth: int,
    width: int,
    ports: str,
    write_size: int,
    work_dir: Path,
    timeout_sec: int = 7200,
    netlist_only: bool = True,
) -> GeneratedMacro:
    compiler, status = resolve_openram()
    if compiler is None:
        raise RuntimeError(status)

    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    default_home = Path(os.environ.get("OPENRAM_HOME", "")).expanduser()
    default_tech = Path(os.environ.get("OPENRAM_TECH", "")).expanduser()
    default_pdk = Path(os.environ.get("PDK_ROOT", "")).expanduser()
    if default_home.is_dir():
        env.setdefault("OPENRAM_HOME", str(default_home))
    else:
        env.setdefault("OPENRAM_HOME", str(compiler.parent))
    if default_tech.is_dir():
        env.setdefault("OPENRAM_TECH", str(default_tech))
    else:
        env.setdefault("OPENRAM_TECH", str(Path(env["OPENRAM_HOME"]).parent / "technology"))
    if default_pdk.is_dir():
        env.setdefault("PDK_ROOT", str(default_pdk))
    else:
        env.setdefault("PDK_ROOT", str(Path.cwd()))
    env["PYTHONPATH"] = env["OPENRAM_HOME"] + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    ports = (ports or "1rw1r").lower()
    if ports not in {"1rw", "1rw1r", "1r1w", "2rw"}:
        ports = "1rw1r"
    name = f"sky130_sram_{ports}_{width}x{depth}_{write_size}"
    gen_dir = work_dir / "generated" / "sky130" / name
    gen_dir.mkdir(parents=True, exist_ok=True)
    cfg = gen_dir / f"{name}_config.py"
    cfg.write_text(
        _openram_config_text(name, depth, width, write_size, ports, gen_dir),
        encoding="utf-8",
    )

    py = _resolve_openram_python()
    # -n disables LVS/DRC checks; still writes v/lib/lef/gds
    cmd = [py, "-u", str(compiler)]
    if netlist_only:
        cmd.append("-n")
    cmd += ["-v", "-p", str(gen_dir), "-o", name, str(cfg)]

    log_path = gen_dir / "openram.log"
    print(f"Info: running OpenRAM → {name}")
    print(f"Info: {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(gen_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"OpenRAM timed out after {timeout_sec}s for {name}") from e

    log_path.write_text(
        (proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or ""),
        encoding="utf-8",
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise RuntimeError(
            f"OpenRAM failed (exit {proc.returncode}) for {name}. "
            f"See {log_path}\n{tail}"
        )

    assets = _collect_assets(gen_dir, name)
    if not any(assets.values()):
        assets = _collect_assets_recursive(gen_dir, name)
    if assets.get("lib") is None:
        libs = sorted(gen_dir.glob(f"{name}*.lib"))
        if libs:
            assets["lib"] = libs[0].resolve()
    if assets.get("v") is None and assets.get("lib") is None:
        raise RuntimeError(
            f"OpenRAM finished but no .v/.lib found under {gen_dir}. See {log_path}"
        )

    return GeneratedMacro(
        name=name,
        depth=depth,
        width=width,
        ports=ports,
        write_size=write_size,
        family="openram",
        assets=assets,
        notes=f"openram online; {status}",
    )


def _collect_assets(d: Path, name: str) -> Dict[str, Optional[Path]]:
    def pick(patterns: List[str]) -> Optional[Path]:
        for pat in patterns:
            hits = sorted(d.glob(pat))
            if hits:
                return hits[0].resolve()
        return None

    return {
        "v": pick([f"{name}.v", f"**/{name}.v", "*.v"]),
        "lib": pick([f"{name}*.lib", f"**/{name}*.lib", "*.lib"]),
        "lef": pick([f"{name}.lef", f"**/{name}.lef", "*.lef"]),
        "gds": pick([f"{name}.gds", f"**/{name}.gds", "*.gds"]),
    }


def _collect_assets_recursive(d: Path, name: str) -> Dict[str, Optional[Path]]:
    assets: Dict[str, Optional[Path]] = {"v": None, "lib": None, "lef": None, "gds": None}
    for f in d.rglob("*"):
        if not f.is_file():
            continue
        s = f.suffix.lower()
        key = {".v": "v", ".lib": "lib", ".lef": "lef", ".gds": "gds"}.get(s)
        if key and assets[key] is None:
            if name in f.name or key != "v":
                assets[key] = f.resolve()
    # prefer name match for v
    for f in d.rglob(f"{name}.v"):
        assets["v"] = f.resolve()
        break
    return assets


# ---------------------------------------------------------------------------
# bsg_fakeram
# ---------------------------------------------------------------------------


def _nangate45_fakeram_cfg(name: str, depth: int, width: int) -> dict:
    """Base tech knobs from ORFS nangate45/fakeram.cfg."""
    return {
        "tech_nm": 45,
        "voltage": 1.1,
        "metalPrefix": "metal",
        "pinWidth_nm": 70,
        "pinPitch_nm": 280,
        "snapWidth_nm": 190,
        "snapHeight_nm": 1400,
        "swapWidthHeight": True,
        "flipPins": True,
        "libertyTimeUnit": "ns",
        "libertyCapUnit": "ff",
        "libertyPowerUnit": "nw",
        "srams": [{"name": name, "width": width, "depth": depth, "banks": 1}],
    }


def generate_bsg_fakeram(
    depth: int,
    width: int,
    work_dir: Path,
    timeout_sec: int = 600,
) -> GeneratedMacro:
    entry, status = resolve_bsg_fakeram()
    if entry is None:
        raise RuntimeError(status)

    name = f"fakeram45_{depth}x{width}"
    gen_dir = work_dir / "generated" / "nangate45" / name
    gen_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = gen_dir / f"{name}.cfg"
    cfg_path.write_text(
        json.dumps(_nangate45_fakeram_cfg(name, depth, width), indent=2) + "\n",
        encoding="utf-8",
    )

    cmd = [sys.executable, "-u", str(entry), str(cfg_path)]
    # Some forks take -c / --config
    log_path = gen_dir / "bsg_fakeram.log"
    print(f"Info: running bsg_fakeram → {name}")
    print(f"Info: {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(entry.parent if entry.is_file() else entry),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    log_path.write_text(
        (proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or ""),
        encoding="utf-8",
    )
    if proc.returncode != 0:
        # retry with cwd=gen_dir
        proc2 = subprocess.run(
            cmd,
            cwd=str(gen_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        log_path.write_text(
            log_path.read_text(encoding="utf-8")
            + "\n--- retry cwd=gen_dir ---\n"
            + (proc2.stdout or "")
            + "\n--- stderr ---\n"
            + (proc2.stderr or ""),
            encoding="utf-8",
        )
        if proc2.returncode != 0:
            raise RuntimeError(
                f"bsg_fakeram failed (exit {proc.returncode}/{proc2.returncode}). "
                f"See {log_path}"
            )

    # Collect from gen_dir and common results/ layouts
    search_roots = [gen_dir, entry.parent / "results", Path.cwd() / "results"]
    assets: Dict[str, Optional[Path]] = {"v": None, "lib": None, "lef": None, "gds": None}
    for root in search_roots:
        if not root or not Path(root).is_dir():
            continue
        found = _collect_assets_recursive(Path(root), name)
        for k, v in found.items():
            if v and assets[k] is None:
                assets[k] = v

    # Copy into gen_dir for stable paths
    stable: Dict[str, Optional[Path]] = {}
    for k, src in assets.items():
        if src and src.is_file():
            dst = gen_dir / src.name
            if dst.resolve() != src.resolve():
                shutil.copy2(src, dst)
            stable[k] = dst.resolve()
        else:
            stable[k] = None

    if stable.get("lib") is None and stable.get("lef") is None:
        raise RuntimeError(f"bsg_fakeram produced no lib/lef. See {log_path}")

    return GeneratedMacro(
        name=name,
        depth=depth,
        width=width,
        ports="1rw",
        write_size=1,
        family="fakeram",
        assets=stable,
        notes=f"bsg_fakeram online; {status}",
    )


# ---------------------------------------------------------------------------
# Builtin FakeRAM (nangate45) — no external tool
# ---------------------------------------------------------------------------


def _snap(val: float, grid: float) -> float:
    return math.ceil(val / grid - 1e-12) * grid


def generate_builtin_fakeram(
    depth: int,
    width: int,
    work_dir: Path,
) -> GeneratedMacro:
    """Emit black-box .lib/.lef + behavioral .v compatible with ORFS FakeRAM ports."""
    name = f"fakeram45_{depth}x{width}"
    gen_dir = work_dir / "generated" / "nangate45" / name
    gen_dir.mkdir(parents=True, exist_ok=True)

    aw = max(1, math.ceil(math.log2(depth)))
    pin_pitch = 0.280  # um
    pin_w = 0.070
    # estimate height from pin count on left edge
    n_left = width * 3 + aw + 3  # mask + rd + wd + addr + ctrl-ish
    height = _snap(max(n_left * pin_pitch + 2.0, 10.0), 1.400)
    # area ~ 0.55 um^2 / bit (ballpark vs ORFS fakeram45_64x32 ≈ 0.61)
    area = max(depth * width * 0.55, height * 8.0)
    mac_w = _snap(max(area / height, 8.0), 0.190)

    lef_path = gen_dir / f"{name}.lef"
    lib_path = gen_dir / f"{name}.lib"
    v_path = gen_dir / f"{name}.v"

    _write_fakeram_lef(lef_path, name, mac_w, height, depth, width, aw, pin_pitch, pin_w)
    _write_fakeram_lib(lib_path, name, depth, width, aw, area_um2=mac_w * height)
    _write_fakeram_v(v_path, name, depth, width, aw)

    return GeneratedMacro(
        name=name,
        depth=depth,
        width=width,
        ports="1rw",
        write_size=1,
        family="fakeram-builtin",
        assets={"v": v_path.resolve(), "lib": lib_path.resolve(), "lef": lef_path.resolve(), "gds": None},
        notes="builtin FakeRAM black-box (no bsg_fakeram/CACTI)",
    )


def _write_fakeram_lef(
    path: Path,
    name: str,
    mac_w: float,
    height: float,
    depth: int,
    width: int,
    aw: int,
    pin_pitch: float,
    pin_w: float,
) -> None:
    lines = [
        "VERSION 5.7 ;",
        'BUSBITCHARS "[]" ;',
        f"MACRO {name}",
        f"  FOREIGN {name} 0 0 ;",
        "  SYMMETRY X Y R90 ;",
        f"  SIZE {mac_w:.3f} BY {height:.3f} ;",
        "  CLASS BLOCK ;",
    ]
    y = 2.800
    # Order similar to ORFS: w_mask, rd_out, wd_in, addr, controls
    pin_list: List[Tuple[str, str]] = []
    for i in range(width):
        pin_list.append((f"w_mask_in[{i}]", "INPUT"))
    for i in range(width):
        pin_list.append((f"rd_out[{i}]", "OUTPUT"))
    for i in range(width):
        pin_list.append((f"wd_in[{i}]", "INPUT"))
    for i in range(aw):
        pin_list.append((f"addr_in[{i}]", "INPUT"))
    pin_list += [
        ("we_in", "INPUT"),
        ("ce_in", "INPUT"),
        ("clk", "INPUT"),
        ("VDD", "INOUT"),
        ("VSS", "INOUT"),
    ]
    for pname, direction in pin_list:
        use = "POWER" if pname == "VDD" else ("GROUND" if pname == "VSS" else "SIGNAL")
        layer = "metal4" if pname in {"VDD", "VSS"} else "metal3"
        lines += [
            f"  PIN {pname}",
            f"    DIRECTION {direction} ;",
            f"    USE {use} ;",
            "    SHAPE ABUTMENT ;",
            "    PORT",
            f"      LAYER {layer} ;",
            f"      RECT 0.000 {y:.3f} {pin_w:.3f} {y + pin_w:.3f} ;",
            "    END",
            f"  END {pname}",
        ]
        y += pin_pitch
        if y + pin_w > height - 0.5:
            y = 2.800  # wrap (still on left; black-box only)
    lines += [f"END {name}", "END LIBRARY", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_fakeram_lib(
    path: Path, name: str, depth: int, width: int, aw: int, area_um2: float
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    # Minimal liberty: setup on control, delay on rd_out
    lines = [
        f"library({name}) {{",
        "  technology (cmos);",
        "  delay_model : table_lookup;",
        '  date : "' + now + '";',
        '  comment : "gen-memwrap builtin FakeRAM black-box";',
        '  time_unit : "1ns";',
        '  voltage_unit : "1V";',
        '  current_unit : "1uA";',
        '  leakage_power_unit : "1nw";',
        "  nom_process : 1;",
        "  nom_temperature : 25.0;",
        "  nom_voltage : 1.1;",
        "  capacitive_load_unit (1,ff);",
        "  pulling_resistance_unit : \"1kohm\";",
        "  operating_conditions(tt_1.1_25.0) {",
        "    process : 1; temperature : 25.0; voltage : 1.1;",
        "    tree_type : balanced_tree;",
        "  }",
        "  default_operating_conditions : tt_1.1_25.0;",
        "  default_max_transition : 0.5;",
        f"  type ({name}_DATA) {{ base_type : array; data_type : bit; bit_width : {width}; bit_from : {width-1}; bit_to : 0; downto : true; }}",
        f"  type ({name}_ADDR) {{ base_type : array; data_type : bit; bit_width : {aw}; bit_from : {aw-1}; bit_to : 0; downto : true; }}",
        f"  cell({name}) {{",
        f"    area : {area_um2:.3f};",
        "    interface_timing : true;",
        "    memory() { type : ram; "
        + f"address_width : {aw}; word_width : {width}; }}",
        "    pin(clk) { direction : input; capacitance : 10.0; clock : true; }",
        "    pin(ce_in) { direction : input; capacitance : 5.0; }",
        "    pin(we_in) { direction : input; capacitance : 5.0; }",
        f"    bus(addr_in) {{ bus_type : {name}_ADDR; direction : input;",
        f"      pin(addr_in[{aw-1}:0]) {{ capacitance : 2.0; }} }}",
        f"    bus(wd_in) {{ bus_type : {name}_DATA; direction : input;",
        f"      pin(wd_in[{width-1}:0]) {{ capacitance : 2.0; }} }}",
        f"    bus(w_mask_in) {{ bus_type : {name}_DATA; direction : input;",
        f"      pin(w_mask_in[{width-1}:0]) {{ capacitance : 2.0; }} }}",
        f"    bus(rd_out) {{ bus_type : {name}_DATA; direction : output;",
        f"      pin(rd_out[{width-1}:0]) {{",
        "        timing() {",
        "          related_pin : \"clk\";",
        "          timing_type : rising_edge;",
        "          cell_rise(scalar) { values(\"0.50\"); }",
        "          cell_fall(scalar) { values(\"0.50\"); }",
        "          rise_transition(scalar) { values(\"0.05\"); }",
        "          fall_transition(scalar) { values(\"0.05\"); }",
        "        }",
        "      }",
        "    }",
        "  }",
        "}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_fakeram_v(path: Path, name: str, depth: int, width: int, aw: int) -> None:
    lines = [
        f"// Builtin FakeRAM behavioral model — {name}",
        f"module {name} (",
        f"  output reg [{width-1}:0] rd_out,",
        f"  input  [{aw-1}:0]      addr_in,",
        "  input                  we_in,",
        f"  input  [{width-1}:0]   wd_in,",
        "  input                  clk,",
        "  input                  ce_in,",
        f"  input  [{width-1}:0]   w_mask_in",
        ");",
        f"  reg [{width-1}:0] mem [0:{depth-1}];",
        "  integer i;",
        "  always @(posedge clk) begin",
        "    if (ce_in) begin",
        "      if (we_in) begin",
        f"        for (i = 0; i < {width}; i = i + 1)",
        "          if (w_mask_in[i]) mem[addr_in][i] <= wd_in[i];",
        "      end",
        "      rd_out <= mem[addr_in];",
        "    end",
        "  end",
        "endmodule",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def generate_macro(
    platform: str,
    depth: int,
    width: int,
    ports: str,
    write_size: int,
    work_dir: Path,
    prefer_external: bool = True,
    openram_timeout: int = 7200,
) -> GeneratedMacro:
    """Generate a new macro for platform. Raises RuntimeError on hard failure."""
    platform = platform.lower()
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if platform == "sky130":
        return generate_openram(
            depth=depth,
            width=width,
            ports=ports or "1rw1r",
            write_size=write_size or 8,
            work_dir=work_dir,
            timeout_sec=openram_timeout,
        )

    if platform == "nangate45":
        if prefer_external:
            entry, _ = resolve_bsg_fakeram()
            if entry is not None:
                try:
                    return generate_bsg_fakeram(depth, width, work_dir)
                except Exception as e:
                    print(f"WARN: bsg_fakeram failed ({e}); falling back to builtin")
        return generate_builtin_fakeram(depth, width, work_dir)

    raise ValueError(f"online generate unsupported platform: {platform}")


if __name__ == "__main__":
    print(generator_status())
    if len(sys.argv) >= 4 and sys.argv[1] == "test-builtin":
        d, w = int(sys.argv[2]), int(sys.argv[3])
        out = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("tmp/fakeram_test")
        m = generate_builtin_fakeram(d, w, out)
        print(m)
