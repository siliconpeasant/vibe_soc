#!/usr/bin/env python3
"""Build a compact, risk-routed context packet for the vibe_soc loop."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from loop_state_core import (
    STAGE_ORDER,
    SUCCESS_STATES,
    compact_state_summary,
    compute_rtl_fingerprint,
    find_repo_root,
    state_errors,
    validate_state,
)


MODE_RANK = {"dev": 0, "merge": 1, "signoff": 2}
CHECK_STAGE = {
    "doc_delta": "doc",
    "architecture_doc_delta": "doc",
    "soc_lint": "rtl",
    "soc_comp": "rtl",
    "rtl_quality": "rtl",
    "soc_sim": "verif",
    "sim_log": "verif",
    "soc_syn": "syn",
}
RTL_SUFFIXES = {".v", ".sv", ".vh", ".svh"}
CLOCK_RESET_RE = re.compile(r"\b(?:clk|clock|rst|reset|cdc|rdc)[A-Za-z0-9_]*\b", re.I)
PORT_DECL_RE = re.compile(r"^\s*(?:input|output|inout|parameter)\b", re.I | re.M)
MODULE_HEADER_RE = re.compile(
    r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*(?:#\s*\(.*?\)\s*)?(?:\(.*?\))?\s*;",
    re.DOTALL,
)
COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def _git(repo: Path, *args: str, check: bool = False) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def _normalize_path(value: str, repo: Path) -> str:
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix().lstrip("./")


def _default_base(repo: Path) -> str:
    configured = os.environ.get("LOOP_BASE_REF")
    if configured:
        return configured
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        remote = f"origin/{github_base}"
        if _git(repo, "rev-parse", "--verify", remote).strip():
            return remote
    if _git(repo, "rev-parse", "--verify", "origin/main").strip():
        return "origin/main"
    return "HEAD"


def collect_changed_paths(repo: Path, base_ref: str) -> list[str]:
    paths: set[str] = set()
    commands = [
        ("diff", "--name-only", f"{base_ref}...HEAD"),
        ("diff", "--name-only"),
        ("diff", "--cached", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    ]
    for command in commands:
        for raw in _git(repo, *command).splitlines():
            raw = raw.strip()
            if raw:
                paths.add(_normalize_path(raw, repo))
    return sorted(paths)


def module_workspace(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] == "chip":
        return "/".join(parts[:2])
    if len(parts) >= 3 and parts[0] == "ip":
        return "/".join(parts[:3])
    return None


def affected_stages(paths: list[str]) -> list[str]:
    stages: set[str] = set()
    for path in paths:
        wrapped = f"/{path}"
        if "/docs/" in wrapped:
            stages.add("doc")
        if "/de/rtl/" in wrapped or path.endswith("/de/run/rtl.f"):
            stages.add("rtl")
        if "/dv/" in wrapped:
            stages.add("verif")
        if "/de/syn/" in wrapped:
            stages.add("syn")
    return [stage for stage in STAGE_ORDER if stage in stages]


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _source_at(repo: Path, revision: str, path: str) -> str | None:
    completed = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _module_headers(text: str | None) -> tuple[str, ...]:
    if text is None:
        return ()
    stripped = COMMENT_RE.sub(" ", text)
    headers = []
    for match in MODULE_HEADER_RE.finditer(stripped):
        normalized = " ".join(match.group(0).split())
        headers.append(normalized)
    return tuple(headers)


def _changed_lines(repo: Path, base_ref: str, path: str) -> str:
    output = _git(repo, "diff", "--unified=0", base_ref, "--", path)
    return "\n".join(
        line[1:]
        for line in output.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )


def detect_semantic_impacts(repo: Path, base_ref: str, paths: list[str]) -> set[str]:
    impacts: set[str] = set()
    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix not in RTL_SUFFIXES:
            continue
        current_path = repo / path
        current = (
            current_path.read_text(encoding="utf-8", errors="replace")
            if current_path.is_file()
            else None
        )
        previous = _source_at(repo, base_ref, path)
        if _module_headers(previous) != _module_headers(current):
            impacts.add("interface")
        changed = _changed_lines(repo, base_ref, path)
        if PORT_DECL_RE.search(changed):
            impacts.add("interface")
        if CLOCK_RESET_RE.search(changed):
            impacts.add("clock/reset")
    return impacts


def _requested_mode(value: str | None, policy: dict) -> str:
    requested = (
        os.environ.get("LOOP_MODE")
        if value in {None, "auto"}
        else value
    ) or policy.get("default_mode", "dev")
    if requested == "auto":
        return policy.get("default_mode", "dev")
    if requested not in MODE_RANK:
        raise ValueError(f"invalid loop mode: {requested}")
    return requested


def _rule_set_fingerprint(repo: Path, rules: list[str]) -> str:
    digest = hashlib.sha256()
    for rule in rules:
        digest.update(rule.encode("utf-8"))
        digest.update(b"\0")
        path = repo / rule
        if path.is_file():
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_policy(path: Path) -> dict:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("loop policy requires schema_version 1")
    if policy.get("mode_order") != ["dev", "merge", "signoff"]:
        raise ValueError("loop policy mode_order must be dev, merge, signoff")
    modes = policy.get("modes")
    routing = policy.get("routing")
    if not isinstance(modes, dict) or any(mode not in modes for mode in MODE_RANK):
        raise ValueError("loop policy is missing a mode contract")
    required_routing = {
        "material_globs",
        "merge_globs",
        "signoff_globs",
        "signoff_impacts",
    }
    if not isinstance(routing, dict) or not required_routing.issubset(routing):
        raise ValueError("loop policy is missing routing lists")
    return policy


def route_mode(
    requested: str,
    paths: list[str],
    impacts: set[str],
    policy: dict,
) -> tuple[str, list[str], bool, list[str]]:
    routing = policy["routing"]
    detected = "dev"
    reasons: list[str] = []
    affected = sorted({item for path in paths if (item := module_workspace(path))})
    material = any(_matches(path, routing["material_globs"]) for path in paths)

    signoff_paths = [path for path in paths if _matches(path, routing["signoff_globs"])]
    merge_paths = [path for path in paths if _matches(path, routing["merge_globs"])]
    explicit_signoff = sorted(set(impacts) & set(routing["signoff_impacts"]))
    semantic_signoff = sorted(set(impacts) & {"clock/reset"})

    if len(affected) > 1:
        detected = "signoff"
        reasons.append(f"multiple module workspaces changed: {', '.join(affected)}")
    if signoff_paths:
        detected = "signoff"
        reasons.append(f"signoff-sensitive paths: {', '.join(signoff_paths[:4])}")
    if explicit_signoff or semantic_signoff:
        detected = "signoff"
        reasons.append(
            "signoff-sensitive impact: " + ", ".join(explicit_signoff + semantic_signoff)
        )
    if detected != "signoff" and merge_paths:
        detected = "merge"
        reasons.append(f"delivery-sensitive paths: {', '.join(merge_paths[:4])}")
    if not reasons:
        reasons.append(
            "single-module low-risk inner-loop change"
            if material
            else "no pipeline-governed risk detected"
        )

    selected = max((requested, detected), key=MODE_RANK.__getitem__)
    if MODE_RANK[selected] > MODE_RANK[requested]:
        reasons.append(f"automatically escalated from {requested} to {selected}")
    elif MODE_RANK[requested] > MODE_RANK[detected]:
        reasons.append(f"caller requested delivery floor {requested}")
    return selected, reasons, material, affected


def _stage_freshness(
    state: dict | None,
    workspace: Path,
    paths: list[str],
    issues: list[dict],
) -> dict[str, dict]:
    if not state or state.get("mode") == "multi_module":
        return {
            stage: {"fresh": False, "reason": "no single-module state"}
            for stage in STAGE_ORDER
        }
    pipeline = state.get("pipeline", {})
    current_fp = compute_rtl_fingerprint(workspace)
    repo = find_repo_root(workspace)
    workspace_prefix = workspace.relative_to(repo).as_posix()

    def workspace_relative(path: str) -> str | None:
        if workspace_prefix == ".":
            return path
        prefix = workspace_prefix.rstrip("/") + "/"
        return path[len(prefix):] if path.startswith(prefix) else None

    relative_paths = [item for path in paths if (item := workspace_relative(path))]
    stage_changes = {
        "doc": [path for path in relative_paths if path.startswith("docs/")],
        "rtl": [
            path
            for path in relative_paths
            if path.startswith("de/rtl/") or path == "de/run/rtl.f"
        ],
        "verif": [path for path in relative_paths if path.startswith("dv/")],
        "syn": [path for path in relative_paths if path.startswith("de/syn/")],
    }
    result = {}
    for stage in STAGE_ORDER:
        info = pipeline.get(stage, {})
        status_ok = info.get("status") in SUCCESS_STATES
        recorded_paths = set(info.get("artifacts") or []) | set(
            (info.get("artifact_evidence") or {}).keys()
        )
        unrecorded_changes = [
            path for path in stage_changes[stage] if path not in recorded_paths
        ]
        stage_errors = [
            issue
            for issue in issues
            if issue.get("severity") == "error" and issue.get("stage") == stage
        ]
        fingerprint_ok = True
        if stage in {"rtl", "verif", "syn"} and info.get("status") == "done":
            fingerprint_ok = bool(current_fp and info.get("rtl_fingerprint") == current_fp)
        fresh = status_ok and fingerprint_ok and not unrecorded_changes and not stage_errors
        if not status_ok:
            reason = f"status is {info.get('status', 'missing')}"
        elif not fingerprint_ok:
            reason = "RTL fingerprint is stale"
        elif unrecorded_changes:
            reason = "changed paths are not bound to stage evidence: " + ", ".join(
                unrecorded_changes[:3]
            )
        elif stage_errors:
            reason = "recorded stage evidence is invalid"
        else:
            reason = "recorded evidence matches the current snapshot"
        result[stage] = {"fresh": fresh, "reason": reason}
    return result


def _load_state(workspace: Path) -> tuple[dict | None, list[dict]]:
    path = workspace / "pipeline_state.json"
    if not path.is_file():
        return None, []
    state = json.loads(path.read_text(encoding="utf-8"))
    issues = validate_state(state, workspace, verify_filesystem=True, allow_legacy=True)
    return state, issues


def build_context(
    workspace: Path,
    *,
    requested_mode: str | None = None,
    base_ref: str | None = None,
    changed_paths: list[str] | None = None,
    impacts: set[str] | None = None,
    review_result: str | None = None,
    risk_checks_passed: bool = False,
    policy_path: Path | None = None,
) -> dict:
    workspace = workspace.expanduser().resolve()
    repo = find_repo_root(workspace)
    policy_path = policy_path or Path(__file__).resolve().parents[1] / "loop_policy.json"
    policy = load_policy(policy_path)
    base_ref = base_ref or _default_base(repo)
    paths = sorted(
        {
            _normalize_path(path, repo)
            for path in (changed_paths or collect_changed_paths(repo, base_ref))
        }
    )
    impacts = set(impacts or ())
    impacts.update(detect_semantic_impacts(repo, base_ref, paths))
    requested = _requested_mode(requested_mode, policy)
    mode, reasons, governed, affected = route_mode(requested, paths, impacts, policy)
    affected_stage_list = affected_stages(paths)
    state, issues = _load_state(workspace)
    freshness = _stage_freshness(state, workspace, paths, issues)
    if not governed:
        freshness = {}
    mode_policy = policy["modes"][mode]

    stage_evidence_ready = not governed
    if governed and mode in {"merge", "signoff"}:
        stage_evidence_ready = bool(
            state
            and not state_errors(issues)
            and all(item["fresh"] for item in freshness.values())
        )
    elif governed:
        stage_evidence_ready = False
    review_required = governed and mode in {"merge", "signoff"}
    risk_checks_required = governed and mode == "signoff"
    delivery_ready = bool(
        stage_evidence_ready
        and (not risk_checks_required or risk_checks_passed)
        and (not review_required or review_result == "pass")
    )

    if not governed:
        rules = []
    elif mode == "dev" and affected_stage_list == ["doc"]:
        rules = [".agents/rules/00_loop_modes.md"]
    else:
        rules = list(mode_policy["rules"])
    if any(Path(path).suffix.lower() in RTL_SUFFIXES for path in paths):
        rules.extend(
            rule
            for rule in (
                ".agents/rules/04_coding_style.md",
                ".agents/rules/06_design_knowledge.md",
            )
            if rule not in rules
        )

    if not governed:
        required_checks = ["closest_non_eda_validation"]
    elif mode == "dev" and affected_stage_list == ["doc"]:
        required_checks = ["doc_delta"]
    else:
        required_checks = mode_policy["required_checks"]
    review_mode = mode_policy["review_mode"] if governed else "not_run"
    close_pipeline = mode_policy["close_pipeline"] if governed else False
    stale = [stage for stage, info in freshness.items() if not info["fresh"]]
    reused = [stage for stage, info in freshness.items() if info["fresh"]]
    checks_to_run = []
    for check in required_checks:
        stage = CHECK_STAGE.get(check)
        if (
            mode in {"merge", "signoff"}
            and stage
            and freshness.get(stage, {}).get("fresh")
        ):
            continue
        if check.startswith("loop_review_") and review_result == "pass":
            continue
        if check == "risk_specific_checks" and risk_checks_passed:
            continue
        checks_to_run.append(check)
    actions = []
    if governed and mode == "dev" and "rtl" in affected_stage_list:
        actions = [
            "start or keep rtl in_progress",
            "run registered targeted lint, compile, and simulation",
            "defer pipeline closure, synthesis, and independent review",
        ]
    elif governed and mode == "dev" and affected_stage_list == ["doc"]:
        actions = [
            "start or keep doc in_progress",
            "run the documentation delta check",
            "defer downstream closure until merge",
        ]
    elif governed and stale:
        actions = [f"complete stale delivery stages: {', '.join(stale)}"]
    elif risk_checks_required and not risk_checks_passed:
        actions = ["run the router-selected registered risk-specific checks"]
    elif governed and review_result != "pass":
        actions = [f"run soc-reviewer {mode_policy['review_mode']} and record --review-result pass"]
    elif governed:
        actions = ["delivery evidence and review are ready; deliver the final diff"]
    else:
        actions = ["run the closest non-EDA validation for the changed files"]

    state_summary = (
        compact_state_summary(state, workspace, issues=issues) if state else {"present": False}
    )
    visible_paths = paths[:100]
    return {
        "schema_version": 1,
        "workspace": workspace.relative_to(repo).as_posix() if workspace != repo else ".",
        "base_ref": base_ref,
        "requested_mode": requested,
        "mode": mode,
        "reasons": reasons,
        "pipeline_governed": governed,
        "affected_modules": affected,
        "affected_stages": affected_stage_list,
        "changed_path_count": len(paths),
        "changed_paths": visible_paths,
        "changed_paths_truncated": len(paths) > len(visible_paths),
        "detected_impacts": sorted(impacts),
        "rules": rules,
        "rule_set_fingerprint": _rule_set_fingerprint(repo, rules),
        "required_checks": required_checks,
        "checks_to_run": checks_to_run,
        "review_mode": review_mode,
        "review_required": review_required,
        "review_result": review_result,
        "risk_checks_required": risk_checks_required,
        "risk_checks_passed": risk_checks_passed,
        "close_pipeline": close_pipeline,
        "cache": {
            "current_rtl_fingerprint": compute_rtl_fingerprint(workspace),
            "stages": freshness,
        },
        "state": state_summary,
        "stage_evidence_ready": stage_evidence_ready,
        "delivery_ready": delivery_ready,
        "reused_stages": reused,
        "next_actions": actions,
    }


def _print_text(context: dict) -> None:
    print(f"Loop mode     : {context['mode']} (requested {context['requested_mode']})")
    print(f"Workspace     : {context['workspace']}")
    print(f"Pipeline      : {'governed' if context['pipeline_governed'] else 'not governed'}")
    print(f"Delivery ready: {'yes' if context['delivery_ready'] else 'no'}")
    print("Reasons       : " + "; ".join(context["reasons"]))
    print("Rules         : " + (", ".join(context["rules"]) or "none"))
    print("Checks        : " + ", ".join(context["required_checks"]))
    print("Run now       : " + ", ".join(context["checks_to_run"]))
    cache_text = ", ".join(
        f"{stage}={'fresh' if info['fresh'] else 'stale'}"
        for stage, info in context["cache"]["stages"].items()
    )
    print("Stage cache   : " + (cache_text or "n/a"))
    for action in context["next_actions"]:
        print(f"Next          : {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--mode", choices=("auto", "dev", "merge", "signoff"), default="auto")
    parser.add_argument("--base-ref")
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="explicit repo-relative changed path; repeatable",
    )
    parser.add_argument(
        "--impact",
        action="append",
        default=[],
        help="explicit risk impact such as interface or constraints",
    )
    parser.add_argument(
        "--review-result",
        choices=("pass", "needs-fix", "needs-validation", "blocked"),
        help="result from the mapped independent delivery review",
    )
    parser.add_argument(
        "--risk-checks-passed",
        action="store_true",
        help="record that router-selected signoff checks passed",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument(
        "--write",
        action="store_true",
        help="write de/run/loop_evidence/loop_context.json",
    )
    parser.add_argument(
        "--check-ready",
        action="store_true",
        help="return 2 unless delivery evidence is ready",
    )
    args = parser.parse_args()
    try:
        context = build_context(
            args.workspace,
            requested_mode=args.mode,
            base_ref=args.base_ref,
            changed_paths=args.changed or None,
            impacts=set(args.impact),
            review_result=args.review_result,
            risk_checks_passed=args.risk_checks_passed,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"loop_context: {exc}", file=sys.stderr)
        return 1
    if args.write:
        if context["workspace"] == "." or not context["pipeline_governed"]:
            print(
                "loop_context: --write requires a pipeline-governed module workspace",
                file=sys.stderr,
            )
            return 1
        output = (
            args.workspace.expanduser().resolve()
            / "de"
            / "run"
            / "loop_evidence"
            / "loop_context.json"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.format == "text":
        _print_text(context)
    else:
        print(json.dumps(context, separators=(",", ":"), sort_keys=True))
    return 2 if args.check_ready and not context["delivery_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
