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
        text = replace_once(
            text,
            "| 流程编排 | `soc-pipeline` | 协调架构、doc、RTL、验证、综合、PD handoff |",
            "| 流程编排 | `vibe-soc-loop` → `soc-pipeline` | 前者分类与路由，后者协调架构、doc、RTL、验证、综合、PD handoff |",
            relative,
        )
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
        text = replace_once(
            text,
            "- 阶段 2 RTL 改动如果是 1-2 行 + 不改接口,可主 Agent 自己改;**改接口或多于 1 个模块的必须 spawn `soc-rtl-designer`**",
            "- 阶段 2 即使只有 1-2 行 RTL 改动也由 `soc-rtl-designer` stage owner 实施；主 Agent 只负责协调和状态握手",
            relative,
        )
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
        text = replace_once(
            text,
            "3. Resolve the absolute project root, module workspace, and module name. For the active top, use `chip/top` and `vibe_soc_top` unless the user specifies another module.",
            "3. Resolve the absolute project root, workspace, state module name, RTL top, and testbench top separately. For `chip/top`, the state module is `vibe_soc_top` while the current RTL top is `chip_earlgrey_asic`; never infer one from the other.",
            relative,
        )
        classification = """## Classification

Classify ownership before selecting an executor. Any generated top, wrapper, register RTL, CRG RTL, RTL/filelist, interface, or constraint change is pipeline-governed and must be owned by `soc-pipeline` plus the applicable stage role. Lower-level skills and MCP tools execute work for that owner; they do not bypass state gates.

| Task class | Owner | Executor |
|---|---|---|
| architecture, material RTL, generated RTL/top/wrapper, multi-stage recovery | `soc-pipeline` / stage role | matching generator, `soc-integrate`, or `soc-build` |
| standalone lint/compile/simulation/regression/coverage/synthesis request | applicable stage role | `soc-build` |
| read-only port extraction, snapshot, or interface diff | coordinator | `soc-integrate` |
| OpenROAD physical-design handoff | `soc-pd-engineer` | `soc-openroad` |
| loop audit, validation evidence, commit readiness | `soc-reviewer` | `check_loop_state.py` and read-only inspection |
| approved source-table conversion with no RTL output | coordinator | `excel-yml-gen`, `crg-req-to-design`, or `cr-tree-diag-gen` |

If a required owner role or executor is missing, stop with a precise blocker. Do not hand-roll generated tops, generated CRG logic, direct simulator runs, direct synthesis runs, or OpenROAD shell fallbacks.

## Loop Contract
"""
        text, count = re.subn(
            r"## Classification\n.*?## Loop Contract\n",
            classification,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1 and classification not in text:
            raise ValueError(f"{relative}: classification block not found")
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
        text = replace_once(
            text,
            "1. Read repository `AGENTS.md` and the relevant `.agents/rules` files. Always read `01_swarm_flow.md`, `02_toolchain.md`, `05_pipeline_state.md`, and `13_review_gate.md` when present.",
            "1. Read repository `AGENTS.md` and the relevant `.agents/rules` files. Always read `01_swarm_flow.md`, `02_toolchain.md`, `05_pipeline_state.md`, and `13_review_gate.md`; read `10_rtl_change_gate.md`, `11_verif_recovery_gate.md`, and `12_syn_pd_gate.md` when the focus touches them.",
            relative,
        )
        text = replace_once(
            text,
            "5. Verify that state, artifacts, check results, and claimed EDA evidence agree with real files and registered MCP execution.\n6. Report findings and exact follow-up checks. Do not modify source, state, generated artifacts, or waivers, and do not run EDA tools.",
            "5. Verify that state, artifacts, check results, and claimed EDA evidence agree with real files and registered MCP execution. Treat stale/missing logs, estimated timing, direct shell fallback, illegal roots, and missing RTL-repair invalidation as findings.\n6. Report `pass`, `needs-fix`, `needs-validation`, or `blocked` with exact follow-up checks. Do not modify source, state, generated artifacts, or waivers, and do not run EDA tools.",
            relative,
        )
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
