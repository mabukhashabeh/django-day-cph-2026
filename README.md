# Django Day Copenhagen 2026 — talk kit

**Stop relying on discipline: Pre-commit hooks that catch Django problems early**
Mohammad Abu Khashabeh · Friday 2 October 2026 · 14:55 · Union · 25 minutes

This repository is two things:

1. The **copy-paste config** (`.pre-commit-config.yaml` + `.github/workflows/pre-commit.yml`).
2. A **tiny Django app** with resettable demos: breakpoint, PEM, system check, missing migration, format, F821, then CI.

> Local hooks protect the people who installed them. CI protects the repo.

Present **`slides/interactive.html`**, not `index.html`. From the repo root:

```bash
python3.12 scripts/present.py
```

Then open http://127.0.0.1:8777/interactive.html and go fullscreen (`F`). **T** opens a real IDE with a live terminal. **G** opens GitHub Actions. Stay in the deck.

## Configure locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
python manage.py check
pre-commit run --all-files
```

Hallway extras: missing migration, format, F821, leftover conflict markers, then CI-if-you-skipped-local. Reset between each:

```bash
./scripts/demo-1-secrets-and-breakpoint.sh
./scripts/reset.sh
./scripts/demo-2-django-check.sh
./scripts/reset.sh
./scripts/demo-pass.sh
```

If a demo dies: do not debug. The next slide is the output.

## Files

```
slides/interactive.html            the deck
.pre-commit-config.yaml            the stack
.github/workflows/pre-commit.yml   the required check
scripts/                           resettable demos
```
