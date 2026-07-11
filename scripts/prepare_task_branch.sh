#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/prepare_task_branch.sh <task-slug> [base-branch]

Fetch the latest remote base and create a unique codex/<task>-<timestamp>
branch. Run this before making changes for a new task.
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
cd "$repo_root"

if [ -n "$(git status --porcelain --untracked-files=normal)" ]; then
    echo "Refusing to create a task branch with a dirty worktree." >&2
    echo "Commit, stash, or remove current changes first." >&2
    exit 1
fi

git fetch --prune "$remote" "$base_branch"
base_ref="$remote/$base_branch"
git rev-parse --verify "$base_ref^{commit}" >/dev/null

timestamp=${GIT_PUBLISH_TIMESTAMP:-$(date -u +%Y%m%d-%H%M%S)}
branch="codex/${task_slug}-${timestamp}"
suffix=1

while git show-ref --verify --quiet "refs/heads/$branch" ||
      git ls-remote --exit-code --heads "$remote" "refs/heads/$branch" >/dev/null 2>&1; do
    branch="codex/${task_slug}-${timestamp}-${suffix}"
    suffix=$((suffix + 1))
done

git switch --create "$branch" "$base_ref"

cat <<EOF
Created fresh task branch: $branch
Base: $base_ref ($(git rev-parse --short HEAD))
Push with: git push -u $remote $branch
EOF
