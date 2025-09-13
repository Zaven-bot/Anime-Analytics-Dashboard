#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LINT_DIR="$REPO_ROOT/tools/linting"

cd "$REPO_ROOT"

echo "Running Python linting..."

# Use configs from tools/linting
echo "  -> flake8..."
flake8 --config="$LINT_DIR/.flake8" services/etl services/backend

echo "  -> mypy..."
mypy --config-file="$LINT_DIR/pyproject.toml" services/etl services/backend

echo "  -> black (check only)..."
black --config="$LINT_DIR/pyproject.toml" --check services/etl services/backend

echo ""
echo "Running JavaScript linting..."
cd services/frontend

# Copy configs temporarily (eslint/prettier expect them in project root)
cp "$LINT_DIR/.eslintrc.js" .
cp "$LINT_DIR/.prettierrc" .

echo "  -> eslint..."
npx eslint src/ --ext .js,.jsx

echo "  -> prettier..."
npx prettier --check src/

# Clean up
rm .eslintrc.js .prettierrc

cd "$REPO_ROOT"
echo ""
echo "All linting checks passed!"
