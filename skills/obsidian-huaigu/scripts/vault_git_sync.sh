#!/usr/bin/env bash
set -euo pipefail

VAULT_DIR=${1:-"$HOME/obsidian/obsidian_huaigu"}

cd "$VAULT_DIR"

echo "[vault] git status (before)"
git status --porcelain || true

echo "[vault] git pull --rebase"
# If this hits conflicts, git will exit non-zero and leave repo in rebase state.
git pull --rebase

echo "[vault] git status (after)"
git status --porcelain || true
