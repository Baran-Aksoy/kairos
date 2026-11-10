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

if git_sub commit || git_sub merge || git_sub rebase; then
  echo "Refusé : seul l'humain commite et fusionne (CLAUDE.md, règle 7). Laisser les changements non commités." >&2
  exit 2
fi

exit 0
