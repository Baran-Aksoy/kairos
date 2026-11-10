#!/usr/bin/env python3
"""Definition of Ready check for stories in team/backlog/.

A story must contain the required sections and a valid status. Once its status is
"prêt" or later, the tech lead's estimate must be filled in.

Usage: check_story.py STORY.md [STORY.md ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ("Objectif", "Critères d'acceptation", "Hors périmètre", "Estimation")
STATUSES = ("brouillon", "prêt", "en cours", "terminé")
NEEDS_ESTIMATE = {"prêt", "en cours", "terminé"}

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_STATUS_RE = re.compile(r"^Statut\s*:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_CRITERION_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+\S", re.MULTILINE)
_PLACEHOLDER_RE = re.compile(r"^_.*_$")


def _sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(text))
    result = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.end() : end].strip()
    return result


def _is_empty(body: str) -> bool:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return all(_PLACEHOLDER_RE.match(line) for line in lines)


def check_story(text: str) -> list[str]:
    errors = []
    sections = _sections(text)
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            errors.append(f"section manquante : '## {name}'")

    status_match = _STATUS_RE.search(text)
    status = status_match.group(1).lower() if status_match else None
    if status not in STATUSES:
        errors.append(f"'Statut :' doit valoir l'un de {', '.join(STATUSES)}")

    criteria = sections.get("Critères d'acceptation", "")
    if "Critères d'acceptation" in sections and not _CRITERION_RE.search(criteria):
        errors.append("au moins un critère d'acceptation au format '- [ ] ...'")

    if "Hors périmètre" in sections and _is_empty(sections["Hors périmètre"]):
        errors.append("'Hors périmètre' ne doit pas être vide (écrire 'Rien' si c'est le cas)")

    if status in NEEDS_ESTIMATE and _is_empty(sections.get("Estimation", "")):
        errors.append(f"statut '{status}' : l'estimation du tech lead est obligatoire")

    return errors


def main(argv: list[str]) -> int:
    failed = False
    for arg in argv[1:]:
        path = Path(arg)
        errors = check_story(path.read_text(encoding="utf-8"))
        for error in errors:
            print(f"{path.name}: {error}", file=sys.stderr)
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
