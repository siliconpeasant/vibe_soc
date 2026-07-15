#!/usr/bin/env bash
set -u

hook_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

# EDA environments commonly export Python 2.7 PYTHONHOME/PYTHONPATH values.
# Remove them and prefer the repository MCP runtime before ambient interpreters.
unset PYTHONHOME PYTHONPATH PYTHONVERSION
python_candidates=(
    "${SILICON_CREW_HOOK_PYTHON:-}"
    "${SILICON_CREW_MCP_VENV:+${SILICON_CREW_MCP_VENV}/bin/python}"
    "${SOC_MCP_VENV:+${SOC_MCP_VENV}/bin/python}"
    "${XDG_CACHE_HOME:-${HOME:-}/.cache}/silicon-crew/venv/bin/python"
    python3.13 python3.12 python3.11 python3.10 python3
    /usr/local/bin/python3 /usr/bin/python3
)
for python in "${python_candidates[@]}"; do
    [ -n "${python}" ] || continue
    if command -v "${python}" >/dev/null 2>&1 && \
       "${python}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
        exec "${python}" "${hook_dir}/pre_tool_use_policy.py"
    fi
done

printf '%s\n' 'PreToolUse policy hook error: Python 3.10 or newer is required' >&2
exit 0
