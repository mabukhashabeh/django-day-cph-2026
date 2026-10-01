#!/usr/bin/env bash
# Demo 3 — model changed, no migration. makemigrations --check --dry-run fails.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/models_unmigrated.py catalog/models.py
git add catalog/models.py
echo
echo ">>> About to commit. Watch django-unmigrated-models"
echo
set +e
git commit -m "feat: add colour field"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded."
  exit 1
fi
echo "Expected failure: the migration was written in the model, not in git."
