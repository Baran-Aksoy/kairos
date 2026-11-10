# Kairos

Suivi des versions, fins de support (EOL) et vulnérabilités (CVE) d'un parc de VM
multi‑clients, pour les infogéreurs.

> **Statut : initialisation.** Rien n'est encore utilisable.

## Principe

1. **Collecter** — un job AWX lance `ansible/collect.yml` sur les inventaires des clients.
   Le playbook est strictement en lecture seule et envoie l'inventaire à l'API Kairos.
2. **Comparer** — Kairos confronte l'inventaire aux bases publiques
   (endoflife.date, bases de sécurité des distributions, OSV, EPSS, CISA KEV) via Trivy.
3. **Afficher** — interface Kairos pour le détail, Grafana pour les tableaux de bord.

Kairos **n'agit jamais** sur les machines : il observe et recommande.

## Démarrage (développement)

```bash
cp .env.example .env               # puis renseigner les mots de passe
docker compose up -d               # API sur http://127.0.0.1:8000/health
docker compose --profile grafana up -d   # + Grafana sur http://127.0.0.1:3000
```

Sans Docker :

```bash
uv sync
uv run pytest
uv run uvicorn kairos.main:app --reload
```

## Organisation

Le projet est développé avec Claude Code et une petite équipe d'agents
(voir [team/REGLES.md](team/REGLES.md)).
