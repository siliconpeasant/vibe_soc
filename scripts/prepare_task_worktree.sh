#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/prepare_task_worktree.sh <task-slug> [base-branch]

Create an isolated worktree and unique codex task branch from the latest
remote base. The current checkout may be dirty and is never modified.
Whitelisted machine-local configuration is copied into the new worktree, or
linked from a configured persistent local-config root.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    usage
    exit 2
fi

task_slug=$1
base_branch=${2:-main}
remote=${GIT_PUBLISH_REMOTE:-origin}
if [[ ! "$task_slug" =~ ^[a-z0-9]+([._-][a-z0-9]+)*$ ]]; then
    echo "Invalid task slug: use lowercase letters, digits, dots, underscores, or hyphens." >&2
    exit 2
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "Not inside a Git repository." >&2
    exit 1
}
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
git -C "$repo_root" fetch --prune "$remote" "$base_branch"
base_ref="$remote/$base_branch"
git -C "$repo_root" rev-parse --verify "$base_ref^{commit}" >/dev/null

timestamp=${GIT_PUBLISH_TIMESTAMP:-$(date -u +%Y%m%d-%H%M%S)}
worktree_root=${CODEX_WORKTREE_ROOT:-${TMPDIR:-/tmp}/vibe_soc_tasks}
mkdir -p "$worktree_root"
repo_name=$(basename "$repo_root")
worktree_path="$worktree_root/${repo_name}-${task_slug}-${timestamp}"
suffix=1
while [ -e "$worktree_path" ]; do
    worktree_path="$worktree_root/${repo_name}-${task_slug}-${timestamp}-${suffix}"
    suffix=$((suffix + 1))
done

created=0
cleanup_partial() {
    if [ "$created" = "1" ]; then
        git -C "$repo_root" worktree remove "$worktree_path" >/dev/null 2>&1 || true
    fi
}
trap cleanup_partial EXIT

git -C "$repo_root" worktree add --detach "$worktree_path" "$base_ref"
created=1
"$script_dir/sync_local_configs.sh" "$worktree_path" "$repo_root"
(
    cd "$worktree_path"
    GIT_PREPARE_SKIP_FETCH=1 \
    GIT_PUBLISH_TIMESTAMP="$timestamp" \
    GIT_PUBLISH_REMOTE="$remote" \
        "$script_dir/prepare_task_branch.sh" "$task_slug" "$base_branch"
)
branch=$(git -C "$worktree_path" branch --show-current)
created=0
trap - EXIT

cat <<EOF
WORKTREE=$worktree_path
BRANCH=$branch
Start with: cd "$worktree_path"
EOF
