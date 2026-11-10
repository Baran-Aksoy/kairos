from conftest import ROOT

VALID = """\
# 001 — Collecte

Statut : {status}
Priorité : haute

## Objectif
En tant qu'infogéreur, je veux voir l'OS de mes VM afin de repérer les fins de vie.

## Critères d'acceptation
- [ ] L'OS et sa version sont visibles pour chaque VM.

## Hors périmètre
- Les CVE.

## Estimation
{estimate}
"""


def test_draft_without_estimate_is_valid(story_checker):
    text = VALID.format(status="brouillon", estimate="_à compléter par le tech lead_")
    assert story_checker.check_story(text) == []


def test_ready_story_requires_estimate(story_checker):
    text = VALID.format(status="prêt", estimate="_à compléter par le tech lead_")
    assert any("estimation" in e for e in story_checker.check_story(text))


def test_ready_story_with_estimate_is_valid(story_checker):
    text = VALID.format(status="prêt", estimate="1 session, risque faible.")
    assert story_checker.check_story(text) == []


def test_missing_out_of_scope_section_is_rejected(story_checker):
    text = VALID.format(status="brouillon", estimate="").replace("## Hors périmètre", "## Divers")
    assert any("Hors périmètre" in e for e in story_checker.check_story(text))


def test_unknown_status_is_rejected(story_checker):
    text = VALID.format(status="fini", estimate="1 session")
    assert any("Statut" in e for e in story_checker.check_story(text))


def test_template_is_structurally_complete(story_checker):
    template = (ROOT / "team" / "backlog" / "_modele.md").read_text(encoding="utf-8")
    errors = story_checker.check_story(template)
    # The template only fails on placeholder values, never on missing sections.
    assert not any("section manquante" in e for e in errors)
