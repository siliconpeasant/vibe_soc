#!/bin/sh
set -eu

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
cache_root=${XDG_CACHE_HOME:-$HOME/.cache}/silicon-crew
venv_dir=$cache_root/venv

unset PYTHONHOME PYTHONPATH PYTHONVERSION
mkdir -p "$cache_root"

if command -v uv >/dev/null 2>&1; then
    UV_PROJECT_ENVIRONMENT="$venv_dir" uv sync --project "$plugin_root"
else
    python_bin=${SILICON_CREW_BOOTSTRAP_PYTHON:-python3}
    "$python_bin" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null
    "$python_bin" -m venv "$venv_dir"
    "$venv_dir/bin/python" -m pip install --upgrade pip
    "$venv_dir/bin/python" -m pip install "$plugin_root"
fi

"$venv_dir/bin/python" -c 'import mcp, openpyxl, pandas, yaml, xlrd'
printf 'silicon-crew MCP environment ready: %s\n' "$venv_dir"
