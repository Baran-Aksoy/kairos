# Kairos

Outil d'**observation** pour infogéreurs : inventaire des VM de plusieurs clients
(OS, logiciels, versions), fins de support (EOL), CVE, recommandations de montée de version.
La collecte passe par **AWX** (playbook `ansible/collect.yml`), l'affichage par une petite
interface Kairos et par **Grafana** (lecture seule sur le schéma `reporting`).

## Règles non négociables

1. **Kairos n'agit jamais sur les VM.** Le rôle Ansible est en lecture seule :
   uniquement des modules de collecte, `changed_when: false` sur toute commande.
   Vérifié par `scripts/check_ansible_readonly.py`.
2. **Cloisonnement par client** : chaque table (sauf `clients`) porte `client_id`,
   chaque requête filtre par client. Vérifié par `tests/test_models.py`.
3. **Versions** : toujours comparées avec `python-debian` / `univers`, jamais comme chaînes.
4. **CVE** : pour un paquet de distribution, la source de vérité est la base de la
   distribution (Ubuntu, Debian…), jamais NVD seul (rétroportages).
5. **Dépôt public** : aucun nom de client, nom d'hôte réel, IP, jeton ou secret.
   Les fixtures de test sont anonymisées (`client-a`, `vm-01`, `10.0.0.x`).
6. **Pas de sur‑ingénierie** : on n'écrit que ce qu'une story demande (voir `team/REGLES.md`).
7. **Ni commit, ni push, ni merge.** Ni Claude ni aucun agent n'exécute `git commit`,
   `git push`, `git merge`, ne crée ou ne fusionne de pull request. Claude travaille sur une
   branche `story/NNN-titre` créée depuis `main` et laisse les changements non commités ;
   l'humain commite, fusionne et pousse. Bloqué par `.claude/hooks/git-gate.sh`.
   Avant de passer à la story suivante : faire un topo à l'humain et attendre son accord.
8. **Sans état (Kubernetes)** : l'API et le worker n'écrivent rien sur le disque local et ne
   gardent aucun état en mémoire ; tout est dans PostgreSQL. Configuration par variables
   d'environnement, migrations hors démarrage. Détail : `team/decisions/0004-kubernetes-sans-etat.md`.

## Rapports

À la fin de chaque session de travail, et chaque fois que l'humain demande où on en est :
écrire ou mettre à jour `team/journal/AAAA-MM-JJ-sujet.md` (fait, vérifié, non vérifié,
décidé, reporté, prochaine étape) et en donner un résumé court dans la conversation.

## Pile

Python ≥ 3.12 (image Docker 3.14) · FastAPI · SQLAlchemy 2 + Alembic · PostgreSQL 18 ·
Trivy (côté serveur, sur SBOM) · Jinja2 + HTMX · Grafana · Docker Compose et Kubernetes.
Pas encore de worker : Procrastinate sera ajouté avec la première story qui en a besoin.

## Arborescence

- `src/kairos/` — application (`main.py`, `config.py`, `db.py`, `models.py`)
- `migrations/` — Alembic · `tests/` — pytest
- `ansible/` — playbook et rôle `kairos_collect` (projet AWX)
- `deploy/` — init PostgreSQL, provisioning Grafana
- `scripts/` — contrôles qualité (`dod.sh`, `check_story.py`, `check_ansible_readonly.py`)
- `team/` — règles d'équipe, backlog, décisions (ADR), journal, questions ouvertes

## Commandes

```bash
uv sync                          # installer les dépendances
uv run pytest                    # tests
uv run ruff check . && uv run ruff format .
scripts/dod.sh                   # définition de « terminé » (lancé avant chaque commit)
docker compose up -d             # API + PostgreSQL ; ajouter --profile grafana
```

## Conventions

- Code, noms et commentaires en **anglais** ; documentation et `team/` en **français**.
- Une story = une branche `story/NNN-titre` = une session (`/clear` entre deux stories).
- Messages de commit : `NNN: description courte` (NNN = numéro de story).

## Équipe

Workflow complet dans `team/REGLES.md`. Agents : `po` (produit) et `relecteur`
(QA, sécurité, lecture seule). La session principale tient le rôle tech lead + dev.
Seul l'humain valide « prêt » et fusionne.
