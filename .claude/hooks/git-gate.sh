#!/usr/bin/env bash
# PreToolUse (Bash) — garde-fou Git, sans token :
#  - interdit tout push et toute création/fusion de PR (seul l'humain pousse) ;
#  - interdit de commiter sur main ;
#  - bloque « git commit » si la définition de « terminé » (scripts/dod.sh) échoue.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cmd="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')"

git_sub() {  # matches "git <sub>" anywhere in the command, including "git -C dir <sub>"
  printf '%s' "$cmd" | grep -Eq "(^|[;&|(\`[:space:]])git([[:space:]]+-[^[:space:]]+([[:space:]]+[^-[:space:]][^[:space:]]*)?)*[[:space:]]+$1([[:space:]]|\$)"
}

if git_sub push || printf '%s' "$cmd" | grep -Eq 'gh[[:space:]]+pr[[:space:]]+(create|merge)'; then
  echo "Refusé : seul l'humain pousse vers GitHub ou crée/fusionne une PR (CLAUDE.md, règle 7)." >&2
  exit 2
fi

if git_sub commit; then
  branch="$(git -C "$ROOT" symbolic-ref --short HEAD 2>/dev/null || true)"
  if [ "$branch" = "main" ]; then
    echo "Refusé : pas de commit sur main. Créer une branche story/NNN-titre." >&2
    exit 2
  fi
  if ! out="$("$ROOT/scripts/dod.sh" 2>&1)"; then
    { echo "Commit refusé : la définition de « terminé » n'est pas remplie."; echo "$out"; } >&2
    exit 2
  fi
fi

exit 0
