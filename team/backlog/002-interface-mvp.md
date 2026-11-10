# 002 — Interface minimale : clients, hôtes, paquets

Statut : en cours
Priorité : haute

## Objectif
En tant qu'infogéreur, je veux consulter dans un navigateur mes clients, leurs VM et les
paquets installés, afin de voir ce que Kairos a collecté sans passer par la base.

## Critères d'acceptation
- [ ] `/` liste les clients avec leur nombre d'hôtes et la date de la dernière collecte.
- [ ] `/clients/<client>` liste les hôtes du client : OS, version, noyau, date de dernière
      collecte, nombre de paquets (dernière collecte).
- [ ] `/clients/<client>/hosts/<hôte>` affiche la dernière collecte et ses paquets, filtrables par nom.
- [ ] Une page client n'affiche jamais un hôte d'un autre client ; client ou hôte inconnu : 404.
- [ ] Rendu côté serveur (Jinja2, échappement HTML), sans JavaScript, lisible sur mobile,
      thème clair et sombre.
- [ ] Tests automatisés ; `scripts/dod.sh` passe.

## Hors périmètre
- Authentification des utilisateurs : interface exposée en local uniquement (127.0.0.1)
  jusqu'à une story dédiée.
- EOL, CVE, historique entre collectes, pagination, HTMX, export.

## Estimation
Une demi‑session, risque faible. Rédigée par le tech lead (économie de tokens), à la demande
de l'humain qui a validé le périmètre le 2026-11-10.

## Notes techniques
_aucune_
