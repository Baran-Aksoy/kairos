# 003 — Fins de support de l'OS

Statut : terminé
Priorité : haute

## Objectif
En tant qu'infogéreur, je veux voir pour chaque VM si son OS est encore supporté, et jusqu'à
quand, afin d'anticiper les montées de version avant la fin de support.

## Critères d'acceptation
- [x] `python -m kairos sync-eol` récupère les cycles Ubuntu depuis endoflife.date et les
      enregistre en base (relancer la commande met à jour sans doublon).
- [x] Chaque VM a un statut d'OS : supporté, fin de support à moins de 6 mois, support standard
      terminé (couvert seulement par Ubuntu Pro / ESM), fin de vie, ou inconnu.
- [x] La page client affiche ce statut et la date de fin de support pour chaque hôte ;
      la page hôte l'affiche aussi.
- [x] Les données de référence (cycles) sont communes à tous les clients et ne contiennent
      aucune donnée client.
- [x] Tests automatisés (sans appel réseau) ; `scripts/dod.sh` passe.

## Hors périmètre
- Autres OS que Ubuntu, logiciels applicatifs, recommandation de version cible.
- Détection d'un abonnement Ubuntu Pro sur la VM.
- Synchronisation planifiée (CronJob / worker) : commande manuelle pour l'instant.

## Estimation
Une demi‑session, risque faible. Rédigée par le tech lead (enchaînement 003‑004 demandé
par l'humain le 2026-11-10).

## Notes techniques
- Table `release_cycles` : référentiel public, exemptée de `client_id` (ADR 0003 amendée).
- Statut calculé à l'affichage à partir de la date du jour : rien à recalculer en tâche de fond.
