#!/usr/bin/env bash
# Demo 2 — manage.py check fails because BROKEN_ON_PURPOSE is True.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python - <<'PY'
from pathlib import Path
p = Path("shop/settings.py")
text = p.read_text()
if "BROKEN_ON_PURPOSE = False" not in text:
    raise SystemExit("Could not find BROKEN_ON_PURPOSE = False")
p.write_text(text.replace("BROKEN_ON_PURPOSE = False", "BROKEN_ON_PURPOSE = True", 1))
PY

git add shop/settings.py
echo
echo ">>> About to commit. Watch django-system-check / catalog.E001"
echo
set +e
git commit -m "chore: surely this is just a settings tweak"
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "UNEXPECTED: commit succeeded. Is the local hook installed?"
  exit 1
fi
echo "Expected failure: a system check reached the commit gate."
