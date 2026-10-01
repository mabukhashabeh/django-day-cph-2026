#!/usr/bin/env bash
# Put the repo back to a clean, passing state.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

git restore --staged --worktree -- catalog/views.py catalog/models.py shop/settings.py 2>/dev/null || true
git restore --staged -- secrets/id_rsa 2>/dev/null || true
rm -f secrets/id_rsa
python - <<'PY'
from pathlib import Path
p = Path("shop/settings.py")
text = p.read_text()
text = text.replace("BROKEN_ON_PURPOSE = True", "BROKEN_ON_PURPOSE = False")
p.write_text(text)
PY
echo "Reset. Working tree should pass hooks."
