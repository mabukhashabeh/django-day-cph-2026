#!/usr/bin/env bash
# Optional hall demo — flake8 F821, name used before it exists.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/views_f821.py catalog/views.py
git add catalog/views.py
echo
echo ">>> About to commit. Watch flake8 F821."
echo
set +e
git commit -m "fix: health payload"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded."
  exit 1
fi
echo "Expected failure: ok is not defined. That is F821."
echo "Reset with: ./scripts/reset.sh"
