#!/usr/bin/env bash
# Optional hall demo — black + isort --profile black.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/views_ugly.py catalog/views.py
git add catalog/views.py
echo
echo ">>> About to commit. Watch isort then black rewrite, or fail."
echo
set +e
git commit -m "wip: whatever the IDE saved"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded. Formatters are not in the yaml, or not installed."
  exit 1
fi
echo "Expected failure. Formatting is no longer a person."
echo "Reset with: ./scripts/reset.sh"
