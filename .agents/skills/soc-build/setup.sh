#!/bin/bash
# =============================================================================
# SoC Build Skill — Setup & MCP Config Helper
# =============================================================================
# 用法:
#   ./setup.sh              安装共享 MCP runtime
# =============================================================================

set -e

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SKILL_ROOT/../.." && pwd)"
MCP_SERVER="$SKILL_ROOT/mcp_server.py"

echo "========================================"
echo "  SoC Build Skill Setup"
echo "========================================"
echo "  Plugin root:  $PLUGIN_ROOT"
echo "  MCP server:   $MCP_SERVER"
echo "========================================"
echo

# -----------------------------------------------------------------------------
# 1. 安装隔离 runtime
# -----------------------------------------------------------------------------
echo "[1/2] Installing isolated MCP runtime..."
"$PLUGIN_ROOT/scripts/setup_mcp_env.sh"

# -----------------------------------------------------------------------------
# 3. 验证 MCP Server
# -----------------------------------------------------------------------------
echo
echo "[2/2] Verifying MCP server..."
if [ ! -f "$MCP_SERVER" ]; then
    echo "[ERROR] MCP server not found: $MCP_SERVER"
    exit 1
fi

"$PLUGIN_ROOT/scripts/run_mcp_python.sh" "$MCP_SERVER" --help >/dev/null 2>&1 || {
    echo "[ERROR] MCP SDK not available. Please check installation."
    exit 1
}

echo "      MCP runtime OK"
echo "Setup complete. Plugin manifests already provide MCP configuration."
