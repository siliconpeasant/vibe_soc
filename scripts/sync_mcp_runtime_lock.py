#!/usr/bin/env python3
"""Normalize the generated MCP runtime to use crash-safe flock locking."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/sync_mcp_runtime.py"
OLD = '''acquire_install_lock() {
    lock_dir=$venv_dir.install.lock
    mkdir -p "$(dirname -- "$venv_dir")"
    attempts=0
    while ! mkdir "$lock_dir" 2>/dev/null; do
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 120 ]; then
            echo "silicon-crew MCP: timed out waiting for runtime lock: $lock_dir" >&2
            exit 127
        fi
        sleep 1
    done
    trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT HUP INT TERM
}

release_install_lock() {
    rmdir "$lock_dir" 2>/dev/null || true
    trap - EXIT HUP INT TERM
}
'''
NEW = '''acquire_install_lock() {
    lock_file=$venv_dir.install.lock
    mkdir -p "$(dirname -- "$venv_dir")"
    command -v flock >/dev/null 2>&1 || {
        echo "silicon-crew MCP: flock is required for runtime setup" >&2
        exit 127
    }
    exec 9>"$lock_file"
    flock -w 120 9 || {
        echo "silicon-crew MCP: timed out waiting for runtime lock: $lock_file" >&2
        exit 127
    }
}

release_install_lock() {
    flock -u 9 || true
}
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        print("[MCP-LOCK] flock contract is current")
        return 0
    if OLD not in text:
        print("[MCP-LOCK] ERROR: expected lock contract not found", file=sys.stderr)
        return 2
    if not args.write:
        print("[MCP-LOCK] OUT-OF-DATE: scripts/sync_mcp_runtime.py", file=sys.stderr)
        return 2
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("[MCP-LOCK] Wrote scripts/sync_mcp_runtime.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
