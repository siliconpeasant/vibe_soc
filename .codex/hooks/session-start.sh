#!/usr/bin/env bash
set -u

# Consume the hook payload before any early exit.
cat >/dev/null

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

is_soc=0
if [ -d "${repo_root}/chip" ] && [ -d "${repo_root}/ip" ]; then
    is_soc=1
elif [ -f "${repo_root}/CLAUDE.md" ] && grep -qE "silicon-crew|SoC" "${repo_root}/CLAUDE.md" 2>/dev/null; then
    is_soc=1
elif [ -d "${repo_root}/.agents/skills/soc-pipeline" ] && [ -d "${repo_root}/.agents/rules" ]; then
    is_soc=1
fi
[ "$is_soc" -eq 1 ] || exit 0

rules="${repo_root}/.agents/rules"
[ -d "$rules" ] || exit 0

# EDA environments commonly export Python 2.7 PYTHONHOME/PYTHONPATH values.
# Prefer a healthy Python 3.10+ interpreter (same strategy as pre-tool-use.sh).
unset PYTHONHOME PYTHONPATH PYTHONVERSION
export PYTHONIOENCODING=utf-8
export SILICON_CREW_RULES="$rules"

python_candidates=(
    "${SILICON_CREW_HOOK_PYTHON:-}"
    "${SILICON_CREW_MCP_VENV:+${SILICON_CREW_MCP_VENV}/bin/python}"
    "${SOC_MCP_VENV:+${SOC_MCP_VENV}/bin/python}"
    "${XDG_CACHE_HOME:-${HOME:-}/.cache}/silicon-crew/venv/bin/python"
    python3.13 python3.12 python3.11 python3.10
    /usr/local/bin/python3 /usr/bin/python3 python3
)
python_bin=""
for candidate in "${python_candidates[@]}"; do
    [ -n "${candidate}" ] || continue
    if command -v "${candidate}" >/dev/null 2>&1 && \
       "${candidate}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
        python_bin=$(command -v "${candidate}")
        break
    fi
done

if [ -z "${python_bin}" ]; then
    # Soft-fail: missing healthy Python must not break Codex session start.
    printf '%s\n' 'SessionStart hook warning: Python 3.10+ not found; skipping workflow context' >&2
    exit 0
fi

exec "${python_bin}" - <<'PYEOF'
import json
import os

rules = os.environ["SILICON_CREW_RULES"]
context = f"""# silicon-crew SoC workflow

This cwd is a silicon-crew SoC project. For RTL creation or material refactoring:

- Use the gated `doc -> rtl -> {{verif, syn}}` workflow and `pipeline_state.json`.
- Use role agents when the host supports them; otherwise use the `soc-pipeline` Skill with a generic subagent.
- Stage agents must use registered MCP tools. Verification must call `soc-build.soc_sim`; no direct `make`, `iverilog`, `vvp`, or other EDA shell fallback.
- Physical-design handoff uses `soc-openroad`; keep OpenROAD-flow-scripts/OpenROAD directories independent and store project-owned config under `pd/openroad/`.
- Use only `docs/`, `de/rtl/`, `de/syn/`, `de/run/`, `dv/tb/`, and `dv/sim/` artifact roots.
- A stage is done only when artifacts exist and every recorded check passes. Never fabricate simulation PASS or timing WNS/TNS.
- Use `soc-reviewer` for post-stage, pre-commit, or validation-evidence audit; it reports findings only and does not update `pipeline_state.json`.
- `crg-gen` is currently not registered; do not schedule CRG RTL generation until it is available.

Before acting on an RTL workflow, read the relevant full rules from `{rules}`. Pipeline dispatch requires `01_swarm_flow.md`, `02_toolchain.md`, and `05_pipeline_state.md`; review or commit-readiness work also requires `13_review_gate.md`; read coding style or exceptions only when applicable.
"""
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}, ensure_ascii=False))
PYEOF
