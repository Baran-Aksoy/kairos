# 0001 — Pile technique

Date : 2026-11-10 · Statut : acceptée

## Décision
Python (≥ 3.12, image 3.14) · FastAPI · SQLAlchemy 2 + Alembic · PostgreSQL 18 ·
Jinja2 + HTMX · Grafana (source PostgreSQL) · Docker Compose.
Worker Procrastinate (file de tâches dans PostgreSQL) ajouté quand une story en a besoin.

## Raisons
- Python : langage d'Ansible ; bibliothèques clés disponibles (`python-debian`, `univers`,
  `packageurl-python`, `cyclonedx-python-lib`).
- PostgreSQL seul composant de stockage : JSONB pour les faits bruts, relationnel pour le reste,
  lisible directement par Grafana.
- HTMX : une seule base de code ; Grafana couvre les tableaux de bord.

## Écarté
Go (perte de l'écosystème Python/Ansible), React (second projet à maintenir),
Celery + Redis (composant de plus pour peu de tâches), Kubernetes au démarrage.
