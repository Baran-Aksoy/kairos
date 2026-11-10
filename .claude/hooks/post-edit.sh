#!/usr/bin/env bash
# PostToolUse (Edit|Write) — formatage et contrôles rapides, sans token.
# Ne coûte des tokens que si un contrôle échoue (le message est renvoyé à Claude).
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
file="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')"
[ -z "$file" ] && exit 0
case "$file" in
  "$ROOT"/*) rel="${file#"$ROOT"/}" ;;
  *) exit 0 ;;
esac

export PATH="$ROOT/.venv/bin:$PATH"
ruff_cmd() {
  if command -v uv >/dev/null 2>&1; then (cd "$ROOT" && uv run --quiet ruff "$@")
  elif command -v ruff >/dev/null 2>&1; then (cd "$ROOT" && ruff "$@")
  fi
}

case "$rel" in
  *.py)
    ruff_cmd format --quiet "$file" >/dev/null 2>&1
    ruff_cmd check --fix --quiet "$file" >/dev/null 2>&1
    ;;
  team/backlog/_*) ;;
  team/backlog/*.md)
    if ! out="$(python3 "$ROOT/scripts/check_story.py" "$file" 2>&1)"; then
      echo "Story non conforme au modèle (team/backlog/_modele.md) :" >&2
      echo "$out" >&2
      exit 2
    fi
    ;;
  ansible/*.yml | ansible/*.yaml)
    if ! out="$(python3 "$ROOT/scripts/check_ansible_readonly.py" 2>&1)"; then
      echo "Ansible : la collecte doit rester en lecture seule :" >&2
      echo "$out" >&2
      exit 2
    fi
    ;;
esac
exit 0
