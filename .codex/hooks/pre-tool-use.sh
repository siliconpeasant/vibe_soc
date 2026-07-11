#!/usr/bin/env bash
set -u

hook_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

# EDA environments commonly export Python 2.7 PYTHONHOME/PYTHONPATH values.
# Remove them and select a Python new enough for the policy implementation.
unset PYTHONHOME PYTHONPATH PYTHONVERSION
for python in python3 /usr/local/bin/python3 /usr/bin/python3; do
    if command -v "${python}" >/dev/null 2>&1 && \
       "${python}" -c 'import sys; raise SystemExit(sys.version_info < (3, 7))' >/dev/null 2>&1; then
        exec "${python}" "${hook_dir}/pre_tool_use_policy.py"
    fi
done

printf '%s\n' 'PreToolUse policy hook error: Python 3.7 or newer is required' >&2
exit 0
