#!/usr/bin/env bash
# How a skip looks locally, and how CI still catches it.
# Do NOT present --no-verify as a tip.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/views_breakpoint.py catalog/views.py
git add catalog/views.py

echo
echo ">>> Local hook would block this:"
echo
set +e
.venv/bin/pre-commit run debug-statements --files catalog/views.py
echo
echo ">>> A machine can still land it with --no-verify or a missing install."
echo ">>> CI does not care. Same config, --all-files:"
echo
.venv/bin/pre-commit run --all-files
status=$?
set -e
echo
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: all-files passed. The broken view was not staged/seen."
  exit 1
fi
echo "Failed in the all-files run. That is the required CI check."
echo "Reset with: ./scripts/reset.sh"
