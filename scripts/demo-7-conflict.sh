#!/usr/bin/env bash
# Hall demo — leftover conflict markers. People forget this hook exists.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/views_conflict.py catalog/views.py
git add catalog/views.py
echo
echo ">>> About to commit. Watch check-merge-conflict."
echo
set +e
git commit -m "wip: merge leftover"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded."
  exit 1
fi
echo "Expected failure: leftover conflict markers in the file."
echo "Reset with: ./scripts/reset.sh"
