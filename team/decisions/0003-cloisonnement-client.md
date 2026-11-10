# 0003 — Cloisonnement par client

Date : 2026-11-10 · Statut : acceptée

## Décision
Toute table, sauf `clients`, porte une colonne `client_id`, même quand elle pourrait être
déduite d'une table parente. Toute requête applicative filtre par client.

## Raisons
- Kairos contient la carte des vulnérabilités de tous les clients : une fuite entre clients
  serait l'incident le plus grave possible.
- Le filtrage direct est simple à relire et permet d'ajouter plus tard la sécurité au niveau
  des lignes de PostgreSQL (row-level security).

## Contrôle
`tests/test_models.py` échoue si une table n'a pas de `client_id`.
