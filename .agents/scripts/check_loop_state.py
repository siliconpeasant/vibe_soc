#!/usr/bin/env python3
"""Validate pipeline_state.json against real loop artifacts."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from pipeline_state import DEPENDENCIES, STAGE_ORDER, SUCCESS_STATES, compute_next_actions  # noqa: E402

ALLOWED_STATUS = {"pending", "blocked", "in_progress", "done", "fail", "skipped"}
ALLOWED_ARTIFACT_ROOTS = (
    "docs/",
    "de/rtl/",
    "de/run/",
    "de/syn/",
    "dv/tb/",
    "dv/sim/",
)
TRANSIENT_PATTERNS = (
    "*.vcd",
    "*.vpd",
    "*.fsdb",
    "*.log",
    "*.out",
    "simv*",
    "ucli.key",
    "vc_hdrs.h",
    "novas.log",
    "novas.conf",
    "novas.rc",
    "csrc/*",
    "verdiLog/*",
    "obj_dir/*",
    "work/*",
    "work.lib++/*",
    "AN.DB/*",
)
MATERIAL_PATH_PARTS = (
    "/de/rtl/",
    "/de/syn/",
)
MATERIAL_FILENAMES = {"filelist.f", "filelist.mk", "rtl.f"}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _issue(issues: list[dict], severity: str, message: str, *, stage: str | None = None) -> None:
    issues.append({"severity": severity, "stage": stage, "message": message})


def _artifact_path(workspace: Path, rel: str, issues: list[dict], stage: str) -> Path | None:
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        _issue(issues, "error", f"artifact path must be relative and stay in workspace: {rel}", stage=stage)
        return None
    if not rel.startswith(ALLOWED_ARTIFACT_ROOTS):
        _issue(issues, "error", f"artifact outside approved roots: {rel}", stage=stage)
    path = (workspace / rel).resolve()
    try:
        path.relative_to(workspace.resolve())
    except ValueError:
        _issue(issues, "error", f"artifact escapes workspace: {rel}", stage=stage)
        return None
    return path


def _check_stage(workspace: Path, stage: str, info: dict, issues: list[dict], mode: str) -> None:
    status = info.get("status")
    artifacts = info.get("artifacts") or []
    checks = info.get("check_results") or []

    if status not in ALLOWED_STATUS:
        _issue(issues, "error", f"illegal status `{status}`", stage=stage)
    if info.get("step_id") and info.get("step_id") != stage:
        _issue(issues, "error", f"step_id `{info.get('step_id')}` does not match stage", stage=stage)
    if stage != "doc" and status == "skipped":
        _issue(issues, "error", "only doc may be skipped", stage=stage)

    if status == "done":
        if not artifacts:
            _issue(issues, "error", "done stage has no artifacts", stage=stage)
        if not checks:
            _issue(issues, "error", "done stage has no check_results", stage=stage)
        for check in checks:
            if not check.get("passed"):
                _issue(issues, "error", f"done stage contains failed check `{check.get('tool')}`", stage=stage)
        if mode in {"normal", "strict"}:
            for rel in artifacts:
                path = _artifact_path(workspace, rel, issues, stage)
                if not path:
                    continue
                if not path.exists():
                    _issue(issues, "error", f"artifact missing on disk: {rel}", stage=stage)
                elif path.is_file() and path.stat().st_size == 0:
                    _issue(issues, "error", f"artifact is empty: {rel}", stage=stage)
    elif status == "fail":
        if not checks or all(check.get("passed") for check in checks):
            _issue(issues, "error", "fail stage requires at least one failed check", stage=stage)

    if mode in {"normal", "strict"} and status == "done" and stage == "verif":
        sim_logs = [rel for rel in artifacts if rel.startswith("dv/sim/") and rel.endswith(".log")]
        if not sim_logs:
            _issue(issues, "error", "verif done has no dv/sim/*.log artifact", stage=stage)
    if mode in {"normal", "strict"} and status == "done" and stage == "syn":
        syn_artifacts = [rel for rel in artifacts if rel.startswith("de/syn/")]
        if not syn_artifacts:
            _issue(issues, "error", "syn done has no de/syn artifact", stage=stage)


def _check_pipeline(workspace: Path, pipeline: dict, issues: list[dict], mode: str) -> None:
    stages = set(pipeline)
    expected = set(STAGE_ORDER)
    for extra in sorted(stages - expected):
        _issue(issues, "error", f"illegal pipeline stage `{extra}`; allowed stages are {', '.join(STAGE_ORDER)}")
    for missing in sorted(expected - stages):
        _issue(issues, "error", f"missing pipeline stage `{missing}`")
    for stage in STAGE_ORDER:
        if stage in pipeline:
            _check_stage(workspace, stage, pipeline[stage], issues, mode)
    for stage, deps in DEPENDENCIES.items():
        if stage not in pipeline:
            continue
        status = pipeline[stage].get("status")
        unsatisfied = [dep for dep in deps if pipeline.get(dep, {}).get("status") not in SUCCESS_STATES]
        if unsatisfied and status not in {"blocked", "pending"}:
            _issue(issues, "error", f"stage status `{status}` despite unsatisfied dependencies {unsatisfied}", stage=stage)
    if all(stage in pipeline for stage in STAGE_ORDER):
        expected_actions = compute_next_actions(pipeline)
        # Only warn; older states may have stale next_actions until the next update_state call.
        if expected_actions and mode == "strict":
            _issue(issues, "warning", f"next eligible actions: {expected_actions}")


def _git_status(root: Path) -> list[tuple[str, str]]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    entries: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((status, path))
    return entries


def _is_material_path(path: str, workspace_rel: str) -> bool:
    if workspace_rel and not (path == workspace_rel or path.startswith(workspace_rel + "/")):
        return False
    normalized = "/" + path
    if any(part in normalized for part in MATERIAL_PATH_PARTS):
        return True
    if Path(path).name in MATERIAL_FILENAMES:
        return True
    return False


def _check_git(workspace: Path, repo: Path, issues: list[dict], mode: str) -> dict:
    entries = _git_status(repo)
    workspace_rel = _rel(workspace, repo)
    material = [(status, path) for status, path in entries if _is_material_path(path, workspace_rel)]
    state_rel = f"{workspace_rel}/pipeline_state.json" if workspace_rel != "." else "pipeline_state.json"
    state_changed = any(path == state_rel for _, path in entries)

    if mode in {"normal", "strict"} and material and not state_changed:
        _issue(
            issues,
            "warning",
            "working tree has material RTL/synthesis changes but pipeline_state.json is not changed in this diff",
        )
    if mode == "strict":
        for _, path in entries:
            name = Path(path).name
            if any(fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path, pattern) for pattern in TRANSIENT_PATTERNS):
                _issue(issues, "error", f"transient/generated file is present in git status: {path}")
    return {"entries": entries, "material_changes": material, "state_changed": state_changed}


def check(workspace: str, mode: str = "normal") -> dict:
    workspace_path = Path(workspace).expanduser().resolve()
    repo = workspace_path
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(workspace_path),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            repo = Path(proc.stdout.strip()).resolve()
    except OSError:
        pass

    issues: list[dict] = []
    details: dict = {"workspace": str(workspace_path), "mode": mode}
    state_path = workspace_path / "pipeline_state.json"
    if not state_path.is_file():
        _issue(issues, "error", f"pipeline_state.json not found: {state_path}")
        return {"outcome": "needs-fix", "passed": False, "issues": issues, "details": details}

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _issue(issues, "error", f"invalid JSON in pipeline_state.json: {exc}")
        return {"outcome": "needs-fix", "passed": False, "issues": issues, "details": details}

    details["module"] = state.get("module") or state.get("ip")
    details["schema_version"] = state.get("schema_version")
    if state.get("schema_version") != 2:
        _issue(issues, "warning", f"unexpected schema_version: {state.get('schema_version')}")
    if str(workspace_path) != state.get("workspace"):
        _issue(issues, "warning", f"state workspace differs from resolved path: {state.get('workspace')}")

    if state.get("mode") == "multi_module":
        for module, module_state in sorted((state.get("modules") or {}).items()):
            _check_pipeline(workspace_path, module_state.get("pipeline") or {}, issues, mode)
    else:
        _check_pipeline(workspace_path, state.get("pipeline") or {}, issues, mode)

    details["git"] = _check_git(workspace_path, repo, issues, mode)

    severities = {issue["severity"] for issue in issues}
    if "error" in severities:
        outcome = "needs-fix"
    elif "warning" in severities:
        outcome = "needs-validation"
    else:
        outcome = "pass"
    return {"outcome": outcome, "passed": outcome == "pass", "issues": issues, "details": details}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pipeline_state.json and loop evidence")
    parser.add_argument("workspace")
    parser.add_argument("--mode", choices=["quick", "normal", "strict"], default="normal")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = check(args.workspace, args.mode)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"loop_state: {result['outcome']} ({args.mode})")
        for issue in result["issues"]:
            stage = f"[{issue['stage']}] " if issue.get("stage") else ""
            print(f"{issue['severity'].upper()}: {stage}{issue['message']}")
        if not result["issues"]:
            print("No loop-state issues found.")
    return 0 if result["outcome"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
