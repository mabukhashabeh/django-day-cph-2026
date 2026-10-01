#!/usr/bin/env bash
# Hall demo — leftover conflict markers. People forget this hook exists.
# The markers live in a text file so Django never imports a broken view.
# check-merge-conflict needs --assume-in-merge or it is a no-op after the merge.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/conflict.txt conflict-demo.txt
git add -f conflict-demo.txt
echo
echo ">>> About to commit. Watch check-merge-conflict."
echo
set +e
git commit -m "wip: merge leftover"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded. Did the yaml lose --assume-in-merge?"
  exit 1
fi
echo "Expected failure: leftover conflict markers in the file."
echo "Reset with: ./scripts/reset.sh"
