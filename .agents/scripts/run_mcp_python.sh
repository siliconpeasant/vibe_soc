#!/bin/sh

# EDA setup scripts may export Python 2 paths. Keep the MCP runtime isolated.
unset PYTHONHOME PYTHONPATH PYTHONVERSION

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
cache_venv=${XDG_CACHE_HOME:-$HOME/.cache}/silicon-crew/venv/bin/python
required="mcp"

check_python() {
    candidate=$1
    [ -x "$candidate" ] || return 1
    "$candidate" -c '
import importlib.util, sys
required = sys.argv[1:]
assert sys.version_info >= (3, 10)
assert all(importlib.util.find_spec(name) is not None for name in required)
' $required >/dev/null 2>&1
}

for candidate in \
    "${SILICON_CREW_PYTHON:-}" \
    "$cache_venv" \
    "$HOME/.local/share/uv/tools/kimi-cli/bin/python" \
    "$(command -v python3 2>/dev/null || true)"
do
    if [ -n "$candidate" ] && check_python "$candidate"; then
        exec "$candidate" "$@"
    fi
done

echo "silicon-crew MCP: no Python >=3.10 with required modules: $required" >&2
echo "Run: $plugin_root/scripts/setup_mcp_env.sh" >&2
exit 127
