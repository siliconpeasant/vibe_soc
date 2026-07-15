#!/usr/bin/env python3
"""Check the concise silicon-crew Loop contract across canonical files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "AGENTS.md": (
        "The packet is the routing source of truth",
        "do not run both by default",
        "prepare_task_worktree.sh",
    ),
    "README.md": ("dev", "merge", "signoff", "prepare_task_worktree.sh"),
    ".agents/rules/00_loop_modes.md": ("dev", "merge", "signoff"),
    ".agents/rules/01_swarm_flow.md": ("doc -> rtl", "one stage owner"),
    ".agents/rules/02_toolchain.md": ("CDC", "`soc_sim` compiles", "Do not run both"),
    ".agents/rules/05_pipeline_state.md": ("--compact", "immutable artifact paths"),
    ".agents/rules/13_review_gate.md": (
        "Project Rule",
        "Need Human Confirmation",
        "Never state that the design is signed off",
    ),
    ".agents/skills/vibe-soc-loop/SKILL.md": (
        "fewest useful tool loops",
        "compact state",
        "one matching owner",
    ),
    ".agents/skills/soc-pipeline/SKILL.md": ("`merge`", "`signoff`", "registered checks"),
    ".agents/skills/soc-openroad/SKILL.md": ("PD handoff summary", "work_local"),
    ".agents/skills/soc-openroad/mcp_server.py": (
        'DEFAULT_LOCAL_ORFS_DIR = ""',
        "SILICON_CREW_ORFS_DIR",
    ),
    ".agents/agents/soc-pd-engineer.md": ("configured ORFS directory",),
    ".agents/agents/soc-reviewer.md": ("13_review_gate.md", "Do not write"),
}
FORBIDDEN = {
    ".agents/rules/05_pipeline_state.md": ("CLAUDE_PLUGIN_ROOT",),
}


def violations() -> list[str]:
    errors: list[str] = []
    for relative, tokens in REQUIRED.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"{relative}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(
            f"{relative}: missing required contract {token!r}"
            for token in tokens
            if token not in text
        )
    for relative, tokens in FORBIDDEN.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        errors.extend(
            f"{relative}: contains forbidden local/legacy contract {token!r}"
            for token in tokens
            if token in text
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument(
        "--write",
        action="store_true",
        help="compatibility alias; contracts are canonical and are never rewritten",
    )
    args = parser.parse_args()
    errors = violations()
    if errors:
        for error in errors:
            print(f"[LOOP-CONTRACT] ERROR: {error}", file=sys.stderr)
        return 2
    if args.write:
        print("[LOOP-CONTRACT] Canonical contracts already satisfy invariants")
    else:
        print("[LOOP-CONTRACT] Cross-file contract invariants pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
