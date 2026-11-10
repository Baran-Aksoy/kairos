# 0004 — Compatible Kubernetes : application sans état

Date : 2026-11-10 · Statut : acceptée

## Contexte
Kairos doit tourner sur Docker Compose **et** sur Kubernetes, avec plusieurs réplicas
de l'API et du futur worker.

## Décision
L'application (API, worker) est **sans état**. Tout l'état vit dans PostgreSQL.

| Règle | Concrètement |
|---|---|
| Aucune écriture sur le disque local | Image compatible `readOnlyRootFilesystem` ; seul un `/tmp` éphémère est permis pour un traitement en cours |
| Configuration par variables d'environnement | `KAIROS_*` (ConfigMap / Secret) ; jamais de fichier de configuration modifié à l'exécution |
| Aucune session ni cache en mémoire partagé | Sessions dans un cookie signé ou en base ; un réplica peut mourir à tout moment |
| Migrations séparées | Service `migrate` en Compose, Job (hook Helm) en Kubernetes ; jamais au démarrage de l'API |
| Tâches planifiées sans doublon | Tâches périodiques Procrastinate (verrou en base) ou CronJob, jamais un planificateur en mémoire par réplica |
| Fichiers produits (rapports PDF, SBOM) | Générés à la demande, ou stockés en base / stockage objet S3 ; jamais sur le disque du pod |
| Journaux | Sur la sortie standard, au format structuré |
| Sondes | `/health` (vivant, sans base) ; `/ready` (prêt, base joignable) à ajouter avec le chart Helm |
| Arrêt propre | Gestion de SIGTERM (uvicorn le fait) |
| Utilisateur non root | UID numérique 10001 |

## Hors de l'application (avec état, géré à part)
- **PostgreSQL** : base managée ou opérateur (ex. CloudNativePG). Le script
  `deploy/postgres/init/` ne sert qu'en Compose ; en Kubernetes, le rôle `grafana_reader`
  est créé par l'opérateur ou l'administrateur de la base.
- **Base de vulnérabilités de Trivy** (plusieurs centaines de Mo) : à trancher lors du
  prototype CVE. Pistes : `trivy server` déployé à part avec son propre cache, ou
  téléchargement dans un volume éphémère au démarrage du worker.
- **Grafana** : instance existante ou déployée à part.

## Conséquences
- Le relecteur bloque tout code qui écrit sur le disque local ou garde un état en mémoire.
- Le déploiement Kubernetes (chart Helm, sondes, Job de migration) fera l'objet d'une story.
