#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# ZOZI — Install git hooks
#
# Run once after cloning:
#   bash scripts/setup_hooks.sh
#
# Or configure git to use .githooks/ directly:
#   git config core.hooksPath .githooks
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.githooks"

echo "Installing ZOZI git hooks …"

# Method 1: git config (works on all platforms)
git config core.hooksPath .githooks
echo "✅ Set core.hooksPath = .githooks"

# Method 2: Also copy to .git/hooks as fallback for older git versions
if [ -d "$REPO_ROOT/.git/hooks" ]; then
    cp "$HOOKS_DIR/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
    chmod +x "$REPO_ROOT/.git/hooks/pre-commit"
    echo "✅ Copied pre-commit hook to .git/hooks/"
fi

echo ""
echo "Hooks installed. Architecture gate tests will run on every commit."
echo "To bypass (not recommended):  git commit --no-verify"
