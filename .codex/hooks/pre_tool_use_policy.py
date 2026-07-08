#!/usr/bin/env python3
"""Block direct EDA shell fallbacks in silicon-crew projects.

The hook is intentionally conservative: it inspects shell command entrypoints
and lets non-shell or unrecognized hook payloads pass.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

BLOCKED_TOOLS = {
    "vcs",
    "vlogan",
    "vcs-mx",
    "xrun",
    "xcelium",
    "irun",
    "iverilog",
    "vvp",
    "verilator",
    "dc_shell",
    "dc_shell-xg-t",
    "yosys",
    "openroad",
    "verdi",
    "dve",
}
BLOCKED_MAKE_TARGETS = {
    "lint",
    "comp",
    "sim",
    "regress",
    "coverage",
    "syn",
    "verdi",
    "openroad",
}
SHELL_SEPARATORS = {";", "&&", "||", "|"}


def _load_payload() -> object:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _collect_commands(value: object) -> list[str]:
    commands: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            lower = str(key).lower()
            if lower in {"cmd", "command", "shell_command"} and isinstance(item, str):
                commands.append(item)
            else:
                commands.extend(_collect_commands(item))
    elif isinstance(value, list):
        for item in value:
            commands.extend(_collect_commands(item))
    return commands


def _split_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def _first_program(segment: list[str]) -> str:
    if not segment:
        return ""
    index = 0
    # Skip common env assignments before the command.
    while index < len(segment) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[index]):
        index += 1
    if index >= len(segment):
        return ""
    program = Path(segment[index]).name
    # Handle wrappers such as env bash -lc "vcs ..." by checking nested strings separately.
    if program == "env":
        index += 1
        while index < len(segment) and (segment[index].startswith("-") or "=" in segment[index]):
            index += 1
        program = Path(segment[index]).name if index < len(segment) else ""
    return program


def _make_target_violation(segment: list[str]) -> str | None:
    program = _first_program(segment)
    if program not in {"make", "gmake"}:
        return None
    for token in segment[1:]:
        if token.startswith("-") or "=" in token:
            continue
        if token in BLOCKED_MAKE_TARGETS:
            return token
    return None


def _violations_for_command(command: str) -> list[str]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        # Broken shell quoting should be reviewed by the normal approval path, not this hook.
        return []
    issues: list[str] = []
    for segment in _split_segments(tokens):
        program = _first_program(segment)
        if program in BLOCKED_TOOLS:
            issues.append(f"direct EDA tool `{program}` is forbidden; use the registered MCP flow")
        make_target = _make_target_violation(segment)
        if make_target:
            issues.append(f"direct `make {make_target}` is forbidden for EDA stages; use soc-build/soc-openroad MCP tools")
        # Catch shell -c wrappers with an inner command string.
        if program in {"bash", "sh", "zsh", "ksh"}:
            for idx, token in enumerate(segment):
                if token in {"-c", "-lc", "-ic"} and idx + 1 < len(segment):
                    issues.extend(_violations_for_command(segment[idx + 1]))
                    break
    return issues


def main() -> int:
    payload = _load_payload()
    commands = _collect_commands(payload)
    violations: list[str] = []
    for command in commands:
        violations.extend(_violations_for_command(command))

    if not violations:
        return 0

    message = "Blocked direct EDA shell fallback in silicon-crew repo. " + "; ".join(sorted(set(violations)))
    output = {
        "decision": "block",
        "reason": message,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
    }
    print(json.dumps(output, ensure_ascii=False))
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
