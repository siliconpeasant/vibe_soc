#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/cleanup_task_worktree.sh <worktree-path> [base-branch]

Remove a task worktree and its local branch only when the worktree is clean and
the branch is contained in the latest remote base or exactly matches a merged
GitHub PR head. Remote branches are never deleted.
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

target=$1
base_branch=${2:-main}
remote=${GIT_PUBLISH_REMOTE:-origin}
repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "Not inside a Git repository." >&2
    exit 1
}
target=$(CDPATH= cd -- "$target" 2>/dev/null && pwd -P) || {
    echo "Worktree does not exist: $1" >&2
    exit 1
}
current=$(pwd -P)
if [ "$target" = "$repo_root" ] || [ "$target" = "$current" ]; then
    echo "Refusing to remove the main or current worktree." >&2
    exit 1
fi
if ! git -C "$repo_root" worktree list --porcelain | grep -Fqx "worktree $target"; then
    echo "Path is not a registered worktree: $target" >&2
    exit 1
fi
if [ -n "$(git -C "$target" status --porcelain --untracked-files=normal)" ]; then
    echo "Refusing to remove a dirty worktree: $target" >&2
    exit 1
fi
branch=$(git -C "$target" symbolic-ref --quiet --short HEAD) || {
    echo "Refusing to remove a detached worktree." >&2
    exit 1
}
case "$branch" in
    codex/*|feature/*|fix/*) ;;
    *)
        echo "Refusing to remove non-task branch: $branch" >&2
        exit 1
        ;;
esac

git -C "$repo_root" fetch --prune "$remote" "$base_branch"
base_ref="$remote/$base_branch"
merged=0
if git -C "$repo_root" merge-base --is-ancestor "$branch" "$base_ref"; then
    merged=1
else
    remote_url=$(git -C "$repo_root" remote get-url "$remote")
fi
if [ "$merged" != "1" ] && command -v gh >/dev/null 2>&1 && \
   [[ "$remote_url" == *github.com* ]]; then
    # Squash-merged PR heads are not ancestors of main. Accept only a positive
    # merged-PR result from GitHub; any lookup failure remains fail-closed.
    github_repo=${remote_url#git@github.com:}
    github_repo=${github_repo#https://github.com/}
    github_repo=${github_repo#ssh://git@github.com/}
    github_repo=${github_repo%.git}
    merged_pr_head=$(gh pr list \
        --repo "$github_repo" \
        --head "$branch" --state merged --limit 1 \
        --json number,headRefOid --jq '.[0].headRefOid // ""' 2>/dev/null || true)
    local_head=$(git -C "$repo_root" rev-parse "$branch")
    if [ -n "$merged_pr_head" ] && [ "$merged_pr_head" = "$local_head" ]; then
        merged=1
    fi
fi
if [ "$merged" != "1" ]; then
    echo "Refusing to remove unmerged branch: no ancestor or merged-PR evidence for $branch" >&2
    exit 1
fi

git -C "$repo_root" worktree remove "$target"
# A squash-merged head is intentionally not an ancestor of the base, so the
# guarded deletion must bypass Git's ancestry-only `-d` check.
git -C "$repo_root" branch --delete --force "$branch"
cat <<EOF
Removed worktree: $target
Deleted merged local branch: $branch
Remote branches were not changed.
EOF
