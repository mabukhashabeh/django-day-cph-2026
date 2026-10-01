# Pre-commit hooks that catch Django problems early

Conference demo from [Django Day Copenhagen 2026](https://djangoday.dk/).

> Local hooks protect the people who installed them. CI protects the repo.

A tiny Django app plus the two files you copy: `.pre-commit-config.yaml` and `.github/workflows/pre-commit.yml`. The scripts put a `breakpoint()`, a PEM, or a failing system check in the way of `git commit`. CI runs the same config with `pre-commit run --all-files`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
python manage.py check
pre-commit run --all-files
```

## Demo

Reset between each. The first two must fail. The third must pass.

```bash
./scripts/demo-1-secrets-and-breakpoint.sh
./scripts/reset.sh
./scripts/demo-2-django-check.sh
./scripts/reset.sh
./scripts/demo-pass.sh
```

| Script | What fails |
|---|---|
| `demo-1-secrets-and-breakpoint.sh` | `debug-statements` (`breakpoint()`) and `detect-private-key` (PEM) |
| `demo-2-django-check.sh` | `django-system-check` (`catalog.E001`) |
| `demo-pass.sh` | nothing — `pre-commit run --all-files` on a clean tree |
| `demo-3-unmigrated.sh` | `makemigrations --check --dry-run` |
| `demo-4-why-ci.sh` | local skip vs `--all-files` |
| `demo-5-format.sh` | black |
| `demo-6-f821.sh` | flake8 |
| `demo-7-conflict.sh` | `check-merge-conflict` |

Copy the yaml and the workflow. In GitHub, make the `pre-commit` check **required** on the branch.
