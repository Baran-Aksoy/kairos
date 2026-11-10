# 004 — Prototype : CVE par Trivy sur un SBOM généré par Kairos

Statut : terminé
Priorité : haute

## Objectif
En tant qu'infogéreur, je veux savoir si Kairos peut trouver de façon fiable les CVE d'une VM
à partir de son inventaire, sans rien installer dessus, avant d'investir dans cette fonction.

## Critères d'acceptation
- [x] `python -m kairos sbom <client> <hôte>` produit un SBOM CycloneDX de la dernière collecte,
      limité au client indiqué.
- [x] Comparaison mesurée sur une VM Ubuntu : Trivy sur le SBOM contre Trivy sur le système
      de fichiers ; résultat et décision consignés dans une ADR.
- [x] Tests automatisés de la génération du SBOM ; `scripts/dod.sh` passe.

## Hors périmètre
- Stockage des CVE, EPSS / KEV, affichage dans l'interface, planification des analyses.
- Modification de la collecte (paquets source) : story suivante selon le résultat.

## Estimation
Une demi‑session, risque moyen (hypothèse technique). Rédigée par le tech lead
(enchaînement 003‑004 demandé par l'humain le 2026-11-10).

## Notes techniques
Résultat : ADR 0005. Script de comparaison non versionné (données de la machine de test).
