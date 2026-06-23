#!/usr/bin/env python3
"""Initialize a single- or multi-module pipeline_state.json."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from pipeline_state import compute_next_actions, new_pipeline, now


def _atomic_write(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".pipeline_state.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def init_state_single(module_dir: str, module_name: str | None = None, force: bool = False) -> str:
    workspace = Path(module_dir).expanduser().resolve()
    module_name = module_name or workspace.name
    pipeline = new_pipeline()
    state = {
        "schema_version": 2,
        "module": module_name,
        "workspace": str(workspace),
        "mode": "single",
        "created_at": now(),
        "last_updated": now(),
        "pipeline": pipeline,
        "next_actions": compute_next_actions(pipeline),
    }
    state_path = workspace / "pipeline_state.json"
    if state_path.exists() and not force:
        raise FileExistsError(f"state already exists: {state_path}; use --force to replace it")
    _atomic_write(state_path, state)
    return str(state_path)


def init_state_multi(
    ip_dir: str,
    submodules: list[str],
    ip_name: str | None = None,
    force: bool = False,
) -> str:
    workspace = Path(ip_dir).expanduser().resolve()
    if not submodules:
        raise ValueError("multi-module mode requires at least one submodule")
    modules = {}
    for module in submodules:
        pipeline = new_pipeline()
        modules[module] = {
            "pipeline": pipeline,
            "next_actions": compute_next_actions(pipeline),
        }
    state = {
        "schema_version": 2,
        "ip": ip_name or workspace.name,
        "workspace": str(workspace),
        "mode": "multi_module",
        "created_at": now(),
        "last_updated": now(),
        "modules": modules,
    }
    state_path = workspace / "pipeline_state.json"
    if state_path.exists() and not force:
        raise FileExistsError(f"state already exists: {state_path}; use --force to replace it")
    _atomic_write(state_path, state)
    return str(state_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize pipeline state")
    parser.add_argument("target_dir")
    parser.add_argument("name", nargs="?")
    parser.add_argument("--submodules")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.submodules:
        modules = [item.strip() for item in args.submodules.split(",") if item.strip()]
        path = init_state_multi(args.target_dir, modules, args.name, args.force)
        print(f"Created multi-module pipeline_state.json: {path}")
        print(f"Submodules: {', '.join(modules)}")
    else:
        path = init_state_single(args.target_dir, args.name, args.force)
        print(f"Created pipeline_state.json: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
