#!/usr/bin/env python3
"""Create a traceable vibe_soc design release package."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path


SOURCE_PREFIXES = (
    "Makefile",
    "README.md",
    "AGENTS.md",
    "scripts/",
    "chip/top/Makefile",
    "chip/top/pipeline_state.json",
    "chip/top/de/rtl/",
    "chip/top/dv/tb/",
    "chip/top/dv/tests/",
    "chip/lib/",
    "chip/bus/",
    "chip/core/",
    "chip/periph/",
    "ip/",
    "pd/openroad/nangate45/vibe_soc_top/",
)

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "simv.csrc",
    "simv.daidir",
    "simv.vdb",
    "verdiLog",
}

EXCLUDED_SUFFIXES = (
    ".fsdb",
    ".vpd",
    ".vcd",
    ".pyc",
)

EVIDENCE_PATHS = (
    "chip/top/de/run/.build.fingerprint",
    "chip/top/de/run/compile.log",
    "chip/top/de/run/rtl.f",
    "chip/top/de/run/rtl.raw.f",
    "chip/top/de/run/lint.log",
)

SYN_PATHS = (
    "chip/top/de/syn/rtl.f",
    "chip/top/de/syn/syn.ys",
    "chip/top/de/syn/synth.log",
)


def run_git(root: Path, args: list[str], check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def tracked_files(root: Path) -> list[Path]:
    data = run_git(root, ["ls-files", "-z"])
    return [Path(item) for item in data.split("\0") if item]


def git_sha(root: Path) -> str:
    return run_git(root, ["rev-parse", "HEAD"])


def git_ref(root: Path) -> str:
    ref = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
    if ref and ref != "HEAD":
        return ref
    tag = run_git(root, ["describe", "--tags", "--exact-match"], check=False)
    return tag or os.environ.get("GITHUB_REF_NAME", "detached")


def git_dirty(root: Path) -> bool:
    return bool(run_git(root, ["status", "--porcelain"]))


def selected_source(path: Path) -> bool:
    rel = path.as_posix()
    return any(rel == prefix or rel.startswith(prefix) for prefix in SOURCE_PREFIXES)


def excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_PARTS:
        return True
    rel = path.as_posix()
    if rel.startswith("pd/openroad/work") or "/dv/sim/" in rel or "/de/run/" in rel:
        return True
    return rel.endswith(EXCLUDED_SUFFIXES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(root: Path, rel: Path, stage_root: Path, copied: list[str]) -> None:
    src = root / rel
    if not src.is_file():
        return
    dst = stage_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append(rel.as_posix())


def sanitize_id(value: str) -> str:
    value = value.strip().replace("/", "-")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "release"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_tarball(stage_root: Path, package_root_name: str, archive_path: Path) -> None:
    with tarfile.open(archive_path, "w:gz") as tar:
        for path in sorted(stage_root.rglob("*")):
            tar.add(path, arcname=Path(package_root_name) / path.relative_to(stage_root))


def write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in sorted(values.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--design-name", default="vibe_soc_top")
    parser.add_argument("--module", default="chip/top")
    parser.add_argument("--test", default="chip_sw_uart_smoketest")
    parser.add_argument("--seed", default=os.environ.get("SEED", "1"))
    parser.add_argument("--channel", default="candidate", choices=("candidate", "release", "snapshot", "nightly"))
    parser.add_argument("--release-id", default=os.environ.get("GITHUB_REF_NAME", "local"))
    parser.add_argument("--include-syn", action="store_true")
    parser.add_argument("--metadata-env", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    release_id = sanitize_id(args.release_id)
    short_sha = git_sha(root)[:12]
    package_root_name = f"{args.design_name}-{args.channel}-{release_id}-{short_sha}"
    stage_root = out_dir / "_stage" / package_root_name
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage_root.mkdir(parents=True)

    copied_sources: list[str] = []
    copied_evidence: list[str] = []
    missing_evidence: list[str] = []

    for rel in tracked_files(root):
        if selected_source(rel) and not excluded(rel):
            copy_file(root, rel, stage_root, copied_sources)

    for rel_text in EVIDENCE_PATHS:
        rel = Path(rel_text)
        if (root / rel).is_file():
            copy_file(root, rel, stage_root, copied_evidence)
        else:
            missing_evidence.append(rel_text)

    sim_dir = Path(args.module) / "dv" / "sim" / args.test
    for name in (
        ".build.fingerprint",
        "compile.log",
        "elab.log",
        "sim.log",
        "dut.f",
        "dut.canonical.f",
        "uart0.log",
        "test_rom_sim_dv.logs.txt",
    ):
        rel = sim_dir / name
        if (root / rel).is_file():
            copy_file(root, rel, stage_root, copied_evidence)
        else:
            missing_evidence.append(rel.as_posix())

    if args.include_syn:
        for rel_text in SYN_PATHS:
            rel = Path(rel_text)
            if (root / rel).is_file():
                copy_file(root, rel, stage_root, copied_evidence)
            else:
                missing_evidence.append(rel_text)
        syn_dir = root / args.module / "de" / "syn"
        if syn_dir.is_dir():
            for src in sorted(syn_dir.glob("*_netlist.v")):
                copy_file(root, src.relative_to(root), stage_root, copied_evidence)

    manifest = {
        "schema": "vibe_soc.design_release.v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "design_name": args.design_name,
        "module": args.module,
        "test": args.test,
        "seed": args.seed,
        "channel": args.channel,
        "release_id": args.release_id,
        "package_root": package_root_name,
        "git": {
            "sha": git_sha(root),
            "ref": git_ref(root),
            "dirty": git_dirty(root),
        },
        "github": {
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
            "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        },
        "counts": {
            "source_files": len(copied_sources),
            "evidence_files": len(copied_evidence),
            "missing_evidence_files": len(missing_evidence),
        },
        "source_files": copied_sources,
        "evidence_files": copied_evidence,
        "missing_evidence_files": missing_evidence,
    }

    staged_manifest = stage_root / "manifest.json"
    write_json(staged_manifest, manifest)

    file_hashes: dict[str, str] = {}
    for path in sorted(stage_root.rglob("*")):
        if path.is_file():
            file_hashes[path.relative_to(stage_root).as_posix()] = sha256(path)
    manifest["file_sha256"] = file_hashes
    write_json(staged_manifest, manifest)

    manifest_path = out_dir / f"{package_root_name}.manifest.json"
    write_json(manifest_path, manifest)

    archive_path = out_dir / f"{package_root_name}.tar.gz"
    make_tarball(stage_root, package_root_name, archive_path)

    sha_path = out_dir / "SHA256SUMS"
    sha_path.write_text(
        f"{sha256(archive_path)}  {archive_path.name}\n"
        f"{sha256(manifest_path)}  {manifest_path.name}\n",
        encoding="utf-8",
    )

    if args.metadata_env:
        write_env(
            args.metadata_env,
            {
                "PACKAGE_NAME": package_root_name,
                "PACKAGE_PATH": archive_path.as_posix(),
                "MANIFEST_PATH": manifest_path.as_posix(),
                "SHA256_PATH": sha_path.as_posix(),
            },
        )

    print(f"[CD] Package:  {archive_path}")
    print(f"[CD] Manifest: {manifest_path}")
    print(f"[CD] SHA256:   {sha_path}")
    print(f"[CD] Sources:  {len(copied_sources)}")
    print(f"[CD] Evidence: {len(copied_evidence)} copied, {len(missing_evidence)} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
