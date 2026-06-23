#!/usr/bin/env python3
"""Apply validated, atomic transitions to pipeline_state.json."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
from pathlib import Path

from pipeline_state import (
    DEPENDENCIES,
    SUCCESS_STATES,
    compute_next_actions,
    dependencies_satisfied,
    now,
    parse_check,
    recompute_blocked,
)


ALLOWED_TRANSITIONS = {
    "pending": {"in_progress", "skipped"},
    "blocked": {"pending", "skipped"},
    "in_progress": {"done", "fail"},
    "fail": {"in_progress"},
    "done": {"in_progress"},
    "skipped": {"in_progress"},
}


def _artifact_paths(workspace: Path, artifacts: list[str]) -> list[str]:
    validated = []
    for item in artifacts:
        rel = Path(item.strip())
        if not item.strip() or rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"artifact must be a relative workspace path: {item}")
        path = (workspace / rel).resolve()
        try:
            path.relative_to(workspace)
        except ValueError as exc:
            raise ValueError(f"artifact escapes workspace: {item}") from exc
        if not path.exists():
            raise ValueError(f"artifact does not exist: {item}")
        if path.is_file() and path.stat().st_size == 0:
            raise ValueError(f"artifact is empty: {item}")
        validated.append(rel.as_posix())
    return validated


def _validate_transition(pipeline: dict, stage: str, target: str, note: str) -> None:
    current = pipeline[stage].get("status", "pending")
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid transition for {stage}: {current} -> {target}")
    if target == "in_progress" and not dependencies_satisfied(pipeline, stage):
        raise ValueError(f"dependencies not satisfied for {stage}: {list(DEPENDENCIES[stage])}")
    if target == "skipped" and not note:
        raise ValueError("skipped status requires --note with the applicable exception")
    if target == "skipped" and stage != "doc":
        raise ValueError("only the doc stage may be skipped")


def _apply_transition(
    pipeline: dict,
    workspace: Path,
    stage: str,
    status: str,
    artifacts: list[str],
    checks: list[str],
    note: str,
) -> None:
    _validate_transition(pipeline, stage, status, note)
    info = pipeline[stage]
    parsed_checks = [parse_check(item) for item in checks]

    if status == "in_progress":
        info.update(
            {
                "status": status,
                "started_at": now(),
                "completed_at": None,
                "artifacts": [],
                "check_results": [],
                "notes": note or "",
                "blocked_by": [],
            }
        )
    elif status == "done":
        if not artifacts:
            raise ValueError("done status requires --artifacts")
        validated_artifacts = _artifact_paths(workspace, artifacts)
        if not parsed_checks:
            raise ValueError("done status requires at least one --check")
        failed = [entry for entry in parsed_checks if not entry["passed"]]
        if failed:
            raise ValueError(f"done status cannot contain failed checks: {failed}")
        info.update(
            {
                "status": status,
                "completed_at": now(),
                "artifacts": validated_artifacts,
                "check_results": parsed_checks,
                "notes": note or info.get("notes", ""),
            }
        )
    elif status == "fail":
        if not parsed_checks or all(entry["passed"] for entry in parsed_checks):
            raise ValueError("fail status requires at least one failed --check")
        info.update(
            {
                "status": status,
                "completed_at": now(),
                "check_results": parsed_checks,
                "notes": note or info.get("notes", ""),
            }
        )
    elif status == "skipped":
        info.update(
            {
                "status": status,
                "completed_at": now(),
                "artifacts": [],
                "check_results": [],
                "notes": note,
                "blocked_by": [],
            }
        )
    elif status == "pending":
        info["status"] = "pending"
        info["blocked_by"] = []

    info["last_updated"] = now()
    recompute_blocked(pipeline)


def _atomic_write(path: Path, state: dict) -> None:
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


def update_state(
    module_dir: str,
    stage: str,
    status: str,
    *,
    submodule: str | None = None,
    artifacts: list[str] | None = None,
    checks: list[str] | None = None,
    note: str = "",
) -> str:
    workspace = Path(module_dir).expanduser().resolve()
    state_path = workspace / "pipeline_state.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"state file not found: {state_path}; run init_state.py first")

    lock_path = workspace / ".pipeline_state.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = json.loads(state_path.read_text())
        if state.get("mode", "single") == "multi_module":
            if not submodule:
                raise ValueError("multi-module state requires --module")
            if submodule not in state.get("modules", {}):
                raise ValueError(f"unknown submodule: {submodule}")
            module_state = state["modules"][submodule]
            pipeline = module_state["pipeline"]
            _apply_transition(
                pipeline, workspace, stage, status, artifacts or [], checks or [], note
            )
            module_state["next_actions"] = compute_next_actions(pipeline)
        else:
            pipeline = state["pipeline"]
            _apply_transition(
                pipeline, workspace, stage, status, artifacts or [], checks or [], note
            )
            state["next_actions"] = compute_next_actions(pipeline)
        state["schema_version"] = 2
        state["workspace"] = str(workspace)
        state["last_updated"] = now()
        _atomic_write(state_path, state)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return str(state_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update pipeline state")
    parser.add_argument("module_dir")
    parser.add_argument("stage", choices=["doc", "rtl", "verif", "syn"])
    parser.add_argument(
        "status",
        choices=["pending", "in_progress", "done", "fail", "blocked", "skipped"],
    )
    parser.add_argument("--module")
    parser.add_argument("--artifacts", default="")
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    if args.status == "blocked":
        parser.error("blocked is dependency-derived and cannot be set directly")
    artifacts = [item.strip() for item in args.artifacts.split(",") if item.strip()]
    path = update_state(
        args.module_dir,
        args.stage,
        args.status,
        submodule=args.module,
        artifacts=artifacts,
        checks=args.check,
        note=args.note,
    )
    suffix = f" [{args.module}]" if args.module else ""
    print(f"Updated pipeline_state.json:{suffix} {args.stage} -> {args.status}")
    print(f"State: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
