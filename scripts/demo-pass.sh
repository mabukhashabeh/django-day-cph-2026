#!/usr/bin/env bash
# What "Passed" looks like. Run this after reset.sh, on a clean tree.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo ">>> Clean tree. This is the boring success you want."
echo
.venv/bin/pre-commit run --all-files
echo
echo "That is a pass. No story. Commit would go through."
