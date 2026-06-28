#!/usr/bin/env python3
"""Generate a SpyGlass compatibility CDC Tcl/SGDC run directory."""

from __future__ import annotations

import argparse
from pathlib import Path


def read_flist(path: Path, project_root: Path) -> list[str]:
    files: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        if line.startswith("+incdir+") or line.startswith("-y ") or line.startswith("+define+"):
            continue
        line = line.replace("$SOC", str(project_root))
        files.append(line)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--filelist", required=True, type=Path)
    parser.add_argument("--top", required=True)
    parser.add_argument("--spyglass-home", required=True, type=Path)
    parser.add_argument("--goal", default="cdc/cdc_verify_struct")
    parser.add_argument("--methodology", default="")
    parser.add_argument("--clock-port", default="clk")
    parser.add_argument("--reset-port", default="rst_n")
    parser.add_argument("--reset-value", default="0")
    parser.add_argument("--sgdc", default=None, type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    sgdc_path = run_dir / "cdc.sgdc"
    if args.sgdc is not None:
        sgdc_src = args.sgdc.resolve()
        if not sgdc_src.exists():
            raise FileNotFoundError(f"SGDC file not found: {sgdc_src}")
        sgdc_path.write_text(sgdc_src.read_text())
    else:
        lines = [f"current_design {args.top}"]
        if args.clock_port:
            lines.append(f"clock -name {args.clock_port}")
        if args.reset_port:
            lines.append(f"reset -name {args.reset_port} -value {args.reset_value}")
        sgdc_path.write_text("\n".join(lines) + "\n")

    methodology = args.methodology or str(args.spyglass_home / "GuideWare/latest/soc/rtl_handoff")
    hdl_files = read_flist(args.filelist, project_root)
    if not hdl_files:
        raise RuntimeError(f"No HDL files found in {args.filelist}")

    read_cmds = "\n".join(f"read_file -type hdl {{{src}}}" for src in hdl_files)
    tcl_path = run_dir / "run_sg_cdc.tcl"
    tcl = (
        f"set env(SPYGLASS_HOME) {args.spyglass_home}\n"
        f"new_project {args.top}_cdc -force\n"
        "set_option language_mode verilog\n"
        "set_option enable_save_restore no\n"
        f"set_option top {args.top}\n"
        f"current_methodology {methodology}\n"
        f"current_goal {args.goal} -alltop\n"
        "read_file -type sgdc {cdc.sgdc}\n"
        f"{read_cmds}\n"
        "run_goal\n"
        "write_report moresimple > moresimple.rpt\n"
        "write_report waiver > waiver.rpt\n"
        "quit\n"
    )
    tcl_path.write_text(tcl)
    print(tcl_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
