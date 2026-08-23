#!/usr/bin/env python3
"""DFT readiness scan and SpyGlass DFT SGDC/Tcl generator.

Commands:
  readiness  — classify top ports / RTL text for DFT hooks
  from-rtl   — RTL top ports → starter .sgdc (+ optional .tcl)
  gen        — YAML/JSON config → .sgdc (+ optional .tcl)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


# ---------------------------------------------------------------------------
# Lightweight port parsing (mirrors sdc-gen/rtl_ports spirit; self-contained)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    msb: Optional[int] = None
    lsb: Optional[int] = None

    @property
    def width(self) -> int:
        if self.msb is None or self.lsb is None:
            return 1
        return abs(self.msb - self.lsb) + 1

    @property
    def is_bus(self) -> bool:
        return self.width > 1


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated module port list")


def split_top_level_commas(text: str) -> List[str]:
    parts: List[str] = []
    start = 0
    square = paren = brace = 0
    for index, char in enumerate(text):
        if char == "[":
            square += 1
        elif char == "]" and square:
            square -= 1
        elif char == "(":
            paren += 1
        elif char == ")" and paren:
            paren -= 1
        elif char == "{":
            brace += 1
        elif char == "}" and brace:
            brace -= 1
        elif char == "," and square == paren == brace == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def find_module(text: str, top: Optional[str]) -> Tuple[str, str, str]:
    pattern = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)")
    for match in pattern.finditer(text):
        name = match.group(1)
        if top and name != top:
            continue
        pos = match.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos < len(text) and text[pos] == "#":
            pos += 1
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text) or text[pos] != "(":
                raise ValueError(f"malformed parameter list for module {name}")
            pos = matching_paren(text, pos) + 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != "(":
            continue
        end = matching_paren(text, pos)
        ports = text[pos + 1 : end]
        body_start = end + 1
        body_end_match = re.search(r"\bendmodule\b", text[body_start:])
        body_end = body_start + body_end_match.start() if body_end_match else len(text)
        return name, ports, text[body_start:body_end]
    wanted = top or "first module"
    raise ValueError(f"module not found: {wanted}")


def parse_range(tokens: List[str]) -> Tuple[Optional[int], Optional[int], List[str]]:
    rest: List[str] = []
    msb = lsb = None
    for token in tokens:
        if token.startswith("[") and token.endswith("]"):
            m = re.match(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", token)
            if m:
                msb, lsb = int(m.group(1)), int(m.group(2))
        else:
            rest.append(token)
    return msb, lsb, rest


_DIR_RE = re.compile(r"^(input|output|inout)$", re.I)
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def parse_ansi_ports(port_text: str) -> List[Port]:
    ports: List[Port] = []
    for chunk in split_top_level_commas(port_text):
        if not chunk or chunk.startswith("."):
            continue
        tokens = re.findall(r"\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_$]*|[^,\s\[\]]+", chunk)
        if not tokens:
            continue
        direction = "input"
        idx = 0
        if _DIR_RE.match(tokens[0]):
            direction = tokens[0].lower()
            idx = 1
        while idx < len(tokens) and tokens[idx] in {
            "wire",
            "reg",
            "logic",
            "signed",
            "unsigned",
            "tri",
            "wand",
            "wor",
        }:
            idx += 1
        msb = lsb = None
        if idx < len(tokens) and tokens[idx].startswith("["):
            msb, lsb, _ = parse_range([tokens[idx]])
            idx += 1
        names = [t for t in tokens[idx:] if _IDENT_RE.match(t)]
        for name in names:
            ports.append(Port(name=name, direction=direction, msb=msb, lsb=lsb))
    return ports


def parse_body_ports(body: str) -> List[Port]:
    ports: List[Port] = []
    for match in re.finditer(
        r"\b(input|output|inout)\b([^;]*);", body, flags=re.I | re.S
    ):
        direction = match.group(1).lower()
        rest = match.group(2)
        tokens = re.findall(r"\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_$]*", rest)
        msb = lsb = None
        names: List[str] = []
        for token in tokens:
            if token.startswith("["):
                m = re.match(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", token)
                if m:
                    msb, lsb = int(m.group(1)), int(m.group(2))
            elif token.lower() in {"wire", "reg", "logic", "signed", "unsigned"}:
                continue
            elif _IDENT_RE.match(token):
                names.append(token)
        for name in names:
            ports.append(Port(name=name, direction=direction, msb=msb, lsb=lsb))
    return ports


def parse_rtl_ports(rtl_path: Path, module: str = "") -> Tuple[str, List[Port], str]:
    raw = rtl_path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments(raw)
    name, port_text, body = find_module(text, module or None)
    ports = parse_ansi_ports(port_text)
    if not ports:
        ports = parse_body_ports(body)
    if not ports:
        raise ValueError(f"no ports parsed for module {name}")
    # de-dupe by name preserving order
    seen = set()
    unique: List[Port] = []
    for port in ports:
        if port.name in seen:
            continue
        seen.add(port.name)
        unique.append(port)
    return name, unique, raw


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

_CLK_RE = re.compile(
    r"(^|_)(clk|clock|aclk|pclk|sclk|bclk|mclk|hclk|gclk|refclk|sysclk|core_?clk|xtal|tck)(_|$)",
    re.I,
)
_FUNC_RST_RE = re.compile(r"(^|_)(rst|reset|por|nrst|nreset|arst|preset|hreset)(_|$|n$)", re.I)
_TEST_MODE_RE = re.compile(r"(test_mode|scan_mode|dft_mode|tm_in\b)", re.I)
_SCAN_EN_RE = re.compile(r"(scan_en|scan_enable|(^|_)se($|_)|shift_en)", re.I)
_TEST_RST_RE = re.compile(
    r"(test_rst|test_rstn|scan_rst|scan_rstn|dft_.*rst|dft_div_rst)",
    re.I,
)
_DFT_RST_DIS_RE = re.compile(r"(dftrstdisable|dft_rst_disable|dft_rst_dis)", re.I)
_SCAN_IO_RE = re.compile(r"(scan_in|scan_out|(^|_)si($|_)|(^|_)so($|_))", re.I)
_JTAG_RE = re.compile(r"(^|_)(tck|tms|tdi|tdo|trst)(_|$|n$)", re.I)
_MBIST_RE = re.compile(r"(mbist|bist_)", re.I)
_CAPTURE_RE = re.compile(r"(capture_en|capt_en)", re.I)


@dataclass
class CategoryHit:
    category: str
    level: str  # must | recommended
    ports: List[str] = field(default_factory=list)
    body_hits: List[str] = field(default_factory=list)

    @property
    def present(self) -> bool:
        return bool(self.ports or self.body_hits)


def _match_ports(ports: Sequence[Port], pattern: re.Pattern[str]) -> List[str]:
    return [p.name for p in ports if pattern.search(p.name)]


def _body_names(raw: str, pattern: re.Pattern[str], limit: int = 20) -> List[str]:
    hits: List[str] = []
    for match in pattern.finditer(raw):
        # grab nearby identifier-ish token
        start = max(0, match.start() - 40)
        end = min(len(raw), match.end() + 40)
        window = raw[start:end]
        for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", window):
            if pattern.search(ident) and ident not in hits:
                hits.append(ident)
                if len(hits) >= limit:
                    return hits
    return hits


def classify_dft(ports: Sequence[Port], raw: str) -> List[CategoryHit]:
    categories = [
        ("test_mode", "must", _TEST_MODE_RE),
        ("scan_enable", "must", _SCAN_EN_RE),
        ("test_reset", "must", _TEST_RST_RE),
        ("functional_reset", "must", _FUNC_RST_RE),
        ("clock", "must", _CLK_RE),
        ("dft_reset_disable", "recommended", _DFT_RST_DIS_RE),
        ("scan_io", "recommended", _SCAN_IO_RE),
        ("jtag", "recommended", _JTAG_RE),
        ("mbist", "recommended", _MBIST_RE),
        ("capture_en", "recommended", _CAPTURE_RE),
    ]
    results: List[CategoryHit] = []
    for name, level, pattern in categories:
        port_hits = _match_ports(ports, pattern)
        # functional_reset should exclude pure test resets when possible
        if name == "functional_reset":
            port_hits = [
                n
                for n in port_hits
                if not _TEST_RST_RE.search(n) and not _DFT_RST_DIS_RE.search(n)
            ]
        body_hits = []
        if not port_hits and name in {
            "test_mode",
            "scan_enable",
            "test_reset",
            "dft_reset_disable",
            "mbist",
        }:
            body_hits = _body_names(raw, pattern)
        results.append(
            CategoryHit(
                category=name,
                level=level,
                ports=port_hits,
                body_hits=body_hits,
            )
        )
    return results


# ---------------------------------------------------------------------------
# SGDC / Tcl emit
# ---------------------------------------------------------------------------

def _require_mapping(data: Any, label: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a mapping")
    return data


def load_config(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise SystemExit("PyYAML is required: pip install pyyaml")
        raw = yaml.safe_load(text) or {}
    elif path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raise ValueError(f"unsupported config type: {path.suffix}")
    return _require_mapping(raw, "config")


def render_sgdc(
    design: str,
    test_modes: Sequence[Dict[str, Any]],
    resets: Sequence[Dict[str, Any]],
    clocks: Sequence[Dict[str, Any]],
    notes: Sequence[str] = (),
) -> str:
    lines: List[str] = [
        f"# Generated by dft-gen on {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "# Review hierarchical paths before SpyGlass DFT signoff.",
    ]
    for note in notes:
        lines.append(f"# {note}")
    lines.append(f"current_design {design}")
    lines.append("")
    if test_modes:
        lines.append("# test_mode")
        for item in test_modes:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            value = item.get("value", 1)
            lines.append(f"test_mode -name {name} -value {value}")
        lines.append("")
    if resets:
        lines.append("# reset")
        for item in resets:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            value = item.get("value", 0)
            lines.append(f"reset -name {name} -value {value}")
        lines.append("")
    if clocks:
        lines.append("# clock")
        for item in clocks:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            parts = [f"clock -name {name}"]
            if item.get("atspeed") or item.get("testclock"):
                if item.get("atspeed", True):
                    parts.append("-atspeed")
                if item.get("testclock", True):
                    parts.append("-testclock")
            period = item.get("period", item.get("period_ns"))
            if period is not None:
                parts.append(f"-period {period}")
            edge = item.get("edge", "0 1" if item.get("testclock") else None)
            if edge:
                parts.append(f"-edge {{{edge}}}")
            lines.append(" ".join(parts))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_module_tcl(
    top: str,
    sgdc_rel: str,
    *,
    goal: str = "dft/dft_scan_ready",
    best_practice: bool = False,
    lib_tcl: str = "",
    awl: str = "",
) -> str:
    lines = [
        f"# Generated DFT driver collateral for {top}",
        f"# Registered run still goes through scripts/dft/sg_dft.tcl + make dft",
        f"# SGDC: {sgdc_rel}",
        "",
    ]
    if lib_tcl:
        lines.append(f"# source {lib_tcl}")
    if awl:
        lines.append(f"# read_file -type awl {awl}")
    lines.extend(
        [
            "set_option language_mode mixed",
            "set_option enableSV yes",
            "set_option enableSV09 yes",
            f"set_option top {top}",
            f"read_file -type sgdc {sgdc_rel}",
            f"current_goal {goal} -top {top}",
            "run_goal",
        ]
    )
    if best_practice:
        lines.extend(
            [
                f"current_goal dft/dft_best_practice -top {top}",
                "run_goal",
            ]
        )
    else:
        lines.append(f"# current_goal dft/dft_best_practice -top {top}")
    lines.append("")
    return "\n".join(lines)


def emit_artifacts(paths: Dict[str, str], extra: Optional[Dict[str, Any]] = None) -> str:
    payload = {"artifacts": paths}
    if extra:
        payload.update(extra)
    return "DFT_ARTIFACTS=" + json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_readiness(args: argparse.Namespace) -> int:
    rtl = Path(args.rtl).expanduser().resolve()
    if not rtl.is_file():
        raise SystemExit(f"RTL not found: {rtl}")
    name, ports, raw = parse_rtl_ports(rtl, args.module)
    cats = classify_dft(ports, raw)
    must_missing = [
        c.category for c in cats if c.level == "must" and not c.present
    ]
    # scan_enable is soft-must for pure frontend IP without scan ports yet:
    # if test_mode present but no scan_en, warn rather than hard-fail when --soft-scan
    soft_notes: List[str] = []
    if args.soft_scan and "scan_enable" in must_missing and any(
        c.category == "test_mode" and c.present for c in cats
    ):
        must_missing = [m for m in must_missing if m != "scan_enable"]
        soft_notes.append(
            "scan_enable missing but soft-scan allowed (test_mode present)"
        )
    # test_reset soft when body has rstn_test_mux pattern
    if "test_reset" in must_missing and re.search(r"rstn_test_mux|test_rst", raw, re.I):
        soft_notes.append("test_reset not on top ports but body mentions test reset mux")
    status = "pass" if not must_missing else "fail"
    report = {
        "module": name,
        "rtl": str(rtl),
        "status": status,
        "must_missing": must_missing,
        "categories": [
            {
                "category": c.category,
                "level": c.level,
                "present": c.present,
                "ports": c.ports,
                "body_hits": c.body_hits,
            }
            for c in cats
        ],
        "ports": [asdict(p) for p in ports],
        "notes": soft_notes
        + [
            "Bootstrap checklist; project DFT frontend standard overrides when available."
        ],
    }
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        md = out.with_suffix(".md")
        md_lines = [
            f"# DFT readiness: {name}",
            "",
            f"- Status: **{status}**",
            f"- RTL: `{rtl}`",
            f"- Must missing: {', '.join(must_missing) if must_missing else '(none)'}",
            "",
            "| Category | Level | Present | Ports |",
            "|---|---|---|---|",
        ]
        for c in cats:
            md_lines.append(
                f"| {c.category} | {c.level} | {'yes' if c.present else 'no'} | "
                f"{', '.join(c.ports) or '-'} |"
            )
        if soft_notes:
            md_lines.extend(["", "## Notes", ""])
            md_lines.extend(f"- {n}" for n in soft_notes)
        md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        print(text, end="")
        print(
            emit_artifacts(
                {"readiness_json": str(out), "readiness_md": str(md)},
                {"status": status, "module": name},
            )
        )
    else:
        print(text, end="")
        print(emit_artifacts({}, {"status": status, "module": name}))
    # Always exit 0 so MCP can parse status; fail is encoded in report["status"].
    return 0


def _config_from_ports(
    design: str,
    ports: Sequence[Port],
    period_ns: float,
    testclock: bool,
) -> Dict[str, Any]:
    cats = {c.category: c for c in classify_dft(ports, "")}
    test_modes = [{"name": n, "value": 1} for n in cats["test_mode"].ports]
    if not test_modes and cats["scan_enable"].ports:
        # some designs use scan_en only
        test_modes = [{"name": cats["scan_enable"].ports[0], "value": 1}]
    resets = []
    for n in cats["functional_reset"].ports:
        resets.append({"name": n, "value": 0})
    for n in cats["test_reset"].ports:
        resets.append({"name": n, "value": 0})
    for n in cats["dft_reset_disable"].ports:
        resets.append({"name": n, "value": 0})
    clocks = []
    for n in cats["clock"].ports:
        entry: Dict[str, Any] = {"name": n, "period": period_ns}
        if testclock:
            entry["testclock"] = True
            entry["atspeed"] = True
            entry["edge"] = "0 1"
        clocks.append(entry)
    return {
        "design": design,
        "test_modes": test_modes,
        "resets": resets,
        "clocks": clocks,
        "notes": [
            "Generated from top-level ports only; add hierarchical paths as needed."
        ],
    }


def _write_sgdc_tcl(
    cfg: Dict[str, Any],
    sgdc_path: Path,
    tcl_path: Optional[Path],
    goal: str,
    best_practice: bool,
) -> Dict[str, str]:
    design = str(cfg.get("design") or cfg.get("top") or "").strip()
    if not design:
        raise ValueError("config requires design/top")
    sgdc = render_sgdc(
        design,
        cfg.get("test_modes") or cfg.get("test_mode") or [],
        cfg.get("resets") or [],
        cfg.get("clocks") or [],
        cfg.get("notes") or [],
    )
    sgdc_path.parent.mkdir(parents=True, exist_ok=True)
    sgdc_path.write_text(sgdc, encoding="utf-8")
    artifacts = {"sgdc": str(sgdc_path)}
    if tcl_path:
        tcl = render_module_tcl(
            design,
            str(sgdc_path.name),
            goal=goal,
            best_practice=best_practice,
        )
        tcl_path.parent.mkdir(parents=True, exist_ok=True)
        tcl_path.write_text(tcl, encoding="utf-8")
        artifacts["tcl"] = str(tcl_path)
    return artifacts


def cmd_from_rtl(args: argparse.Namespace) -> int:
    rtl = Path(args.rtl).expanduser().resolve()
    if not rtl.is_file():
        raise SystemExit(f"RTL not found: {rtl}")
    name, ports, _raw = parse_rtl_ports(rtl, args.module)
    cfg = _config_from_ports(name, ports, args.period, args.testclock)
    if args.out:
        sgdc_path = Path(args.out).expanduser().resolve()
    else:
        sgdc_path = rtl.parent / f"{name}_dft.sgdc"
    tcl_path = Path(args.tcl).expanduser().resolve() if args.tcl else None
    artifacts = _write_sgdc_tcl(
        cfg, sgdc_path, tcl_path, args.goal, args.best_practice
    )
    print(f"Wrote {sgdc_path}")
    if tcl_path:
        print(f"Wrote {tcl_path}")
    print(emit_artifacts(artifacts, {"module": name, "source": "from-rtl"}))
    return 0


def cmd_gen(args: argparse.Namespace) -> int:
    cfg_path = Path(args.config).expanduser().resolve()
    if not cfg_path.is_file():
        raise SystemExit(f"config not found: {cfg_path}")
    cfg = load_config(cfg_path)
    design = str(cfg.get("design") or cfg.get("top") or cfg_path.stem)
    if args.out:
        sgdc_path = Path(args.out).expanduser().resolve()
    else:
        sgdc_path = cfg_path.with_name(f"{design}_dft.sgdc")
    tcl_path = Path(args.tcl).expanduser().resolve() if args.tcl else None
    artifacts = _write_sgdc_tcl(
        cfg, sgdc_path, tcl_path, args.goal, args.best_practice
    )
    print(f"Wrote {sgdc_path}")
    if tcl_path:
        print(f"Wrote {tcl_path}")
    print(emit_artifacts(artifacts, {"module": design, "source": "gen"}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DFT readiness + SGDC/Tcl generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("readiness", help="Scan RTL for DFT frontend hooks")
    r.add_argument("--rtl", required=True)
    r.add_argument("-m", "--module", default="")
    r.add_argument("--out", default="", help="Write JSON report path")
    r.add_argument(
        "--soft-scan",
        action="store_true",
        help="Do not fail solely for missing scan_enable when test_mode exists",
    )
    r.set_defaults(func=cmd_readiness)

    f = sub.add_parser("from-rtl", help="Generate starter SGDC from RTL ports")
    f.add_argument("--rtl", required=True)
    f.add_argument("-m", "--module", default="")
    f.add_argument("-o", "--out", default="")
    f.add_argument("--tcl", default="", help="Optional module Tcl path")
    f.add_argument("--period", type=float, default=5.0)
    f.add_argument(
        "--testclock",
        action="store_true",
        help="Mark all detected clocks as -atspeed -testclock",
    )
    f.add_argument("--goal", default="dft/dft_scan_ready")
    f.add_argument("--best-practice", action="store_true")
    f.set_defaults(func=cmd_from_rtl)

    g = sub.add_parser("gen", help="Generate SGDC from YAML/JSON")
    g.add_argument("--config", required=True)
    g.add_argument("-o", "--out", default="")
    g.add_argument("--tcl", default="")
    g.add_argument("--goal", default="dft/dft_scan_ready")
    g.add_argument("--best-practice", action="store_true")
    g.set_defaults(func=cmd_gen)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
