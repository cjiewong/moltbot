#!/usr/bin/env bash
set -euo pipefail

VAULT_DIR=${1:-"$HOME/obsidian/obsidian_huaigu"}
MSG=${2:-"obsidian: update notes"}

cd "$VAULT_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
  :
fi

echo "[vault] git status (before add)"
git status --porcelain || true

# Stage tracked changes + new files
# NOTE: This will add ALL changes under the vault. Use with care.
git add -A

echo "[vault] git status (staged)"
git status --porcelain || true

# If nothing staged, do nothing.
if git diff --cached --quiet; then
  echo "[vault] nothing to commit"
  exit 0
fi

echo "[vault] git commit"
git commit -m "$MSG"

echo "[vault] git push"
git push
