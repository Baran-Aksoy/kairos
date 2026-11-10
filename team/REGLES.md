# Règles de l'équipe Kairos

## Rôles

| Rôle | Qui | Décide de | N'a pas le droit de |
|---|---|---|---|
| **Humain** | toi | « prêt », fusion, push, arbitrages | — |
| **PO** | agent `po` | quoi et pourquoi, priorités, périmètre | coder, clore une story, demander de livrer |
| **Tech lead + dev** | session principale | comment, estimation, implémentation | ajouter du périmètre, fusionner, pousser |
| **Relecteur** | agent `relecteur` | conformité qualité et sécurité (veto) | modifier le code, juger le périmètre fonctionnel |

**Vetos** : le PO peut refuser ce qui sort du périmètre ; le relecteur peut bloquer
ce qui ne respecte pas la qualité ou la sécurité. **Seul l'humain livre.**

## Déroulé d'une story

1. L'humain demande une story → le **PO** rédige `team/backlog/NNN-titre.md` (`brouillon`).
2. Le **tech lead** relit : faisabilité, risques, estimation. **Un seul aller‑retour** avec le PO ;
   en cas de désaccord, question à l'humain avec options.
3. 🔒 **L'humain passe la story à `prêt`.**
4. Le **dev** crée la branche `story/NNN-titre`, implémente, teste (`en cours`).
5. Le **relecteur** relit le diff. S'il bloque : correction, puis **une seule** relecture de plus ;
   au‑delà, l'humain arbitre.
6. Le **PO** fait la recette des critères d'acceptation.
7. 🔒 **L'humain fusionne et pousse.** Le dev passe la story à `terminé` et écrit le journal.

## Définition de « prêt »
Vérifiée par `scripts/check_story.py` (hook automatique) :
- sections Objectif, Critères d'acceptation, Hors périmètre, Estimation ;
- au moins un critère `- [ ] …`, « Hors périmètre » non vide ;
- estimation remplie dès que le statut est `prêt`.

## Définition de « terminé »
Vérifiée par `scripts/dod.sh`, lancé automatiquement avant chaque commit :
- ruff (lint + format), pytest, collecte Ansible en lecture seule, syntaxe Ansible ;

et par le relecteur :
- chaque critère couvert par un test, chaque changement rattaché à un critère ;
- aucun secret ni donnée client réelle.

## Économie de tokens
- Une story par session, `/clear` entre deux stories.
- Agents appelés uniquement aux étapes 1, 5 et 6 ; réponses de 10 lignes maximum.
- Le relecteur ne lit que le diff.
- Les contrôles mécaniques sont des scripts, pas des agents.

## Garde‑fous techniques
- `git push`, `gh pr create/merge` : interdits (`.claude/settings.json` + `.claude/hooks/git-gate.sh`).
- Pas de commit sur `main`, pas de commit si `scripts/dod.sh` échoue.
- Le PO ne peut écrire que dans `team/` (`.claude/hooks/po-scope.sh`).

## Espace commun
- `backlog/` — stories (modèle : `_modele.md`)
- `decisions/` — décisions d'architecture (ADR), numérotées
- `journal/` — une entrée par session : ce qui a été fait, décidé, reporté
- `QUESTIONS-OUVERTES.md` — ce qui attend une décision de l'humain
