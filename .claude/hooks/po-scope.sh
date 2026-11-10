#!/usr/bin/env bash
# PreToolUse (Edit|Write) de l'agent po : écriture autorisée uniquement dans team/.
set -uo pipefail

ROOT="$(realpath -m "${CLAUDE_PROJECT_DIR:-$(pwd)}")"
file="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')"
file="$(realpath -m "$file")"

case "$file" in
  "$ROOT"/team/*) exit 0 ;;
esac
echo "Refusé : le PO n'écrit que dans team/ (fichier demandé : $file)." >&2
exit 2
