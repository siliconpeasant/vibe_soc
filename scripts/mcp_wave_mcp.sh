#!/bin/sh
# Launch the external wave-mcp runtime without the shared Python MCP wrapper.

set -eu
unset PYTHONHOME PYTHONPATH

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
if [ -n "${WAVE_MCP_BIN:-}" ] && [ -x "$WAVE_MCP_BIN" ]; then
    wave_mcp_bin=$WAVE_MCP_BIN
elif [ -x "$repo_root/.wave-mcp-venv/bin/wave-mcp" ]; then
    wave_mcp_bin=$repo_root/.wave-mcp-venv/bin/wave-mcp
elif [ -n "${HOME:-}" ] && [ -x "$HOME/.venvs/wave-mcp/bin/wave-mcp" ]; then
    wave_mcp_bin=$HOME/.venvs/wave-mcp/bin/wave-mcp
else
    echo "wave-mcp not found. Install with:" >&2
    echo "python3 -m venv ~/.venvs/wave-mcp && ~/.venvs/wave-mcp/bin/pip install 'wave-mcp==1.1.1'" >&2
    exit 1
fi

exec "$wave_mcp_bin" --transport stdio "$@"
