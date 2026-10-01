#!/usr/bin/env bash
# Demo 1 — ~45s on stage.
# What the room should see: debug-statements + detect-private-key fail.
# If this fails for any other reason, go to slides: "what the terminal should show".
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cp fixtures/broken/views_breakpoint.py catalog/views.py
mkdir -p secrets
# Built at demo time so git never stores a PEM. Split so this script
# itself does not trip detect-private-key.
python3 - <<'PY'
from pathlib import Path

header = "-----BEGIN RSA " + "PRIVATE KEY-----"
footer = "-----END RSA " + "PRIVATE KEY-----"
Path("secrets/id_rsa").write_text(f"{header}\nDEMO_NOT_A_REAL_KEY\n{footer}\n")
PY

git add catalog/views.py
git add -f secrets/id_rsa
echo
echo ">>> About to commit. Watch debug-statements and detect-private-key."
echo
set +e
git commit -m "wip: definitely fine"
status=$?
set -e
echo
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded. Hooks are not installed. Run: pre-commit install"
  exit 1
fi
echo "Expected failure. That is the talk."
