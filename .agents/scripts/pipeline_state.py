#!/usr/bin/env python3
"""Shared pipeline-state model and transition helpers."""

from __future__ import annotations

from datetime import datetime, timezone


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


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
            "check_results": [],
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
        if not info or info.get("status") in {"done", "skipped", "fail", "in_progress"}:
            continue
        unsatisfied = [
            dep
            for dep in DEPENDENCIES[stage]
            if pipeline.get(dep, {}).get("status") not in SUCCESS_STATES
        ]
        info["blocked_by"] = unsatisfied
        info["status"] = "blocked" if unsatisfied else "pending"


def compute_next_actions(pipeline: dict) -> list[dict]:
    failures = [stage for stage in STAGE_ORDER if pipeline.get(stage, {}).get("status") == "fail"]
    if failures:
        return [
            {
                "stage": stage,
                "action": "fix_and_retry",
                "reason": f"{stage} failed; no new stage may start until it is retried",
            }
            for stage in failures
        ]

    actions = []
    for stage in STAGE_ORDER:
        info = pipeline.get(stage, {})
        if info.get("status") == "pending" and dependencies_satisfied(pipeline, stage):
            actions.append(
                {
                    "stage": stage,
                    "action": f"spawn {info['agent']}",
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
