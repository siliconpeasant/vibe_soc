#!/bin/sh
# Launch a silicon-crew MCP server with a clean, mcp-capable Python.
#
# Portable across clones: no user-specific paths. Two problems this solves:
#   1. Some EDA tool envs (e.g. Arteris/FlexNoC) export PYTHONHOME/PYTHONPATH
#      pointing at a python2.7 tree, which poisons every python3 launch. We
#      strip them here (same trick as the `kimi` alias in ~/.cshrc).
#   2. The mcp package needs python>=3.10; the mcp-capable interpreter lives in
#      a dedicated venv that we auto-create on first run.
#
# Overrides (optional):
#   SOC_MCP_PYTHON   full path to an interpreter that already has `mcp`
#   SOC_MCP_VENV     venv location to create/use (default: <repo>/.soc-mcp-venv)
#
# Usage: scripts/mcp_python.sh <server_script.py> [args...]

set -e
unset PYTHONHOME PYTHONPATH

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV="${SOC_MCP_VENV:-$ROOT/.soc-mcp-venv}"

if [ -n "$SOC_MCP_PYTHON" ]; then
    PY="$SOC_MCP_PYTHON"
elif [ -x "$VENV/bin/python" ]; then
    PY="$VENV/bin/python"
else
    # Bootstrap a venv using the first python>=3.10 found on PATH.
    BASE=""
    for c in python3.13 python3.12 python3.11 python3.10 python3; do
        p=$(command -v "$c" 2>/dev/null) || continue
        if "$p" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then
            BASE="$p"; break
        fi
    done
    if [ -z "$BASE" ]; then
        echo "mcp_python.sh: no python>=3.10 on PATH; set SOC_MCP_PYTHON" >&2
        exit 1
    fi
    # All bootstrap chatter goes to stderr so stdout stays a clean JSON-RPC stream.
    echo "mcp_python.sh: creating venv at $VENV using $BASE" >&2
    "$BASE" -m venv "$VENV" >&2
    "$VENV/bin/python" -m pip install -q --upgrade pip >&2
    "$VENV/bin/python" -m pip install -q mcp >&2
    PY="$VENV/bin/python"
fi

# Self-heal: make sure mcp is importable even for a pre-existing venv/override.
if ! "$PY" -c 'import mcp' 2>/dev/null; then
    "$PY" -m pip install -q mcp >&2
fi

exec "$PY" "$@"
