#!/usr/bin/env python3
"""Block direct EDA shell fallbacks in silicon-crew projects.

The hook is intentionally conservative: it inspects shell command entrypoints
and lets non-shell or unrecognized hook payloads pass.
"""

from __future__ import annotations

import json
import os
import re
import select
import shlex
import sys
import time
from datetime import datetime, timezone
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
MAX_PAYLOAD_BYTES = 1024 * 1024
PAYLOAD_WAIT_SECONDS = 2.0
DIAGNOSTIC_LOG = Path(
    os.environ.get(
        "VIBE_SOC_HOOK_DIAGNOSTIC_LOG",
        Path(__file__).resolve().parent / "logs" / "pre_tool_use_policy.log",
    )
)


def _write_diagnostic(exc: BaseException) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    message = f"{timestamp} {type(exc).__name__}: {exc}\n"
    try:
        DIAGNOSTIC_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DIAGNOSTIC_LOG.open("a", encoding="utf-8") as log:
            log.write(message)
    except OSError as log_exc:
        print(f"PreToolUse diagnostic log error: {log_exc}", file=sys.stderr)


def _load_payload() -> object:
    """Read one JSON payload without requiring the hook runner to close stdin."""
    chunks: list[bytes] = []
    size = 0
    deadline = time.monotonic() + PAYLOAD_WAIT_SECONDS
    fd = sys.stdin.fileno()

    while size < MAX_PAYLOAD_BYTES:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            break
        chunk = os.read(fd, min(65536, MAX_PAYLOAD_BYTES - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)

        raw = b"".join(chunks).decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue

    raw = b"".join(chunks).decode("utf-8", errors="replace")
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
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        # Fail open on hook infrastructure errors so a broken hook cannot wedge
        # every tool call. Keep both persistent and visible diagnostics.
        _write_diagnostic(exc)
        print(f"PreToolUse policy hook error: {exc}", file=sys.stderr)
        raise SystemExit(0)
