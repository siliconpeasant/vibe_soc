#!/usr/bin/env python3
"""Normalize cross-file silicon-crew loop contracts and check invariants."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "AGENTS.md",
    "README.md",
    ".agents/rules/00_loop_modes.md",
    ".agents/rules/01_swarm_flow.md",
    ".agents/rules/02_toolchain.md",
    ".agents/rules/03_exceptions.md",
    ".agents/rules/05_pipeline_state.md",
    ".agents/rules/06_design_knowledge.md",
    ".agents/rules/13_review_gate.md",
    ".agents/skills/vibe-soc-loop/SKILL.md",
    ".agents/skills/soc-pipeline/SKILL.md",
    ".agents/skills/soc-openroad/SKILL.md",
    ".agents/skills/soc-openroad/mcp_server.py",
    ".agents/agents/soc-pd-engineer.md",
    ".agents/agents/soc-reviewer.md",
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError(f"{label}: expected source text not found")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    if count:
        return updated
    if re.search(re.escape(replacement), text):
        return text
    raise ValueError(f"{label}: expected pattern not found")


def normalize(relative: str, text: str) -> str:
    if relative == "AGENTS.md":
        text = replace_once(
            text,
            "## Build, Test, and Development Commands\n\nRun from the repository root unless noted:",
            "## Build, Test, and Development Commands\n\nThe Make examples below are for human developers. Agents must use registered MCP tools for EDA stages.\n\nRun from the repository root unless noted:",
            relative,
        )
        text = replace_once(
            text,
            "Verification must use the project Make/MCP flow, not direct simulator commands. Preferred smoke check is:",
            "Human verification may use the Make flow below. Agent verification must use `soc-build.soc_sim`, never direct Make or simulator commands. Preferred human smoke check is:",
            relative,
        )
    elif relative == "README.md":
        # The mode-aware table is canonical; retain only historical migrations
        # in older branches rather than rewriting current wording.
        pass
    elif relative.endswith("01_swarm_flow.md"):
        text = replace_once(
            text,
            "- RTL/filelists: `de/rtl/`\n- constraints, synthesis and STA: `de/syn/`",
            "- RTL/filelists: `de/rtl/`\n- transient build output: `de/run/`\n- constraints, synthesis and STA: `de/syn/`",
            relative,
        )
    elif relative.endswith("02_toolchain.md"):
        text = replace_once(
            text,
            "| lint | `soc-build` | `soc_lint` |\n| compile/single simulation |",
            "| lint | `soc-build` | `soc_lint` |\n| CDC | `soc-build` | `soc_cdc` |\n| compile/single simulation |",
            relative,
        )
    elif relative.endswith("03_exceptions.md"):
        # Mode routing replaced the historical line-count exception. The rule
        # file is now canonical rather than a migration target.
        pass
    elif relative.endswith("05_pipeline_state.md"):
        text = text.replace("${CLAUDE_PLUGIN_ROOT}/scripts/", "<project_root>/.agents/scripts/")
    elif relative.endswith("06_design_knowledge.md"):
        text = replace_once(
            text,
            "All substantive development tasks must be evidence-led. Before making architecture, documentation, RTL, verification, synthesis, physical-design, integration, lint-fix, or material refactoring decisions, query the local SoC AI knowledge base with `soc-ai-kb` for relevant methodology, coding, tool, domain, or implementation guidance.",
            "All substantive development tasks must be evidence-led. When `soc-ai-kb` is registered, query it before architecture, documentation, RTL, verification, synthesis, physical-design, integration, lint-fix, or material-refactoring decisions. If it is unavailable, do not block a fresh clone solely for that reason; record the unavailable capability, local evidence used, and engineering assumptions.",
            relative,
        )
    elif relative.endswith("13_review_gate.md"):
        text = replace_once(
            text,
            "If role agents are unavailable, use a generic subagent with `.codex/agents/soc-reviewer.toml` as the role contract.",
            "If named role agents are unavailable, use a generic subagent with canonical `.agents/agents/soc-reviewer.md` as the role contract.",
            relative,
        )
    elif relative.endswith("vibe-soc-loop/SKILL.md"):
        # The mode-aware dispatcher is canonical. Keep this sync pass from
        # replacing it with the retired all-stages classification block.
        pass
    elif relative.endswith("soc-pipeline/SKILL.md"):
        text = replace_once(
            text,
            "- Canonical paths: `docs/`, `de/rtl/`, `de/syn/`, `dv/tb/`, `dv/sim/`.",
            "- Canonical artifact paths: `docs/`, `de/rtl/`, `de/run/`, `de/syn/`, `dv/tb/`, `dv/sim/`.",
            relative,
        )
    elif relative.endswith("soc-openroad/SKILL.md"):
        text = re.sub(
            r"orfs_dir=/[^`,]+/OpenROAD-flow-scripts-master/flow",
            "orfs_dir=${SILICON_CREW_ORFS_DIR}",
            text,
        )
        text = replace_once(
            text,
            "6. Call `soc_openroad_status` and record real report/result paths in `pipeline_state.json`.",
            "6. Call `soc_openroad_status` and record real report/result paths in the PD handoff summary. PD is not a `pipeline_state.json` stage.",
            relative,
        )
        text = text.replace("└── work/                 # ORFS logs/objects/reports/results; ignored by Git", "└── work_local/           # default local ORFS logs/objects/reports/results; ignored by Git")
    elif relative.endswith("soc-openroad/mcp_server.py"):
        text = re.sub(
            r'DEFAULT_LOCAL_ORFS_DIR = "[^"]*"',
            'DEFAULT_LOCAL_ORFS_DIR = ""',
            text,
            count=1,
        )
        text = replace_once(
            text,
            "def _default_orfs_dir() -> str:\n    return os.environ.get(LOCAL_ORFS_ENV, DEFAULT_LOCAL_ORFS_DIR)",
            "def _default_orfs_dir() -> str:\n    configured = os.environ.get(LOCAL_ORFS_ENV, DEFAULT_LOCAL_ORFS_DIR)\n    if not configured:\n        raise ValueError(\"local backend requires orfs_dir or SILICON_CREW_ORFS_DIR\")\n    return configured",
            relative,
        )
        text = re.sub(
            r"defaults to SILICON_CREW_ORFS_DIR or /[^ ]*/OpenROAD-flow-scripts-master/flow for backend=local",
            "defaults to SILICON_CREW_ORFS_DIR for backend=local",
            text,
        )
    elif relative.endswith("soc-pd-engineer.md"):
        text = re.sub(
            r"- `orfs_dir`: OpenROAD-flow-scripts `flow/` directory, default `[^`]+`",
            "- `orfs_dir`: OpenROAD-flow-scripts `flow/` directory; use explicit input or `SILICON_CREW_ORFS_DIR`",
            text,
            count=1,
        )
        text = text.replace(
            "and the default local ORFS directory.",
            "and the configured local ORFS directory.",
        )
    elif relative.endswith("soc-reviewer.md"):
        # The reviewer contract is canonical and generated into Codex adapters by
        # sync_agent_profiles.py. Keep this cross-contract pass idempotent.
        pass
    return text


def expected_files() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for relative in FILES:
        path = ROOT / relative
        source = path.read_text(encoding="utf-8")
        outputs[path] = normalize(relative, source)
    return outputs


def run(write: bool) -> int:
    mismatches: list[Path] = []
    for path, expected in expected_files().items():
        actual = path.read_text(encoding="utf-8")
        if actual == expected:
            continue
        mismatches.append(path)
        if write:
            path.write_text(expected, encoding="utf-8")
            print(f"[LOOP-CONTRACT] Wrote {path.relative_to(ROOT)}")
    if write:
        return 0
    if mismatches:
        for path in mismatches:
            print(f"[LOOP-CONTRACT] OUT-OF-DATE: {path.relative_to(ROOT)}", file=sys.stderr)
        print("Run: python3 scripts/sync_loop_contracts.py --write", file=sys.stderr)
        return 2
    print("[LOOP-CONTRACT] Cross-file contracts are synchronized")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        return run(args.write)
    except (OSError, ValueError) as exc:
        print(f"[LOOP-CONTRACT] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
