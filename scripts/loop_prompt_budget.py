#!/usr/bin/env python3
"""Measure stable Loop instruction bundles and enforce context budgets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP_POLICY = json.loads(
    (ROOT / ".agents/loop_policy.json").read_text(encoding="utf-8")
)
MODE_BUDGETS = {
    mode: LOOP_POLICY["modes"][mode]["execution"]["instruction_budget_words"]
    for mode in ("dev", "merge", "signoff")
}
FILE_BUDGETS = {
    "AGENTS.md": 450,
    ".agents/skills/vibe-soc-loop/SKILL.md": 300,
    ".agents/skills/soc-pipeline/SKILL.md": 260,
    ".agents/agents/soc-reviewer.md": 220,
}
DELIVERY_ROUTER_FILES = (
    "AGENTS.md",
    ".agents/skills/vibe-soc-loop/SKILL.md",
    ".agents/skills/soc-pipeline/SKILL.md",
    ".agents/rules/01_swarm_flow.md",
    ".agents/rules/02_toolchain.md",
    ".agents/rules/05_pipeline_state.md",
    ".agents/rules/04_coding_style.md",
    ".agents/rules/06_design_knowledge.md",
    ".agents/rules/10_rtl_change_gate.md",
    ".agents/rules/11_verif_recovery_gate.md",
    ".agents/rules/12_syn_pd_gate.md",
    ".agents/rules/13_review_gate.md",
)
BUNDLES = {
    "dev_rtl": {
        "budget": MODE_BUDGETS["dev"],
        "files": (
            "AGENTS.md",
            ".agents/skills/vibe-soc-loop/SKILL.md",
            ".agents/agents/soc-rtl-designer.md",
            ".agents/rules/10_rtl_change_gate.md",
            ".agents/rules/04_coding_style.md",
            ".agents/rules/06_design_knowledge.md",
        ),
    },
    "delivery_merge_router": {
        "budget": MODE_BUDGETS["merge"],
        "files": DELIVERY_ROUTER_FILES,
    },
    "delivery_signoff_router": {
        "budget": MODE_BUDGETS["signoff"],
        "files": DELIVERY_ROUTER_FILES,
    },
}


def word_count(relative: str) -> int:
    text = (ROOT / relative).read_text(encoding="utf-8")
    return len(re.findall(r"\S+", text))


def report() -> dict:
    files = {
        path: {
            "words": word_count(path),
            "budget": budget,
            "pass": word_count(path) <= budget,
        }
        for path, budget in FILE_BUDGETS.items()
    }
    bundles = {}
    for name, spec in BUNDLES.items():
        words = sum(word_count(path) for path in spec["files"])
        bundles[name] = {
            "words": words,
            "budget": spec["budget"],
            "pass": words <= spec["budget"],
            "files": list(spec["files"]),
        }
    return {
        "pass": all(item["pass"] for item in (*files.values(), *bundles.values())),
        "files": files,
        "bundles": bundles,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when a budget is exceeded")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for kind in ("files", "bundles"):
            for name, item in result[kind].items():
                status = "PASS" if item["pass"] else "FAIL"
                print(f"{status} {kind[:-1]} {name}: {item['words']}/{item['budget']} words")
    return 2 if args.check and not result["pass"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
