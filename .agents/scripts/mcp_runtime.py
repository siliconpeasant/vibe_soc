#!/usr/bin/env python3
"""Shared subprocess helpers for silicon-crew MCP servers."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, Union


PathLike = Union[str, Path]


def run_command(
    command: Sequence[str],
    *,
    cwd: Optional[PathLike] = None,
    timeout: int = 120,
) -> str:
    """Run a command and turn every process failure into an MCP tool error."""
    rendered = shlex.join(str(item) for item in command)
    try:
        result = subprocess.run(
            [str(item) for item in command],
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd is not None else None,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"command not found while running: {rendered}") from exc
    except subprocess.TimeoutExpired as exc:
        stdout = _text(exc.stdout)
        stderr = _text(exc.stderr)
        raise RuntimeError(
            _failure_message(rendered, f"timed out after {timeout}s", stdout, stderr)
        ) from exc

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if result.returncode != 0:
        raise RuntimeError(
            _failure_message(
                rendered,
                f"exited with status {result.returncode}",
                stdout,
                stderr,
            )
        )

    if stdout and stderr:
        return stdout.rstrip() + "\n[stderr]\n" + stderr.rstrip()
    return (stdout or stderr).rstrip()


def run_python(
    script: PathLike,
    *args: str,
    cwd: Optional[PathLike] = None,
    timeout: int = 120,
) -> str:
    return run_command(
        [sys.executable, str(script), *[str(arg) for arg in args]],
        cwd=cwd,
        timeout=timeout,
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _failure_message(command: str, reason: str, stdout: str, stderr: str) -> str:
    parts = [f"command {reason}: {command}"]
    if stdout:
        parts.append("[stdout]\n" + stdout.rstrip())
    if stderr:
        parts.append("[stderr]\n" + stderr.rstrip())
    return "\n".join(parts)
