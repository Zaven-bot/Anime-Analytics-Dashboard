#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LINT_DIR="$REPO_ROOT/tools/linting"

cd "$REPO_ROOT"

echo "Auto-fixing Python code formatting..."

echo "  -> isort (import sorting)..."
isort --settings-file="$LINT_DIR/pyproject.toml" services/etl services/backend

echo "  -> black (code formatting)..."
black --config="$LINT_DIR/pyproject.toml" services/etl services/backend

echo ""
echo "Auto-fixing JavaScript code formatting..."
cd services/frontend

# Copy configs temporarily
cp "$LINT_DIR/.eslintrc.js" .
cp "$LINT_DIR/.prettierrc" .

echo "  -> prettier..."
npx prettier --write src/

echo "  -> eslint (auto-fixable issues)..."
npx eslint src/ --ext .js,.jsx --fix

# Clean up
rm .eslintrc.js .prettierrc

cd "$REPO_ROOT"
echo ""
echo "Auto-formatting complete! Run lint.sh to check remaining issues."
