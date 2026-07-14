#!/usr/bin/env python3
"""Canonical implementation for the vibe_soc gated-loop state tools.

Generated entrypoints import this module.  Keeping schema validation, state
transitions, evidence handling, review checks, and migration here prevents the
five public CLIs from acquiring subtly different contracts.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


CURRENT_SCHEMA_VERSION = 3
STAGE_ORDER = ("doc", "rtl", "verif", "syn")
DEPENDENCIES = {
    "doc": (),
    "rtl": ("doc",),
    "verif": ("rtl",),
    "syn": ("rtl",),
}
STAGE_META = {
    "doc": ("设计文档编写", "soc-doc-engineer"),
    "rtl": ("RTL设计与编码", "soc-rtl-designer"),
    "verif": ("验证环境搭建与仿真", "soc-verification-engineer"),
    "syn": ("逻辑综合与时序分析", "soc-synthesis-engineer"),
}
SUCCESS_STATES = {"done", "skipped"}
ALLOWED_STATUS = {"pending", "blocked", "in_progress", "done", "fail", "skipped"}
ALLOWED_TRANSITIONS = {
    "pending": {"in_progress", "skipped"},
    "blocked": {"pending", "skipped"},
    "in_progress": {"done", "fail", "pending"},
    "fail": {"in_progress", "pending"},
    "done": {"in_progress", "pending"},
    "skipped": {"in_progress"},
}
ALLOWED_ARTIFACT_ROOTS = (
    "docs/",
    "de/rtl/",
    "de/run/",
    "de/syn/",
    "dv/tb/",
    "dv/sim/",
)

# Each tuple is one independently required evidence class.
STAGE_REQUIRED_CHECK_GROUPS = {
    "doc": (("documentation audit", frozenset({"doc_completeness", "doc_review"})),),
    "rtl": (
        ("registered lint", frozenset({"soc_lint"})),
        ("registered compile", frozenset({"soc_comp"})),
        ("RTL/filelist audit", frozenset({"rtl_quality", "filelist_equivalence"})),
    ),
    "verif": (
        ("registered simulation", frozenset({"soc_sim"})),
        ("simulation-log audit", frozenset({"sim_log", "check_sim_pass"})),
    ),
    "syn": (
        ("registered synthesis", frozenset({"soc_syn"})),
    ),
}
LEGACY_STAGE_REQUIRED_CHECK_GROUPS = {
    **STAGE_REQUIRED_CHECK_GROUPS,
    "rtl": (
        ("registered lint/compile", frozenset({"soc_lint", "soc_comp"})),
        ("RTL/filelist audit", frozenset({"rtl_quality", "filelist_equivalence"})),
    ),
}
RTL_FINGERPRINT_SUFFIXES = {".v", ".sv", ".vh", ".svh", ".f", ".mk"}
RTL_SOURCE_SUFFIXES = {".v", ".sv", ".vh", ".svh"}
LEGACY_SCHEMA_VERSIONS = {None, 1, 2}
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
MATERIAL_PATH_PARTS = ("/de/rtl/", "/de/syn/")
MATERIAL_FILENAMES = {"filelist.f", "filelist.mk", "rtl.f"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_repo_root(workspace: Path) -> Path:
    workspace = workspace.expanduser().resolve()
    for candidate in (workspace, *workspace.parents):
        if (candidate / ".git").exists():
            return candidate
    return workspace


def portable_workspace(workspace: Path) -> str:
    workspace = workspace.expanduser().resolve()
    repo = find_repo_root(workspace)
    try:
        rel = workspace.relative_to(repo).as_posix()
    except ValueError:
        return "."
    return rel or "."


def new_pipeline() -> dict:
    pipeline = {}
    for stage in STAGE_ORDER:
        name, agent = STAGE_META[stage]
        deps = list(DEPENDENCIES[stage])
        pipeline[stage] = {
            "step_id": stage,
            "name": name,
            "agent": agent,
            "status": "pending" if not deps else "blocked",
            "blocked_by": deps,
            "started_at": None,
            "completed_at": None,
            "artifacts": [],
            "artifact_evidence": {},
            "check_results": [],
            "rtl_fingerprint": None,
            "rtl_fingerprint_source": None,
            "notes": "",
        }
    return pipeline


def dependencies_satisfied(pipeline: dict, stage: str) -> bool:
    return all(
        pipeline.get(dep, {}).get("status") in SUCCESS_STATES
        for dep in DEPENDENCIES.get(stage, ())
    )


def recompute_blocked(pipeline: dict) -> None:
    for stage in STAGE_ORDER:
        info = pipeline.get(stage)
        if not isinstance(info, dict):
            continue
        unsatisfied = [
            dep
            for dep in DEPENDENCIES[stage]
            if pipeline.get(dep, {}).get("status") not in SUCCESS_STATES
        ]
        if info.get("status") == "fail":
            info["blocked_by"] = unsatisfied
            continue
        if info.get("status") in {"done", "skipped", "in_progress"}:
            continue
        info["blocked_by"] = unsatisfied
        info["status"] = "blocked" if unsatisfied else "pending"


def compute_next_actions(pipeline: dict) -> list[dict]:
    failures = [
        stage for stage in STAGE_ORDER if pipeline.get(stage, {}).get("status") == "fail"
    ]
    if failures:
        actions = []
        for stage in failures:
            unsatisfied = [
                dep
                for dep in DEPENDENCIES[stage]
                if pipeline.get(dep, {}).get("status") not in SUCCESS_STATES
            ]
            if unsatisfied:
                actions.append(
                    {
                        "stage": unsatisfied[0],
                        "action": "repair_dependency",
                        "reason": f"{stage} failed after changing RTL; repair {unsatisfied}",
                    }
                )
            else:
                actions.append(
                    {
                        "stage": stage,
                        "action": "fix_and_retry",
                        "reason": f"{stage} failed; no new stage may start until it is retried",
                    }
                )
        return actions
    actions = []
    for stage in STAGE_ORDER:
        info = pipeline.get(stage, {})
        if info.get("status") == "pending" and dependencies_satisfied(pipeline, stage):
            actions.append(
                {
                    "stage": stage,
                    "action": f"spawn {info.get('agent', STAGE_META[stage][1])}",
                    "reason": f"dependencies {list(DEPENDENCIES[stage])} satisfied",
                }
            )
    return actions


def parse_check(value: str) -> dict:
    parts = value.split(":", 2)
    if len(parts) < 2 or not parts[0].strip():
        raise ValueError("check must use tool:passed|failed[:note]")
    result = parts[1].strip().lower()
    if result in {"passed", "pass", "true", "yes"}:
        passed = True
    elif result in {"failed", "fail", "false", "no"}:
        passed = False
    else:
        raise ValueError("check result must be passed or failed")
    return {
        "tool": parts[0].strip(),
        "passed": passed,
        "note": parts[2].strip() if len(parts) > 2 else "",
    }


def _normalized_artifact(item: str) -> str:
    raw = item.strip() if isinstance(item, str) else ""
    rel = Path(raw)
    if not raw or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"artifact must be a relative workspace path: {item}")
    normalized = rel.as_posix()
    if not normalized.startswith(ALLOWED_ARTIFACT_ROOTS):
        raise ValueError(f"artifact outside approved roots: {item}")
    return normalized


def artifact_path(workspace: Path, item: str) -> tuple[str, Path]:
    workspace = workspace.expanduser().resolve()
    rel = _normalized_artifact(item)
    path = (workspace / rel).resolve()
    try:
        path.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"artifact escapes workspace: {item}") from exc
    return rel, path


def validate_artifacts(
    workspace: Path, artifacts: list[str], *, require_existing: bool
) -> list[str]:
    validated = []
    for item in artifacts:
        rel, path = artifact_path(workspace, item)
        if require_existing and not path.exists():
            raise ValueError(f"artifact does not exist: {item}")
        if require_existing and not path.is_file():
            raise ValueError(f"artifact must be a regular file: {item}")
        if require_existing and path.stat().st_size == 0:
            raise ValueError(f"artifact is empty: {item}")
        validated.append(rel)
    return validated


def _digest_path(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    files = (
        [path]
        if path.is_file()
        else sorted(item for item in path.rglob("*") if item.is_file())
    )
    for item in files:
        rel = item.name if path.is_file() else item.relative_to(path).as_posix()
        digest.update(rel.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        data = item.read_bytes()
        digest.update(data)
        digest.update(b"\0")
        total += len(data)
    return digest.hexdigest(), total


def build_artifact_evidence(
    workspace: Path, artifacts: list[str], checks: list[dict]
) -> dict:
    evidence = {}
    provenance = sorted(
        {
            str(check.get("tool"))
            for check in checks
            if isinstance(check, dict) and check.get("passed") and check.get("tool")
        }
    )
    for item in artifacts:
        rel, path = artifact_path(workspace, item)
        if not path.exists():
            continue
        digest, size = _digest_path(path)
        evidence[rel] = {
            "sha256": digest,
            "size": size,
            "recorded_at": now(),
            "provenance": provenance,
        }
    return evidence


def is_transient_artifact(rel: str) -> bool:
    if rel.startswith(("de/run/", "dv/sim/")):
        return True
    if not rel.startswith("de/syn/"):
        return False
    path = Path(rel)
    if path.suffix.lower() in {".log", ".rpt", ".json", ".db", ".ddc"}:
        return True
    return path.name.lower().endswith(("_netlist.v", "_netlist.sv"))


def _expand_manifest_path(token: str, base: Path, repo: Path) -> Path:
    expanded = token.replace("${SOC}", str(repo)).replace("$SOC", str(repo))
    expanded = os.path.expandvars(expanded)
    path = Path(expanded).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _manifest_material(
    manifest: Path, repo: Path, seen: set[Path]
) -> set[Path]:
    manifest = manifest.resolve()
    if manifest in seen or not manifest.is_file():
        return set()
    seen.add(manifest)
    material = {manifest}
    for raw in manifest.read_text(errors="replace").splitlines():
        stripped = raw.strip().rstrip("\\").strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            continue
        index = 0
        while index < len(tokens):
            token = tokens[index]
            nested = None
            if token in {"-f", "-F"} and index + 1 < len(tokens):
                index += 1
                nested = tokens[index]
            elif token.startswith(("-f", "-F")) and len(token) > 2:
                nested = token[2:]
            if nested:
                nested_path = _expand_manifest_path(nested, manifest.parent, repo)
                material.update(_manifest_material(nested_path, repo, seen))
                index += 1
                continue
            if token.startswith(("+", "-")):
                index += 1
                continue
            candidate = _expand_manifest_path(token, manifest.parent, repo)
            suffix = candidate.suffix.lower()
            if suffix in RTL_SOURCE_SUFFIXES and candidate.is_file():
                material.add(candidate)
            elif suffix == ".f" and candidate.is_file():
                material.update(_manifest_material(candidate, repo, seen))
            index += 1
    return material


def _fingerprint_label(path: Path, repo: Path) -> str:
    try:
        return "repo/" + path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return "external/" + path.name


def compute_rtl_fingerprint(workspace: Path) -> str | None:
    """Hash the resolved compile manifest and every source it consumes."""
    workspace = workspace.expanduser().resolve()
    repo = find_repo_root(workspace)
    rtl_dir = workspace / "de" / "rtl"
    material: set[Path] = set()
    if rtl_dir.is_dir():
        material.update(
            path.resolve()
            for path in rtl_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in RTL_FINGERPRINT_SUFFIXES
        )
    seen: set[Path] = set()
    for manifest in (
        workspace / "de" / "run" / "rtl.f",
        rtl_dir / "filelist.f",
    ):
        material.update(_manifest_material(manifest, repo, seen))
    files = sorted(
        (path for path in material if path.is_file()),
        key=lambda path: _fingerprint_label(path, repo),
    )
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        digest.update(_fingerprint_label(path, repo).encode("utf-8"))
        digest.update(b"\0")
        data = path.read_bytes()
        if path.suffix.lower() in {".f", ".mk"}:
            data = data.replace(str(repo).encode(), b"$REPO")
            data = data.replace(str(workspace).encode(), b"$WORKSPACE")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def _tool_matches(tool: str, family: str) -> bool:
    return tool == family or tool.startswith(family + "_")


def missing_required_checks(
    stage: str, checks: list[dict], *, legacy_contract: bool = False
) -> list[str]:
    tools = [
        str(check.get("tool"))
        for check in checks
        if isinstance(check, dict) and check.get("passed") and check.get("tool")
    ]
    return [
        label
        for label, aliases in (
            LEGACY_STAGE_REQUIRED_CHECK_GROUPS
            if legacy_contract
            else STAGE_REQUIRED_CHECK_GROUPS
        )[stage]
        if not any(
            _tool_matches(tool, family)
            for tool in tools
            for family in aliases
        )
    ]


def stage_artifact_issues(stage: str, artifacts: list[str]) -> list[str]:
    if stage == "doc":
        return [] if any(
            rel.startswith("docs/") and Path(rel).suffix.lower() == ".md"
            for rel in artifacts
        ) else ["doc requires at least one docs/*.md artifact"]
    if stage == "rtl":
        has_filelist = any(
            rel.startswith("de/rtl/")
            and Path(rel).name in {"filelist.f", "filelist.mk"}
            for rel in artifacts
        )
        return [] if has_filelist else [
            "rtl requires de/rtl/filelist.f or de/rtl/filelist.mk"
        ]
    if stage == "verif":
        return [] if any(
            rel.startswith("dv/sim/") and rel.endswith(".log")
            for rel in artifacts
        ) else ["verif requires a dv/sim/*.log artifact"]
    if stage == "syn":
        has_output = any(
            rel.startswith("de/syn/")
            and (
                rel.endswith(("_netlist.v", "_netlist.sv"))
                or Path(rel).name in {"synth.log", "yosys.log"}
            )
            for rel in artifacts
        )
        return [] if has_output else [
            "syn requires a synthesis log or netlist artifact"
        ]
    return [f"unknown stage: {stage}"]


def stage_claim_issues(
    stage: str, artifacts: list[str], checks: list[dict]
) -> list[str]:
    """Cross-check optional claims whose evidence is not mandatory for a stage."""
    if stage != "syn":
        return []
    has_timing = any(
        rel.startswith("de/syn/")
        and rel.endswith(".rpt")
        and "timing" in Path(rel).name.lower()
        for rel in artifacts
    )
    timing_claimed = any(
        isinstance(result, dict)
        and result.get("passed")
        and any(
            _tool_matches(str(result.get("tool") or ""), family)
            for family in ("timing", "check_timing")
        )
        for result in checks
    )
    if timing_claimed and not has_timing:
        return ["timing PASS requires a real de/syn/*timing*.rpt artifact"]
    if has_timing and not timing_claimed:
        return ["a recorded timing report requires a passing timing/check_timing check"]
    return []


def _valid_evidence_record(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    sha256 = record.get("sha256")
    size = record.get("size")
    recorded_at = record.get("recorded_at")
    provenance = record.get("provenance")
    return bool(
        isinstance(sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", sha256)
        and isinstance(size, int)
        and not isinstance(size, bool)
        and size >= 0
        and isinstance(recorded_at, str)
        and recorded_at
        and isinstance(provenance, list)
        and provenance
        and all(isinstance(item, str) and item for item in provenance)
    )


def _issue(
    issues: list[dict],
    severity: str,
    message: str,
    *,
    module: str | None = None,
    stage: str | None = None,
    code: str | None = None,
) -> None:
    issue = {
        "severity": severity,
        "module": module,
        "stage": stage,
        "message": message,
    }
    if code:
        issue["code"] = code
    issues.append(issue)


def _legacy_severity(legacy: bool, info: dict) -> str:
    policy = str(info.get("evidence_policy") or "")
    if legacy or policy in {"legacy_compatible", "legacy_migrated"}:
        return "warning"
    if policy.startswith("downstream_repair"):
        return "warning"
    return "error"


def _validate_stage(
    workspace: Path,
    stage: str,
    info: object,
    issues: list[dict],
    *,
    module: str,
    legacy: bool,
    verify_filesystem: bool,
    current_fingerprint: str | None,
    allow_material_drift: bool = False,
) -> None:
    if not isinstance(info, dict):
        _issue(issues, "error", "stage entry must be an object", module=module, stage=stage)
        return
    status = info.get("status")
    if status not in ALLOWED_STATUS:
        _issue(issues, "error", f"illegal status {status!r}", module=module, stage=stage)
        return
    if info.get("step_id") not in {None, stage}:
        _issue(
            issues,
            "error",
            f"step_id {info.get('step_id')!r} does not match stage",
            module=module,
            stage=stage,
        )

    artifacts = info.get("artifacts") or []
    checks = info.get("check_results") or []
    if not isinstance(artifacts, list):
        _issue(issues, "error", "artifacts must be a list", module=module, stage=stage)
        artifacts = []
    if not isinstance(checks, list):
        _issue(issues, "error", "check_results must be a list", module=module, stage=stage)
        checks = []
    valid_checks = []
    for check_result in checks:
        malformed = (
            not isinstance(check_result, dict)
            or not check_result.get("tool")
            or not isinstance(check_result.get("passed"), bool)
        )
        if malformed:
            _issue(
                issues,
                "error",
                f"malformed check result: {check_result}",
                module=module,
                stage=stage,
            )
        else:
            valid_checks.append(check_result)

    if stage != "doc" and status == "skipped":
        _issue(issues, "error", "only doc may be skipped", module=module, stage=stage)
    if status == "skipped" and not str(info.get("notes") or "").strip():
        _issue(issues, "error", "skipped stage requires a note", module=module, stage=stage)

    evidence = info.get("artifact_evidence") or {}
    if not isinstance(evidence, dict):
        _issue(
            issues, "error", "artifact_evidence must be an object", module=module, stage=stage
        )
        evidence = {}
    normalized_artifacts = []
    for item in artifacts:
        try:
            rel, path = artifact_path(workspace, item)
        except (TypeError, ValueError) as exc:
            _issue(issues, "error", str(exc), module=module, stage=stage)
            continue
        normalized_artifacts.append(rel)
        if not verify_filesystem or status != "done":
            continue
        record = evidence.get(rel) if isinstance(evidence.get(rel), dict) else {}
        retained = _valid_evidence_record(record)
        if not path.exists():
            if is_transient_artifact(rel) and retained:
                _issue(
                    issues,
                    "warning",
                    f"transient artifact absent; retained digest/provenance needs revalidation: {rel}",
                    module=module,
                    stage=stage,
                    code="transient_evidence_only",
                )
            else:
                _issue(
                    issues,
                    "error",
                    f"artifact missing without acceptable retained evidence: {rel}",
                    module=module,
                    stage=stage,
                )
            continue
        if path.is_file() and path.stat().st_size == 0:
            _issue(issues, "error", f"artifact is empty: {rel}", module=module, stage=stage)
            continue
        if not _valid_evidence_record(record):
            _issue(
                issues,
                _legacy_severity(legacy, info),
                f"artifact has no valid digest/provenance record: {rel}",
                module=module,
                stage=stage,
            )
        elif not legacy:
            digest, _ = _digest_path(path)
            if digest != record.get("sha256"):
                _issue(
                    issues,
                    "warning" if allow_material_drift else "error",
                    f"artifact digest does not match recorded evidence: {rel}",
                    module=module,
                    stage=stage,
                    code=("downstream_rtl_repair" if allow_material_drift else None),
                )

    if status == "done":
        if not normalized_artifacts:
            _issue(issues, "error", "done stage has no artifacts", module=module, stage=stage)
        if not valid_checks:
            _issue(
                issues, "error", "done stage has no check_results", module=module, stage=stage
            )
        for check_result in valid_checks:
            if not check_result["passed"]:
                _issue(
                    issues,
                    "error",
                    f"done stage contains failed check {check_result.get('tool')!r}",
                    module=module,
                    stage=stage,
                )
        missing = missing_required_checks(stage, valid_checks)
        if missing:
            _issue(
                issues,
                _legacy_severity(legacy, info),
                f"done stage lacks required checks: {', '.join(missing)}",
                module=module,
                stage=stage,
            )
        artifact_contract = stage_artifact_issues(stage, normalized_artifacts)
        if artifact_contract:
            _issue(
                issues,
                _legacy_severity(legacy, info),
                "; ".join(artifact_contract),
                module=module,
                stage=stage,
            )
        claim_contract = stage_claim_issues(stage, normalized_artifacts, valid_checks)
        if claim_contract:
            _issue(
                issues,
                _legacy_severity(legacy, info),
                "; ".join(claim_contract),
                module=module,
                stage=stage,
            )
        if stage in {"rtl", "verif", "syn"}:
            fingerprint = info.get("rtl_fingerprint")
            if not fingerprint:
                _issue(
                    issues,
                    _legacy_severity(legacy, info),
                    "done stage has no RTL/filelist fingerprint",
                    module=module,
                    stage=stage,
                )
        if stage in {"verif", "syn"}:
            run_evidence = info.get("run_evidence")
            expected_family = "soc_sim" if stage == "verif" else "soc_syn"
            evidence_policy = str(info.get("evidence_policy") or "")
            valid_run = (
                isinstance(run_evidence, dict)
                and isinstance(run_evidence.get("run_id"), str)
                and bool(run_evidence.get("run_id"))
                and (
                    str(run_evidence.get("run_id")).startswith(expected_family + "-")
                    or evidence_policy in {"legacy_compatible", "legacy_migrated"}
                )
                and isinstance(run_evidence.get("source_fingerprint"), str)
                and run_evidence.get("source_fingerprint") == info.get("rtl_fingerprint")
                and isinstance(run_evidence.get("tool_family"), str)
                and _tool_matches(
                    run_evidence.get("tool_family"), expected_family
                )
            )
            if not valid_run:
                _issue(
                    issues,
                    _legacy_severity(legacy, info),
                    "done stage lacks valid MCP run_id/source_fingerprint evidence",
                    module=module,
                    stage=stage,
                )
            elif (
                verify_filesystem
                and current_fingerprint
                and fingerprint != current_fingerprint
            ):
                _issue(
                    issues,
                    "warning" if allow_material_drift else "error",
                    "recorded RTL/filelist fingerprint is stale",
                    module=module,
                    stage=stage,
                    code=("downstream_rtl_repair" if allow_material_drift else None),
                )
    elif status == "fail":
        if not valid_checks or all(result["passed"] for result in valid_checks):
            _issue(
                issues,
                "error",
                "fail stage requires at least one failed check",
                module=module,
                stage=stage,
            )
        if not str(info.get("notes") or "").strip():
            _issue(
                issues,
                "error",
                "fail stage requires a remediation note",
                module=module,
                stage=stage,
            )


def _validate_pipeline(
    workspace: Path,
    pipeline: object,
    issues: list[dict],
    *,
    module: str,
    legacy: bool,
    verify_filesystem: bool,
) -> None:
    if not isinstance(pipeline, dict):
        _issue(issues, "error", "pipeline must be an object", module=module)
        return
    actual = set(pipeline)
    expected = set(STAGE_ORDER)
    for extra in sorted(actual - expected):
        _issue(
            issues,
            "error",
            f"illegal pipeline stage {extra!r}; allowed stages are {', '.join(STAGE_ORDER)}",
            module=module,
        )
    for missing in sorted(expected - actual):
        _issue(
            issues, "error", f"missing pipeline stage {missing!r}", module=module, stage=missing
        )

    current_fingerprint = compute_rtl_fingerprint(workspace) if verify_filesystem else None
    downstream_repair = any(
        isinstance(pipeline.get(name), dict)
        and pipeline[name].get("status") == "in_progress"
        for name in ("verif", "syn")
    )
    for stage in STAGE_ORDER:
        if stage in pipeline:
            _validate_stage(
                workspace,
                stage,
                pipeline[stage],
                issues,
                module=module,
                legacy=legacy,
                verify_filesystem=verify_filesystem,
                current_fingerprint=current_fingerprint,
                allow_material_drift=(
                    downstream_repair
                    and stage in {"rtl", "verif", "syn"}
                    and isinstance(pipeline.get(stage), dict)
                    and pipeline[stage].get("status") == "done"
                ),
            )

    fingerprints = {
        stage: pipeline[stage].get("rtl_fingerprint")
        for stage in ("rtl", "verif", "syn")
        if isinstance(pipeline.get(stage), dict)
        and pipeline[stage].get("status") == "done"
        and pipeline[stage].get("rtl_fingerprint")
    }
    if len(set(fingerprints.values())) > 1:
        _issue(
            issues,
            "error",
            f"done-stage evidence is bound to different RTL snapshots: {fingerprints}",
            module=module,
            code="rtl_fingerprint_mismatch",
        )

    for stage, deps in DEPENDENCIES.items():
        info = pipeline.get(stage)
        if not isinstance(info, dict):
            continue
        unsatisfied = [
            dep
            for dep in deps
            if not isinstance(pipeline.get(dep), dict)
            or pipeline[dep].get("status") not in SUCCESS_STATES
        ]
        status = info.get("status")
        if unsatisfied and status not in {"blocked", "fail"}:
            _issue(
                issues,
                "error",
                f"stage status {status!r} despite unsatisfied dependencies {unsatisfied}; expected blocked",
                module=module,
                stage=stage,
            )
        if not unsatisfied and status == "blocked":
            _issue(
                issues,
                "error",
                "stage is blocked despite satisfied dependencies",
                module=module,
                stage=stage,
            )
        blocked_by = info.get("blocked_by")
        if isinstance(blocked_by, list) and sorted(blocked_by) != sorted(unsatisfied):
            _issue(
                issues,
                "warning" if legacy else "error",
                f"blocked_by is stale; expected {unsatisfied}",
                module=module,
                stage=stage,
            )


def validate_state(
    state: object,
    workspace: Path,
    *,
    verify_filesystem: bool = True,
    allow_legacy: bool = False,
) -> list[dict]:
    """Validate a complete state and return module-aware issues."""
    workspace = workspace.expanduser().resolve()
    issues: list[dict] = []
    if not isinstance(state, dict):
        _issue(issues, "error", "pipeline state root must be an object")
        return issues

    version = state.get("schema_version")
    legacy = version != CURRENT_SCHEMA_VERSION
    if legacy:
        severity = (
            "warning"
            if allow_legacy and version in LEGACY_SCHEMA_VERSIONS
            else "error"
        )
        _issue(
            issues,
            severity,
            f"schema_version {version!r} requires migration to {CURRENT_SCHEMA_VERSION}",
            code="legacy_schema",
        )

    stored_workspace = state.get("workspace")
    expected_workspace = portable_workspace(workspace)
    if not isinstance(stored_workspace, str) or not stored_workspace:
        _issue(issues, "error", "workspace must be a non-empty repo-relative path")
    else:
        stored_path = Path(stored_workspace)
        if stored_path.is_absolute():
            matches = stored_path.expanduser().resolve() == workspace
            severity = "warning" if allow_legacy and legacy and matches else "error"
            _issue(
                issues,
                severity,
                "workspace must be repo-relative and portable",
                code="absolute_workspace",
            )
        elif ".." in stored_path.parts:
            _issue(issues, "error", "workspace must not escape the repository")
        else:
            normalized = stored_path.as_posix().rstrip("/") or "."
            if normalized != expected_workspace:
                _issue(
                    issues,
                    "error",
                    f"workspace {stored_workspace!r} does not identify {expected_workspace!r}",
                )

    mode = state.get("mode", "single")
    if mode not in {"single", "multi_module"}:
        _issue(issues, "error", f"illegal mode {mode!r}")
        return issues
    if mode == "multi_module":
        modules = state.get("modules")
        if not isinstance(modules, dict) or not modules:
            _issue(issues, "error", "multi_module state requires a non-empty modules object")
            return issues
        for module, module_state in sorted(modules.items()):
            if not isinstance(module_state, dict):
                _issue(issues, "error", "module state must be an object", module=module)
                continue
            _validate_pipeline(
                workspace,
                module_state.get("pipeline"),
                issues,
                module=module,
                legacy=legacy,
                verify_filesystem=verify_filesystem,
            )
    else:
        module = str(state.get("module") or workspace.name)
        _validate_pipeline(
            workspace,
            state.get("pipeline"),
            issues,
            module=module,
            legacy=legacy,
            verify_filesystem=verify_filesystem,
        )
    return issues


def state_errors(issues: list[dict]) -> list[dict]:
    return [issue for issue in issues if issue.get("severity") == "error"]


def _format_issues(issues: list[dict]) -> str:
    lines = []
    for issue in issues:
        where = "/".join(
            part for part in (issue.get("module"), issue.get("stage")) if part
        )
        prefix = f"[{where}] " if where else ""
        lines.append(f"{prefix}{issue['message']}")
    return "; ".join(lines)


def _fill_stage_defaults(stage: str, original: object) -> dict:
    default = new_pipeline()[stage]
    if isinstance(original, dict):
        default.update(copy.deepcopy(original))
    default["step_id"] = stage
    default.setdefault("artifacts", [])
    default.setdefault("artifact_evidence", {})
    default.setdefault("check_results", [])
    default.setdefault("rtl_fingerprint", None)
    default.setdefault("rtl_fingerprint_source", None)
    default.setdefault("notes", "")
    default.setdefault("blocked_by", list(DEPENDENCIES[stage]))
    return default


def _state_containers(state: dict) -> list[tuple[str, dict]]:
    if state.get("mode") == "multi_module":
        return [
            (module, module_state)
            for module, module_state in (state.get("modules") or {}).items()
            if isinstance(module_state, dict)
        ]
    return [(str(state.get("module") or "module"), state)]


def _legacy_rtl_fingerprint(pipeline: dict) -> str | None:
    rtl = pipeline.get("rtl") if isinstance(pipeline, dict) else None
    if not isinstance(rtl, dict):
        return None
    recorded = rtl.get("rtl_fingerprint")
    if isinstance(recorded, str) and re.fullmatch(r"[0-9a-f]{64}", recorded):
        return recorded
    text = [str(rtl.get("notes") or "")]
    text.extend(
        str(result.get("note") or "")
        for result in rtl.get("check_results") or []
        if isinstance(result, dict)
    )
    for value in text:
        match = re.search(r"\bfingerprint\s*[:=]?\s*([0-9a-f]{64})\b", value, re.I)
        if match:
            return match.group(1).lower()
    return None


def normalize_legacy_state(state: dict, workspace: Path) -> tuple[dict, list[str]]:
    """Safely normalize v1/v2 state before a normal update.

    This compatibility path marks old checks as legacy and records only
    current-checkout digests/fingerprints.  It does not claim that old tools
    were re-executed.
    """
    workspace = workspace.expanduser().resolve()
    normalized = copy.deepcopy(state)
    original_version = normalized.get("schema_version")
    changes: list[str] = []
    if original_version == CURRENT_SCHEMA_VERSION:
        return normalized, changes
    if original_version not in LEGACY_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported schema_version {original_version!r}; refusing implicit downgrade"
        )

    mode = normalized.get("mode", "multi_module" if "modules" in normalized else "single")
    normalized["mode"] = mode
    normalized["schema_version"] = CURRENT_SCHEMA_VERSION
    normalized["workspace"] = portable_workspace(workspace)
    normalized.setdefault("migration", {}).update(
        {
            "normalized_from_schema": original_version if original_version is not None else 1,
            "normalization": "current-checkout snapshot; legacy checks not re-executed",
        }
    )
    changes.extend(
        [
            f"schema {original_version!r} -> {CURRENT_SCHEMA_VERSION}",
            f"workspace -> {normalized['workspace']}",
        ]
    )

    current_fingerprint = compute_rtl_fingerprint(workspace)
    for module, container in _state_containers(normalized):
        raw = container.get("pipeline") if isinstance(container.get("pipeline"), dict) else {}
        removed = sorted(set(raw) - set(STAGE_ORDER))
        if removed:
            changes.append(f"{module}: removed stages {', '.join(removed)}")
        pipeline = {stage: _fill_stage_defaults(stage, raw.get(stage)) for stage in STAGE_ORDER}
        legacy_rtl_fingerprint = _legacy_rtl_fingerprint(raw)
        for stage, info in pipeline.items():
            status = info.get("status")
            if status not in ALLOWED_STATUS:
                info["status"] = "pending"
                info["notes"] = f"Legacy illegal status {status!r} reset during normalization"
                changes.append(f"{module}/{stage}: illegal status reset")
            if info.get("status") == "fail" and not str(info.get("notes") or "").strip():
                info["notes"] = "Legacy failure normalized; remediation required before retry"
                changes.append(f"{module}/{stage}: added failure remediation note")
            if info.get("status") == "done":
                info["evidence_policy"] = "legacy_compatible"
                try:
                    info["artifact_evidence"] = build_artifact_evidence(
                        workspace,
                        info.get("artifacts") or [],
                        info.get("check_results") or [],
                    )
                except (TypeError, ValueError):
                    info["artifact_evidence"] = {}
                if stage in {"rtl", "verif", "syn"} and current_fingerprint:
                    info["rtl_fingerprint"] = (
                        legacy_rtl_fingerprint
                        if stage == "rtl" and legacy_rtl_fingerprint
                        else current_fingerprint
                    )
                    info["rtl_fingerprint_source"] = "migration_current_snapshot"
            elif (
                stage in {"verif", "syn"}
                and info.get("status") == "in_progress"
                and current_fingerprint
            ):
                info["evidence_policy"] = "legacy_compatible"
                info["rtl_fingerprint"] = current_fingerprint
                info["rtl_fingerprint_source"] = "migration_current_snapshot"
        recompute_blocked(pipeline)
        container["pipeline"] = pipeline
        container["next_actions"] = compute_next_actions(pipeline)
    if mode == "multi_module":
        normalized.pop("next_actions", None)
    else:
        normalized["next_actions"] = compute_next_actions(normalized["pipeline"])
    return normalized, changes


def _atomic_write(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=".pipeline_state.", suffix=".tmp", dir=str(path.parent)
    )
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


def init_state_single(
    module_dir: str, module_name: str | None = None, force: bool = False
) -> str:
    workspace = Path(module_dir).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    pipeline = new_pipeline()
    state = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "module": module_name or workspace.name,
        "workspace": portable_workspace(workspace),
        "mode": "single",
        "created_at": now(),
        "last_updated": now(),
        "pipeline": pipeline,
        "next_actions": compute_next_actions(pipeline),
    }
    issues = validate_state(state, workspace, verify_filesystem=False)
    if state_errors(issues):
        raise ValueError(f"generated state is invalid: {_format_issues(state_errors(issues))}")
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
    workspace.mkdir(parents=True, exist_ok=True)
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
        "schema_version": CURRENT_SCHEMA_VERSION,
        "ip": ip_name or workspace.name,
        "workspace": portable_workspace(workspace),
        "mode": "multi_module",
        "created_at": now(),
        "last_updated": now(),
        "modules": modules,
    }
    issues = validate_state(state, workspace, verify_filesystem=False)
    if state_errors(issues):
        raise ValueError(f"generated state is invalid: {_format_issues(state_errors(issues))}")
    state_path = workspace / "pipeline_state.json"
    if state_path.exists() and not force:
        raise FileExistsError(f"state already exists: {state_path}; use --force to replace it")
    _atomic_write(state_path, state)
    return str(state_path)


def init_main() -> int:
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


def _validate_transition(pipeline: dict, stage: str, target: str, note: str) -> None:
    current = pipeline[stage].get("status", "pending")
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid transition for {stage}: {current} -> {target}")
    if target == "in_progress" and not dependencies_satisfied(pipeline, stage):
        raise ValueError(f"dependencies not satisfied for {stage}: {list(DEPENDENCIES[stage])}")
    if target == "in_progress":
        other_failures = [
            name
            for name in STAGE_ORDER
            if name != stage and pipeline.get(name, {}).get("status") == "fail"
        ]
        if other_failures:
            raise ValueError(f"cannot start {stage} while failed stages require retry: {other_failures}")
    if stage == "rtl" and target == "in_progress" and current in SUCCESS_STATES and not note:
        raise ValueError("reopening rtl from a completed state requires --note")
    if target == "skipped" and not note:
        raise ValueError("skipped status requires --note with the applicable exception")
    if target == "pending" and current in {"done", "fail", "in_progress"} and not note:
        raise ValueError("pending invalidation from an active or completed stage requires --note")
    if target == "skipped" and stage != "doc":
        raise ValueError("only the doc stage may be skipped")


def _clear_stage(info: dict, status: str, note: str) -> None:
    info.update(
        {
            "status": status,
            "started_at": None,
            "completed_at": None,
            "artifacts": [],
            "artifact_evidence": {},
            "check_results": [],
            "rtl_fingerprint": None,
            "rtl_fingerprint_source": None,
            "notes": note,
            "blocked_by": [],
            "last_updated": now(),
        }
    )
    info.pop("evidence_policy", None)
    info.pop("run_evidence", None)
    info.pop("repair_owner", None)
    info.pop("repair_evidence", None)
    info.pop("previous_rtl_fingerprint", None)


def _invalidate_stage(pipeline: dict, stage: str, note: str) -> None:
    info = pipeline.get(stage)
    if isinstance(info, dict):
        _clear_stage(info, "pending", note)


def _current_snapshot(workspace: Path) -> str:
    fingerprint = compute_rtl_fingerprint(workspace)
    if not fingerprint:
        raise ValueError("no RTL/filelist material found in the resolved source manifest")
    return fingerprint


def _run_binding(
    stage: str,
    info: dict,
    workspace: Path,
    source_fingerprint: str | None,
    run_id: str | None,
    checks: list[dict],
) -> tuple[str, dict, bool]:
    current = _current_snapshot(workspace)
    legacy = info.get("evidence_policy") == "legacy_compatible"
    if not source_fingerprint and not legacy:
        raise ValueError(
            f"{stage} closure requires --source-fingerprint from the MCP run"
        )
    claimed = source_fingerprint or current
    if claimed != current:
        raise ValueError(
            f"{stage} MCP run consumed source fingerprint {claimed}, "
            f"but current source fingerprint is {current}"
        )
    if not run_id and not legacy:
        raise ValueError(f"{stage} closure requires --run-id from the MCP run")
    tool_family = "soc_sim" if stage == "verif" else "soc_syn"
    if run_id and not legacy and not run_id.startswith(tool_family + "-"):
        raise ValueError(
            f"{stage} run ID must be emitted by {tool_family} (expected {tool_family}-...)"
        )
    matching = [
        str(result.get("tool"))
        for result in checks
        if isinstance(result, dict)
        and result.get("passed")
        and _tool_matches(str(result.get("tool")), tool_family)
    ]
    evidence = {
        "run_id": run_id or "legacy-unavailable",
        "source_fingerprint": claimed,
        "tool_family": matching[0] if matching else tool_family,
        "recorded_at": now(),
    }
    return current, evidence, legacy


def _settle_downstream_repair(
    pipeline: dict,
    workspace: Path,
    stage: str,
    terminal_status: str,
    run_evidence: dict | None,
    checks: list[dict] | None = None,
) -> str:
    fingerprint = _current_snapshot(workspace)
    rtl = pipeline.get("rtl", {})
    previous = rtl.get("rtl_fingerprint")
    drift = rtl.get("status") == "done" and previous != fingerprint
    if not drift:
        return fingerprint
    if terminal_status in {"pending", "fail"}:
        reason = "aborted" if terminal_status == "pending" else "failed"
        note = f"Unsettled RTL changes from {reason} {stage}; RTL stage reopened"
        sibling = "syn" if stage == "verif" else "verif"
        _invalidate_stage(pipeline, sibling, note)
        _clear_stage(rtl, "in_progress", note)
        rtl["started_at"] = now()
        return fingerprint
    owner = rtl.get("repair_owner")
    if owner and owner != stage:
        raise ValueError(
            f"RTL repair is already owned by {owner}; reopen rtl before {stage} edits RTL"
        )
    if not run_evidence:
        raise ValueError(
            f"{stage} changed RTL and must provide MCP run source fingerprint/run ID"
        )
    repair_checks = checks or []
    missing = missing_required_checks("rtl", repair_checks)
    if missing:
        raise ValueError(
            f"{stage} changed RTL; repair closure lacks RTL checks: {', '.join(missing)}"
        )
    checker_result = _call_checker(
        "rtl", workspace, "", rtl, policy="closure"
    )
    if not checker_result.get("passed"):
        raise ValueError(
            "downstream RTL repair checker failed: "
            + "; ".join(
                checker_result.get("issues") or ["unknown RTL checker failure"]
            )
        )
    rtl_checks = [
        result
        for result in repair_checks
        if isinstance(result, dict)
        and any(
            _tool_matches(str(result.get("tool") or ""), family)
            for family in (
                "soc_lint",
                "soc_comp",
                "rtl_quality",
                "filelist_equivalence",
            )
        )
    ]
    rtl["previous_rtl_fingerprint"] = previous
    rtl["repair_owner"] = stage
    rtl["repair_evidence"] = {
        "owner": stage,
        "terminal_status": terminal_status,
        **run_evidence,
    }
    rtl["evidence_policy"] = f"downstream_repair_{terminal_status}"
    rtl["rtl_fingerprint"] = fingerprint
    rtl["rtl_fingerprint_source"] = f"{stage}_{terminal_status}_mcp_run"
    rtl["check_results"] = rtl_checks
    rtl["artifact_evidence"] = build_artifact_evidence(
        workspace, rtl.get("artifacts") or [], rtl_checks
    )
    rtl["completed_at"] = now()
    rtl["last_updated"] = now()
    sibling = "syn" if stage == "verif" else "verif"
    _invalidate_stage(
        pipeline,
        sibling,
        f"RTL changed during {stage}; {sibling} rerun required",
    )
    return fingerprint


def _apply_transition(
    pipeline: dict,
    workspace: Path,
    stage: str,
    status: str,
    artifacts: list[str],
    checks: list[str],
    note: str,
    source_fingerprint: str | None = None,
    run_id: str | None = None,
    checker_module: str = "",
) -> None:
    _validate_transition(pipeline, stage, status, note)
    info = pipeline[stage]
    current = info.get("status", "pending")
    parsed_checks = [parse_check(item) for item in checks]

    if status == "in_progress":
        _clear_stage(info, status, note or "")
        info["started_at"] = now()
        if stage in {"verif", "syn"}:
            info["rtl_fingerprint"] = _current_snapshot(workspace)
            info["rtl_fingerprint_source"] = "stage_start_snapshot"
    elif status == "done":
        if not artifacts:
            raise ValueError("done status requires --artifacts")
        validated_artifacts = validate_artifacts(
            workspace, artifacts, require_existing=True
        )
        if not parsed_checks:
            raise ValueError("done status requires at least one --check")
        failed = [entry for entry in parsed_checks if not entry["passed"]]
        if failed:
            raise ValueError(f"done status cannot contain failed checks: {failed}")
        missing = missing_required_checks(stage, parsed_checks)
        if missing:
            raise ValueError(f"done status lacks required checks: {', '.join(missing)}")
        artifact_contract = stage_artifact_issues(stage, validated_artifacts)
        if artifact_contract:
            raise ValueError("; ".join(artifact_contract))
        claim_contract = stage_claim_issues(stage, validated_artifacts, parsed_checks)
        if claim_contract:
            raise ValueError("; ".join(claim_contract))
        candidate = {
            "artifacts": validated_artifacts,
            "check_results": parsed_checks,
            "artifact_evidence": build_artifact_evidence(
                workspace, validated_artifacts, parsed_checks
            ),
        }
        checker_result = _call_checker(
            stage, workspace, checker_module, candidate, policy="closure"
        )
        if not checker_result.get("passed"):
            raise ValueError(
                f"{stage} real evidence checker failed: "
                + "; ".join(checker_result.get("issues") or ["unknown checker failure"])
            )
        fingerprint = None
        run_evidence = None
        legacy_binding = False
        if stage in {"rtl", "verif", "syn"}:
            if stage in {"verif", "syn"}:
                fingerprint, run_evidence, legacy_binding = _run_binding(
                    stage,
                    info,
                    workspace,
                    source_fingerprint,
                    run_id,
                    parsed_checks,
                )
                fingerprint = _settle_downstream_repair(
                    pipeline,
                    workspace,
                    stage,
                    status,
                    run_evidence,
                    parsed_checks,
                )
            else:
                fingerprint = _current_snapshot(workspace)
        info.update(
            {
                "status": status,
                "completed_at": now(),
                "artifacts": validated_artifacts,
                "check_results": parsed_checks,
                "artifact_evidence": build_artifact_evidence(
                    workspace, validated_artifacts, parsed_checks
                ),
                "rtl_fingerprint": fingerprint,
                "rtl_fingerprint_source": (
                    "recorded_at_transition" if fingerprint else None
                ),
                "notes": note or info.get("notes", ""),
                "blocked_by": [],
            }
        )
        if run_evidence:
            info["run_evidence"] = run_evidence
        if legacy_binding:
            info["evidence_policy"] = "legacy_compatible"
        else:
            info.pop("evidence_policy", None)
    elif status == "fail":
        if not note.strip():
            raise ValueError("fail status requires --note with remediation")
        if not parsed_checks or all(entry["passed"] for entry in parsed_checks):
            raise ValueError("fail status requires at least one failed --check")
        validated_artifacts = (
            validate_artifacts(workspace, artifacts, require_existing=True)
            if artifacts
            else []
        )
        fingerprint = info.get("rtl_fingerprint")
        run_evidence = None
        legacy_binding = False
        if stage in {"verif", "syn"}:
            if source_fingerprint or run_id:
                fingerprint, run_evidence, legacy_binding = _run_binding(
                    stage,
                    info,
                    workspace,
                    source_fingerprint,
                    run_id,
                    parsed_checks,
                )
            else:
                fingerprint = _current_snapshot(workspace)
            fingerprint = _settle_downstream_repair(
                pipeline,
                workspace,
                stage,
                status,
                run_evidence,
                parsed_checks,
            )
        info.update(
            {
                "status": status,
                "completed_at": now(),
                "artifacts": validated_artifacts,
                "artifact_evidence": build_artifact_evidence(
                    workspace, validated_artifacts, parsed_checks
                ),
                "check_results": parsed_checks,
                "notes": note,
                "rtl_fingerprint": fingerprint,
                "rtl_fingerprint_source": (
                    "failed_mcp_run" if run_evidence else info.get("rtl_fingerprint_source")
                ),
            }
        )
        if run_evidence:
            info["run_evidence"] = run_evidence
        if legacy_binding:
            info["evidence_policy"] = "legacy_compatible"
        else:
            info.pop("evidence_policy", None)
    elif status == "skipped":
        _clear_stage(info, status, note)
        info["completed_at"] = now()
    elif status == "pending":
        if stage in {"verif", "syn"}:
            _settle_downstream_repair(
                pipeline, workspace, stage, status, None
            )
        _clear_stage(info, status, note or info.get("notes", ""))

    info["last_updated"] = now()
    if stage == "rtl" and status == "in_progress" and current in SUCCESS_STATES:
        invalidation_note = note or "RTL reopened; downstream results invalidated"
        _invalidate_stage(pipeline, "verif", invalidation_note)
        _invalidate_stage(pipeline, "syn", invalidation_note)
    recompute_blocked(pipeline)


def update_state(
    module_dir: str,
    stage: str,
    status: str,
    *,
    submodule: str | None = None,
    artifacts: list[str] | None = None,
    checks: list[str] | None = None,
    note: str = "",
    source_fingerprint: str | None = None,
    run_id: str | None = None,
) -> str:
    workspace = Path(module_dir).expanduser().resolve()
    state_path = workspace / "pipeline_state.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"state file not found: {state_path}; run init_state.py first")

    lock_path = workspace / ".pipeline_state.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state, _ = normalize_legacy_state(state, workspace)
        pre_issues = validate_state(state, workspace, verify_filesystem=True)
        if state_errors(pre_issues):
            raise ValueError(
                "state is invalid before update; run migrate_state.py first: "
                + _format_issues(state_errors(pre_issues))
            )

        if state.get("mode", "single") == "multi_module":
            if not submodule:
                raise ValueError("multi-module state requires --module")
            if submodule not in state.get("modules", {}):
                raise ValueError(f"unknown submodule: {submodule}")
            module_state = state["modules"][submodule]
            pipeline = module_state["pipeline"]
            _apply_transition(
                pipeline,
                workspace,
                stage,
                status,
                artifacts or [],
                checks or [],
                note,
                source_fingerprint,
                run_id,
                submodule if stage == "doc" else "",
            )
            module_state["next_actions"] = compute_next_actions(pipeline)
        else:
            pipeline = state["pipeline"]
            _apply_transition(
                pipeline,
                workspace,
                stage,
                status,
                artifacts or [],
                checks or [],
                note,
                source_fingerprint,
                run_id,
            )
            state["next_actions"] = compute_next_actions(pipeline)

        state["schema_version"] = CURRENT_SCHEMA_VERSION
        state["workspace"] = portable_workspace(workspace)
        state["last_updated"] = now()
        post_issues = validate_state(state, workspace, verify_filesystem=True)
        if state_errors(post_issues):
            raise ValueError(
                "transition produced invalid state: "
                + _format_issues(state_errors(post_issues))
            )
        _atomic_write(state_path, state)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return str(state_path)


def update_main() -> int:
    parser = argparse.ArgumentParser(description="Update pipeline state")
    parser.add_argument("module_dir")
    parser.add_argument("stage", choices=list(STAGE_ORDER))
    parser.add_argument(
        "status",
        choices=["pending", "in_progress", "done", "fail", "blocked", "skipped"],
    )
    parser.add_argument("--module")
    parser.add_argument("--artifacts", default="")
    parser.add_argument("--check", action="append", default=[])
    parser.add_argument("--note", default="")
    parser.add_argument(
        "--source-fingerprint",
        help="source_fingerprint emitted by the successful soc_sim/soc_syn MCP run",
    )
    parser.add_argument(
        "--run-id",
        help="run_id emitted by the successful soc_sim/soc_syn MCP run",
    )
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
        source_fingerprint=args.source_fingerprint,
        run_id=args.run_id,
    )
    suffix = f" [{args.module}]" if args.module else ""
    print(f"Updated pipeline_state.json:{suffix} {args.stage} -> {args.status}")
    print(f"State: {path}")
    return 0


def _icon(status: str) -> str:
    return {
        "done": "✅",
        "skipped": "⏭️",
        "fail": "❌",
        "in_progress": "⏳",
        "blocked": "🚫",
        "pending": "⬜",
    }.get(status, "❓")


def _print_pipeline(pipeline: dict, indent: str = "  ") -> None:
    for stage in STAGE_ORDER:
        info = pipeline.get(stage, {})
        status = info.get("status", "missing")
        artifacts = info.get("artifacts") or []
        checks = info.get("check_results") or []
        passed = sum(1 for check_result in checks if check_result.get("passed"))
        art_text = f" | artifacts: {len(artifacts)}" if artifacts else ""
        check_text = f" | checks: {passed}/{len(checks)} PASS" if checks else ""
        print(f"{indent}{_icon(status)} {stage:8s} : {status:12s}{art_text}{check_text}")


def _print_stats(pipeline: dict) -> tuple[int, int, int]:
    total = len(STAGE_ORDER)
    done = sum(
        1
        for stage in STAGE_ORDER
        if pipeline.get(stage, {}).get("status") in SUCCESS_STATES
    )
    failed = sum(
        1 for stage in STAGE_ORDER if pipeline.get(stage, {}).get("status") == "fail"
    )
    return total, done, failed


def query_state(module_dir: str) -> dict:
    workspace = Path(module_dir).expanduser().resolve()
    state_path = workspace / "pipeline_state.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"State file not found: {state_path}; run init_state.py first")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    issues = validate_state(
        state, workspace, verify_filesystem=True, allow_legacy=True
    )
    errors = state_errors(issues)
    if errors:
        print(f"State Validity: INVALID ({len(errors)} errors)")
    elif issues:
        print(f"State Validity: VALID WITH WARNINGS ({len(issues)} warnings)")
    else:
        print("State Validity: VALID")
    for issue in issues:
        where = "/".join(
            part for part in (issue.get("module"), issue.get("stage")) if part
        )
        prefix = f"[{where}] " if where else ""
        print(f"  {issue['severity'].upper()}: {prefix}{issue['message']}")
    print()

    if state.get("mode") == "multi_module":
        print(f"IP Package  : {state.get('ip', workspace.name)}")
        print(f"Workspace   : {state.get('workspace')}")
        print(f"Mode        : multi_module ({len(state.get('modules', {}))} submodules)")
        print(f"Created     : {state.get('created_at', 'unknown')}")
        print(f"Last Updated: {state.get('last_updated', 'unknown')}")
        total_done = total_failed = total_steps = 0
        for module, module_state in sorted(state.get("modules", {}).items()):
            pipeline = module_state.get("pipeline", {})
            total, done, failed = _print_stats(pipeline)
            total_steps += total
            total_done += done
            total_failed += failed
            label = "done" if done == total else "fail" if failed else "active"
            print(f"\n[{label}] {module}")
            _print_pipeline(pipeline, "    ")
            for action in module_state.get("next_actions") or []:
                print(f"    → [{action['stage']}] {action['action']}")
        print(f"\nOverall Progress: {total_done}/{total_steps} done, {total_failed} failed")
    else:
        print(f"Module      : {state.get('module', workspace.name)}")
        print(f"Workspace   : {state.get('workspace')}")
        print(f"Created     : {state.get('created_at', 'unknown')}")
        print(f"Last Updated: {state.get('last_updated', 'unknown')}")
        print("\nPipeline Status:")
        _print_pipeline(state.get("pipeline", {}))
        print("\nNext Actions:")
        actions = state.get("next_actions") or []
        if not actions:
            print("  none")
        for action in actions:
            print(f"  → [{action['stage']}] {action['action']}: {action['reason']}")
        total, done, failed = _print_stats(state.get("pipeline", {}))
        print(f"\nProgress: {done}/{total} done, {failed} failed")
    return {"state": state, "issues": issues, "valid": not errors}


def query_main() -> int:
    parser = argparse.ArgumentParser(description="Query pipeline state")
    parser.add_argument("module_dir")
    args = parser.parse_args()
    try:
        result = query_state(args.module_dir)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"query_state: {exc}", file=sys.stderr)
        return 1
    return 0 if result["valid"] else 1


def _has_passed_tool(info: dict, *families: str) -> bool:
    return any(
        isinstance(result, dict)
        and result.get("passed")
        and any(
            _tool_matches(str(result.get("tool") or ""), family)
            for family in families
        )
        for result in info.get("check_results") or []
    )


def _check_recorded_docs(workspace: Path, info: dict) -> dict:
    details = {}
    issues = []
    docs = [
        rel
        for rel in info.get("artifacts") or []
        if rel.startswith("docs/") and Path(rel).suffix.lower() == ".md"
    ]
    if not docs:
        return {
            "passed": False,
            "details": details,
            "issues": ["no recorded Markdown document is available"],
        }
    for rel in docs:
        path = workspace / rel
        exists = path.is_file()
        nonempty = exists and path.stat().st_size > 0
        heading = False
        if nonempty:
            first = next(
                (
                    line.strip()
                    for line in path.read_text(errors="replace").splitlines()
                    if line.strip()
                ),
                "",
            )
            heading = first.startswith("# ")
        details[rel] = {
            "exists": exists,
            "nonempty": nonempty,
            "has_heading": heading,
        }
        if not exists:
            issues.append(f"recorded document is missing: {rel}")
        elif not nonempty:
            issues.append(f"recorded document is empty: {rel}")
        elif not heading:
            issues.append(f"recorded document must start with a Markdown heading: {rel}")
    return {"passed": not issues, "details": details, "issues": issues}


def _call_checker(
    stage: str,
    workspace: Path,
    module: str,
    info: dict,
    *,
    policy: str = "review",
) -> dict:
    if policy not in {"closure", "migration", "review"}:
        raise ValueError(f"unknown checker policy: {policy}")
    if stage == "doc":
        if _has_passed_tool(info, "doc_completeness"):
            from check_doc_completeness import check as checker

            return checker(str(workspace), module)
        return _check_recorded_docs(workspace, info)
    if stage == "rtl":
        from check_rtl_quality import check as checker

        return checker(str(workspace))
    if stage == "verif":
        from check_sim_pass import check as checker

        logs = [
            rel
            for rel in info.get("artifacts") or []
            if rel.startswith("dv/sim/") and rel.endswith(".log")
        ]
        existing = [rel for rel in logs if (workspace / rel).is_file()]
        if not existing:
            retained = info.get("artifact_evidence") or {}
            saved = any(
                isinstance(retained.get(rel), dict)
                and retained[rel].get("sha256")
                and retained[rel].get("provenance")
                for rel in logs
            )
            return {
                "passed": False,
                "unavailable_with_retained_evidence": saved,
                "issues": ["no recorded simulation log is available in this checkout"],
                "details": {"logs": logs},
            }
        return checker(str(workspace), existing)
    if stage == "syn":
        from check_timing import check as checker

        reports = [
            rel
            for rel in info.get("artifacts") or []
            if rel.startswith("de/syn/")
            and rel.endswith(".rpt")
            and "timing" in Path(rel).name.lower()
        ]
        existing = [rel for rel in reports if (workspace / rel).is_file()]
        if not reports:
            if _has_passed_tool(info, "timing", "check_timing"):
                return {
                    "passed": False,
                    "issues": ["timing PASS was recorded without a timing report"],
                    "details": {"reports": []},
                }
            return {
                "passed": True,
                "issues": [],
                "details": {"reports": [], "sta": "not recorded"},
            }
        missing = [rel for rel in reports if rel not in existing]
        if missing:
            retained = info.get("artifact_evidence") or {}
            saved = all(
                _valid_evidence_record(retained.get(rel)) for rel in missing
            )
            return {
                "passed": False,
                "unavailable_with_retained_evidence": saved,
                "issues": [
                    "recorded STA timing report is unavailable in this checkout: "
                    + ", ".join(missing)
                ],
                "details": {"reports": reports, "missing": missing},
            }
        results = [checker(str(workspace), report) for report in existing]
        issues = [
            f"{report}: {message}"
            for report, result in zip(existing, results)
            for message in result.get("issues") or []
        ]
        return {
            "passed": all(result.get("passed") for result in results),
            "issues": issues,
            "details": {
                "reports": existing,
                "results": results,
            },
        }
    raise ValueError(f"unknown stage: {stage}")


def _run_done_stage_checks(
    state: dict, workspace: Path, issues: list[dict], details: dict
) -> None:
    evidence_details = details.setdefault("evidence_checks", {})
    multi = state.get("mode") == "multi_module"
    for module, container in _state_containers(state):
        module_results = evidence_details.setdefault(module, {})
        for stage in STAGE_ORDER:
            info = (container.get("pipeline") or {}).get(stage, {})
            if info.get("status") != "done":
                continue
            checker_module = module if multi and stage == "doc" else ""
            result = _call_checker(stage, workspace, checker_module, info)
            module_results[stage] = result
            if result.get("passed"):
                continue
            severity = (
                "warning"
                if result.get("unavailable_with_retained_evidence")
                else "error"
            )
            for message in result.get("issues") or ["evidence checker failed"]:
                _issue(
                    issues,
                    severity,
                    f"{stage} evidence checker: {message}",
                    module=module,
                    stage=stage,
                    code=(
                        "retained_evidence_needs_revalidation"
                        if severity == "warning"
                        else "evidence_checker_failed"
                    ),
                )


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
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((status, path))
    return entries


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _is_material_path(path: str, workspace_rel: str) -> bool:
    if workspace_rel != "." and not (
        path == workspace_rel or path.startswith(workspace_rel + "/")
    ):
        return False
    normalized = "/" + path
    return any(part in normalized for part in MATERIAL_PATH_PARTS) or (
        Path(path).name in MATERIAL_FILENAMES
    )


def _check_git(
    workspace: Path, repo: Path, issues: list[dict], mode: str
) -> dict:
    entries = _git_status(repo)
    workspace_rel = _rel(workspace, repo)
    material = [
        (status, path)
        for status, path in entries
        if _is_material_path(path, workspace_rel)
    ]
    state_rel = (
        f"{workspace_rel}/pipeline_state.json"
        if workspace_rel != "."
        else "pipeline_state.json"
    )
    state_changed = any(path == state_rel for _, path in entries)
    if mode in {"normal", "strict"} and material and not state_changed:
        _issue(
            issues,
            "warning",
            "working tree has material RTL/synthesis changes but pipeline_state.json is unchanged",
        )
    if mode == "strict":
        for _, path in entries:
            name = Path(path).name
            if any(
                fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(path, pattern)
                for pattern in TRANSIENT_PATTERNS
            ):
                _issue(
                    issues,
                    "error",
                    f"transient/generated file is present in git status: {path}",
                )
    return {
        "entries": entries,
        "material_changes": material,
        "state_changed": state_changed,
    }


def check(workspace: str, mode: str = "normal") -> dict:
    workspace_path = Path(workspace).expanduser().resolve()
    details = {"workspace": str(workspace_path), "mode": mode}
    issues: list[dict] = []
    state_path = workspace_path / "pipeline_state.json"
    if not state_path.is_file():
        _issue(issues, "error", f"pipeline_state.json not found: {state_path}")
        return {
            "outcome": "needs-fix",
            "passed": False,
            "issues": issues,
            "details": details,
        }
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _issue(issues, "error", f"invalid JSON in pipeline_state.json: {exc}")
        return {
            "outcome": "needs-fix",
            "passed": False,
            "issues": issues,
            "details": details,
        }

    details["module"] = state.get("module") or state.get("ip")
    details["schema_version"] = state.get("schema_version")
    issues.extend(
        validate_state(
            state,
            workspace_path,
            verify_filesystem=mode in {"normal", "strict"},
            allow_legacy=True,
        )
    )
    if mode in {"normal", "strict"}:
        _run_done_stage_checks(state, workspace_path, issues, details)
    repo = find_repo_root(workspace_path)
    details["git"] = _check_git(workspace_path, repo, issues, mode)

    severities = {issue["severity"] for issue in issues}
    if "error" in severities:
        outcome = "needs-fix"
    elif "warning" in severities:
        outcome = "needs-validation"
    else:
        outcome = "pass"
    return {
        "outcome": outcome,
        "passed": outcome == "pass",
        "issues": issues,
        "details": details,
    }


def check_main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate pipeline_state.json and loop evidence"
    )
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
            where = "/".join(
                part for part in (issue.get("module"), issue.get("stage")) if part
            )
            prefix = f"[{where}] " if where else ""
            print(f"{issue['severity'].upper()}: {prefix}{issue['message']}")
        if not result["issues"]:
            print("No loop-state issues found.")
    return 0 if result["outcome"] == "pass" else 1


def _reset_for_migration(info: dict, reason: str) -> None:
    _clear_stage(
        info,
        "pending",
        f"Migration invalidated legacy evidence: {reason}",
    )


def _migration_stage_reasons(
    workspace: Path,
    module: str,
    stage: str,
    info: dict,
    *,
    multi: bool,
    legacy_contract: bool,
) -> list[str]:
    reasons = []
    if stage in {"rtl", "verif", "syn"}:
        current_fingerprint = compute_rtl_fingerprint(workspace)
        recorded_fingerprint = info.get("rtl_fingerprint")
        if (
            current_fingerprint
            and recorded_fingerprint
            and recorded_fingerprint != current_fingerprint
        ):
            reasons.append("recorded RTL/filelist fingerprint is stale")
    artifacts = info.get("artifacts") or []
    checks = info.get("check_results") or []
    if not artifacts:
        reasons.append("no artifacts recorded")
    for item in artifacts:
        try:
            _, path = artifact_path(workspace, item)
        except (TypeError, ValueError) as exc:
            reasons.append(str(exc))
            continue
        if not path.exists():
            reasons.append(f"artifact missing: {item}")
        elif not path.is_file():
            reasons.append(f"artifact is not a regular file: {item}")
        elif path.stat().st_size == 0:
            reasons.append(f"artifact empty: {item}")
    if not checks:
        reasons.append("no checks recorded")
    elif any(
        not isinstance(result, dict) or not result.get("passed") for result in checks
    ):
        reasons.append("recorded checks are malformed or failed")
    missing = missing_required_checks(
        stage, checks, legacy_contract=legacy_contract
    )
    if missing:
        reasons.append(f"required checks absent: {', '.join(missing)}")
    reasons.extend(stage_claim_issues(stage, artifacts, checks))
    if not reasons:
        checker_module = module if multi and stage == "doc" else ""
        result = _call_checker(
            stage, workspace, checker_module, info, policy="migration"
        )
        if not result.get("passed"):
            reasons.extend(result.get("issues") or ["real evidence checker failed"])
    return reasons


def migrate_state_data(
    state: dict, workspace: Path
) -> tuple[dict, list[str], list[dict]]:
    """Return a canonical v3 state; unsupported done claims are downgraded."""
    workspace = workspace.expanduser().resolve()
    original_version = state.get("schema_version")
    if original_version == CURRENT_SCHEMA_VERSION:
        migrated = copy.deepcopy(state)
        changes: list[str] = []
        migration = migrated.get("migration")
        if (
            isinstance(migration, dict)
            and migration.get("migrated_from_schema") == CURRENT_SCHEMA_VERSION
        ):
            for key in ("migrated_from_schema", "validated_at", "policy"):
                migration.pop(key, None)
            changes.append("removed self-referential schema-v3 migration metadata")
    else:
        migrated, changes = normalize_legacy_state(state, workspace)

    multi = migrated.get("mode") == "multi_module"
    for module, container in _state_containers(migrated):
        raw = container.get("pipeline") if isinstance(container.get("pipeline"), dict) else {}
        extras = sorted(set(raw) - set(STAGE_ORDER))
        if extras:
            changes.append(f"{module}: removed stages {', '.join(extras)}")
        pipeline = {stage: _fill_stage_defaults(stage, raw.get(stage)) for stage in STAGE_ORDER}
        for stage in STAGE_ORDER:
            info = pipeline[stage]
            unsatisfied = [
                dep
                for dep in DEPENDENCIES[stage]
                if pipeline.get(dep, {}).get("status") not in SUCCESS_STATES
            ]
            if info.get("status") == "done":
                reasons = (
                    [f"dependencies are not complete: {unsatisfied}"]
                    if unsatisfied
                    else _migration_stage_reasons(
                        workspace,
                        module,
                        stage,
                        info,
                        multi=multi,
                        legacy_contract=original_version != CURRENT_SCHEMA_VERSION,
                    )
                )
                if reasons:
                    _reset_for_migration(info, "; ".join(reasons))
                    changes.append(f"{module}/{stage}: done -> pending")
                elif original_version != CURRENT_SCHEMA_VERSION:
                    info["evidence_policy"] = "legacy_migrated"
                    info["artifact_evidence"] = build_artifact_evidence(
                        workspace,
                        info.get("artifacts") or [],
                        info.get("check_results") or [],
                    )
                    if stage in {"rtl", "verif", "syn"}:
                        fingerprint = compute_rtl_fingerprint(workspace)
                        info["rtl_fingerprint"] = fingerprint
                        info["rtl_fingerprint_source"] = "migration_validated_snapshot"
                        if stage in {"verif", "syn"} and fingerprint:
                            family = "soc_sim" if stage == "verif" else "soc_syn"
                            tool = next(
                                (
                                    str(result.get("tool"))
                                    for result in info.get("check_results") or []
                                    if isinstance(result, dict)
                                    and result.get("passed")
                                    and _tool_matches(
                                        str(result.get("tool") or ""), family
                                    )
                                ),
                                family,
                            )
                            info["run_evidence"] = {
                                "run_id": "legacy-migrated-unavailable",
                                "source_fingerprint": fingerprint,
                                "tool_family": tool,
                                "recorded_at": now(),
                            }
            elif unsatisfied and info.get("status") in {"in_progress", "fail"}:
                _reset_for_migration(
                    info, f"dependencies are not complete: {unsatisfied}"
                )
                changes.append(f"{module}/{stage}: active state -> pending")
            elif info.get("status") not in ALLOWED_STATUS:
                _reset_for_migration(info, f"illegal status {info.get('status')!r}")
                changes.append(f"{module}/{stage}: illegal status -> pending")
        recompute_blocked(pipeline)
        container["pipeline"] = pipeline
        container["next_actions"] = compute_next_actions(pipeline)

    migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    migrated["workspace"] = portable_workspace(workspace)
    if original_version != CURRENT_SCHEMA_VERSION:
        migrated["last_updated"] = now()
        migrated.setdefault("migration", {}).update(
            {
                "migrated_from_schema": (
                    original_version if original_version is not None else 1
                ),
                "validated_at": now(),
                "policy": "done retained only with current real evidence",
            }
        )
    elif changes:
        migrated["last_updated"] = now()
        migrated.setdefault("repair", {}).update(
            {
                "validated_at": now(),
                "policy": "invalid current evidence downgraded without rewriting valid provenance",
            }
        )
    if multi:
        migrated.pop("next_actions", None)
    else:
        migrated["next_actions"] = compute_next_actions(migrated["pipeline"])
    issues = validate_state(migrated, workspace, verify_filesystem=True)
    return migrated, changes, issues


def _active_state_stages(state: dict) -> list[str]:
    active = []
    for module, container in _state_containers(state):
        pipeline = container.get("pipeline") or {}
        active.extend(
            f"{module}/{stage}"
            for stage, info in pipeline.items()
            if isinstance(info, dict) and info.get("status") == "in_progress"
        )
    return sorted(active)


def _migration_result(
    workspace_path: Path,
    state_path: Path,
    state: dict,
    *,
    write: bool,
) -> dict:
    active = _active_state_stages(state)
    if active:
        if write:
            raise ValueError(
                "refusing to migrate state with active stages: " + ", ".join(active)
            )
        return {
            "workspace": str(workspace_path),
            "state_path": str(state_path),
            "dry_run": True,
            "written": False,
            "skipped": True,
            "skip_reason": "active stages: " + ", ".join(active),
            "changes": [],
            "issues": [],
            "state": copy.deepcopy(state),
        }
    migrated, changes, issues = migrate_state_data(state, workspace_path)
    errors = state_errors(issues)
    if errors:
        raise ValueError(
            "migration could not produce valid state: " + _format_issues(errors)
        )
    return {
        "workspace": str(workspace_path),
        "state_path": str(state_path),
        "dry_run": not write,
        "written": write,
        "skipped": False,
        "changes": changes,
        "issues": issues,
        "state": migrated,
    }


def migrate_state(workspace: str, *, write: bool = False) -> dict:
    workspace_path = Path(workspace).expanduser().resolve()
    state_path = workspace_path / "pipeline_state.json"
    if not state_path.is_file():
        raise FileNotFoundError(f"state file not found: {state_path}")
    if write:
        lock_path = workspace_path / ".pipeline_state.lock"
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            result = _migration_result(
                workspace_path, state_path, state, write=True
            )
            _atomic_write(state_path, result["state"])
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return result
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return _migration_result(workspace_path, state_path, state, write=False)


def migrate_main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate pipeline_state.json to the canonical schema"
    )
    parser.add_argument("workspace")
    parser.add_argument(
        "--write",
        action="store_true",
        help="atomically replace pipeline_state.json; default is dry-run",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = migrate_state(args.workspace, write=args.write)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("migration: written" if result["written"] else "migration: dry-run")
        if result.get("skipped"):
            print(f"  skipped: {result.get('skip_reason', 'active state')}")
        for change in result["changes"]:
            print(f"  - {change}")
        if not result["changes"]:
            print("  no structural changes")
        for issue in result["issues"]:
            print(f"  {issue['severity'].upper()}: {issue['message']}")
    return 0
