#!/usr/bin/env bash
# Définition de « terminé » : tout doit passer avant un commit.
# Lancé automatiquement par le hook .claude/hooks/pre-commit-gate.sh.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
export PATH="$ROOT/.venv/bin:$PATH"

run() {
  if command -v uv >/dev/null 2>&1; then uv run --quiet "$@"; else "$@"; fi
}

fail=0
step() {
  local label="$1"; shift
  local out
  if out="$("$@" 2>&1)"; then
    echo "ok    $label"
  else
    echo "ÉCHEC $label"
    echo "$out" | tail -n 30
    fail=1
  fi
}

step "ruff check"            run ruff check .
step "ruff format"           run ruff format --check .
step "ansible lecture seule" python3 scripts/check_ansible_readonly.py

if command -v ansible-playbook >/dev/null 2>&1; then
  step "ansible syntaxe" ansible-playbook --syntax-check -i localhost, ansible/collect.yml
fi

shopt -s nullglob
stories=(team/backlog/[0-9]*.md)
if ((${#stories[@]})); then
  step "stories (prêt)" python3 scripts/check_story.py "${stories[@]}"
fi

step "pytest" run pytest -q

exit "$fail"
