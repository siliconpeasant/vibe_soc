#!/usr/bin/env python3
"""
查询模块或 IP 包 pipeline_state.json 的当前状态。
Usage: python3 query_state.py <module_dir>
"""
import sys
import json
import os


def _icon(status: str) -> str:
    return {"done": "✅", "skipped": "⏭️", "fail": "❌", "in_progress": "⏳",
            "blocked": "🚫", "pending": "⬜"}.get(status, "❓")


def _print_pipeline(pipeline: dict, indent: str = "  "):
    for step_name, step_info in pipeline.items():
        status = step_info.get("status", "unknown")
        icon = _icon(status)
        artifacts = step_info.get("artifacts", [])
        checks = step_info.get("check_results", [])
        check_summary = ""
        if checks:
            passed = sum(1 for c in checks if c.get("passed"))
            check_summary = f" | checks: {passed}/{len(checks)} PASS"
        art_summary = f" | artifacts: {len(artifacts)}" if artifacts else ""
        print(f"{indent}{icon} {step_name:8s} : {status:12s}{art_summary}{check_summary}")


def _print_stats(pipeline: dict) -> tuple:
    total = len(pipeline)
    done = sum(1 for s in pipeline.values() if s.get("status") in {"done", "skipped"})
    fail = sum(1 for s in pipeline.values() if s.get("status") == "fail")
    return total, done, fail


def query_state(module_dir: str):
    module_dir = os.path.abspath(module_dir)
    state_path = os.path.join(module_dir, "pipeline_state.json")

    if not os.path.exists(state_path):
        print(f"State file not found: {state_path}")
        print("Run init_state.py first.")
        sys.exit(1)

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    mode = state.get("mode", "single")

    if mode == "multi_module":
        print(f"IP Package  : {state['ip']}")
        print(f"Workspace   : {state['workspace']}")
        print(f"Mode        : multi_module ({len(state['modules'])} submodules)")
        print(f"Created     : {state['created_at']}")
        print(f"Last Updated: {state['last_updated']}")
        print()

        total_done = 0
        total_fail = 0
        total_steps = 0

        for mod_name, mod_data in state["modules"].items():
            pipeline = mod_data["pipeline"]
            t, d, f = _print_stats(pipeline)
            total_done += d
            total_fail += f
            total_steps += t

            status = "✅ done" if d == t else "❌ fail" if f > 0 else "⏳ in_progress" if d > 0 else "⬜ pending"
            print(f"[{status}] {mod_name}")
            _print_pipeline(pipeline, indent="    ")

            if mod_data.get("next_actions"):
                for action in mod_data["next_actions"]:
                    print(f"    → [{action['stage']}] {action['action']}")
            print()

        print("-" * 50)
        print(f"Overall Progress: {total_done}/{total_steps} done, {total_fail} failed")

    else:
        print(f"Module      : {state['module']}")
        print(f"Workspace   : {state['workspace']}")
        print(f"Created     : {state['created_at']}")
        print(f"Last Updated: {state['last_updated']}")
        print()
        print("Pipeline Status:")
        print("-" * 50)

        _print_pipeline(state["pipeline"])

        print()
        if state.get("next_actions"):
            print("Next Actions:")
            for action in state["next_actions"]:
                print(f"  → [{action['stage']}] {action['action']}: {action['reason']}")
        else:
            print("Next Actions: none (all done or blocked by failures)")

        total, done, fail = _print_stats(state["pipeline"])
        print()
        print(f"Progress: {done}/{total} done, {fail} failed, {total - done - fail} pending/in_progress/blocked")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_state.py <module_dir>", file=sys.stderr)
        sys.exit(1)
    query_state(sys.argv[1])
