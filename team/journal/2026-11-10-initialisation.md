# 2026-11-10 — Initialisation

## Fait
- Cadrage du produit : observation seule, AWX derrière, Grafana pour les tableaux de bord.
- Pile technique (ADR 0001), architecture de collecte et d'analyse (ADR 0002),
  cloisonnement client (ADR 0003).
- Squelette : API FastAPI (`/health`), modèle d'inventaire + migration initiale,
  Docker Compose (API, PostgreSQL 18, Grafana optionnel), rôle Ansible minimal.
- Équipe légère : agents `po` et `relecteur`, hooks sans token (format, « prêt »,
  « terminé », lecture seule Ansible, interdiction de push).

- Contrainte Kubernetes : application sans état (ADR 0004) ; migrations sorties du
  démarrage de l'API (service `migrate`), image non root, API en lecture seule.

## Vérifié
- 16 tests pytest sur Python 3.14, `scripts/dod.sh` au vert.
- Pile Docker : migration appliquée sur PostgreSQL 18, 4 tables créées, `/health` répond.
- Hooks : push, PR, commit sur main et écriture du PO hors `team/` bien bloqués.

## Non vérifié
- Grafana : démarré mais vide (aucun tableau de bord, schéma `reporting` vide).

## Reporté
- Catalogue produits, CVE, constats : avec les stories qui en ont besoin.
- Worker de tâches de fond : avec la première story qui en a besoin.

## Prochaine étape
Story 001 rédigée par le PO : collecter l'inventaire d'une VM Ubuntu via AWX.
