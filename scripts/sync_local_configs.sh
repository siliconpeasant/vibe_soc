#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: scripts/sync_local_configs.sh <target-worktree> [source-worktree]

Populate a task worktree with the repository's whitelisted machine-local
configuration. By default, configuration is copied from source-worktree (or
the current checkout). If VIBE_SOC_LOCAL_CONFIG_ROOT or the repository-local
Git key vibeSoc.localConfigRoot is set, configuration is linked from that
persistent directory instead.
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

target_root=$1
source_worktree=${2:-$(git rev-parse --show-toplevel 2>/dev/null || true)}
if [ -z "$source_worktree" ]; then
    echo "A source worktree is required outside a Git checkout." >&2
    exit 2
fi
if [ ! -d "$target_root" ]; then
    echo "Target worktree does not exist: $target_root" >&2
    exit 1
fi
if [ ! -d "$source_worktree" ]; then
    echo "Source worktree does not exist: $source_worktree" >&2
    exit 1
fi

target_root=$(CDPATH= cd -- "$target_root" && pwd -P)
source_worktree=$(CDPATH= cd -- "$source_worktree" && pwd -P)

configured_root=${VIBE_SOC_LOCAL_CONFIG_ROOT:-}
if [ -z "$configured_root" ]; then
    configured_root=$(git -C "$source_worktree" config --local --get vibeSoc.localConfigRoot 2>/dev/null || true)
fi

sync_mode=copy
source_root=$source_worktree
if [ -n "$configured_root" ]; then
    if [[ "$configured_root" != /* ]]; then
        configured_root="$source_worktree/$configured_root"
    fi
    if [ ! -d "$configured_root" ]; then
        echo "Configured local config root does not exist: $configured_root" >&2
        exit 1
    fi
    source_root=$(CDPATH= cd -- "$configured_root" && pwd -P)
    sync_mode=link
fi

if [ "$source_root" = "$target_root" ]; then
    echo "Source and target local config roots must differ." >&2
    exit 1
fi

copied=0
linked=0
skipped=0

sync_item() {
    local relative=$1
    local source_item="$source_root/$relative"
    local target_item="$target_root/$relative"

    if [ ! -e "$source_item" ] && [ ! -L "$source_item" ]; then
        return
    fi
    if [ -e "$target_item" ] || [ -L "$target_item" ]; then
        skipped=$((skipped + 1))
        return
    fi

    mkdir -p "$(dirname -- "$target_item")"
    if [ "$sync_mode" = "link" ]; then
        ln -s "$source_item" "$target_item"
        linked=$((linked + 1))
    else
        cp -a -- "$source_item" "$target_item"
        copied=$((copied + 1))
    fi
}

for relative in scripts/local.mk scripts/local.sh scripts/local.csh; do
    sync_item "$relative"
done

sync_item pd/openroad/local

if [ -d "$source_root/pd/openroad" ]; then
    while IFS= read -r -d '' source_item; do
        relative=${source_item#"$source_root/"}
        sync_item "$relative"
    done < <(
        find "$source_root/pd/openroad" \
            \( -type f -o -type l \) -name config.local.mk -print0
    )
fi

if [ "$copied" -eq 0 ] && [ "$linked" -eq 0 ] && [ "$skipped" -eq 0 ]; then
    echo "Local config: no whitelisted files found; skipped."
else
    echo "Local config: copied=$copied linked=$linked existing=$skipped."
fi
