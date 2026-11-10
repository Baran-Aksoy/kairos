# 001 — Collecter l'inventaire d'une VM Ubuntu et le recevoir dans Kairos

Statut : prêt
Priorité : haute

## Objectif
En tant qu'infogéreur, je veux qu'un job AWX collecte l'OS et les paquets apt d'une VM Ubuntu
et les envoie à Kairos avec le jeton de son client, afin de savoir quelles VM ont été
collectées, quand, et d'avoir la base de tout le reste (EOL, CVE) sans risque de mélange entre clients.

## Critères d'acceptation
- [ ] `ansible-playbook ansible/collect.yml` lancé sur une VM Ubuntu de test (connexion locale, test
      automatisé) envoie une collecte ; ensuite la base contient un hôte, un snapshot (distribution,
      version, noyau, date de collecte) et une installation par paquet apt (nom, version, `source=apt`,
      `detection_method=package`). Recette manuelle par l'humain via un job AWX.
- [ ] Un endpoint d'envoi (ex. `POST /api/v1/inventory`) exige un jeton ; sans jeton ou avec un jeton inconnu : 401, rien n'est écrit.
- [ ] Le client est déduit du jeton uniquement. Le corps de la requête ne peut pas désigner un autre client ; test : une collecte envoyée avec le jeton du client A n'apparaît jamais chez le client B (hôte de même nom inclus).
- [ ] Les jetons ne sont jamais stockés en clair (empreinte seule) ; ils ne figurent ni dans les journaux, ni dans les réponses, ni dans le dépôt.
- [ ] Renvoyer la même collecte ne crée pas de doublon d'hôte ; un nouveau snapshot est créé et `last_seen` de l'hôte est mis à jour.
- [ ] Une charge invalide (champ manquant, version vide) : 422, rien n'est écrit (aucun snapshot partiel).
- [ ] Le jeton est lu par le playbook depuis un type d'identifiant AWX (variable d'environnement), jamais en dur ; l'URL de l'API est un paramètre. `scripts/check_ansible_readonly.py` passe toujours.
- [ ] Un moyen d'exploitation minimal crée un client et affiche son jeton une seule fois (ex. commande `python -m kairos`), documenté dans le README.
- [ ] Pour un client, l'infogéreur obtient la liste des hôtes avec la date de dernière collecte
      via la commande d'exploitation (`python -m kairos hosts <client>`). Le jeton de collecte ne
      permet pas de lire.
- [ ] Tests automatisés couvrant les points ci-dessus avec des fixtures anonymisées (`client-a`, `vm-01`, `10.0.0.x`) ; `scripts/dod.sh` passe.

## Hors périmètre
- Détecteurs hors paquets (Docker, binaires, ports, snap, pip), autres OS (RPM, Windows).
- CVE, SBOM, Trivy, EOL, recommandations de montée de version.
- Interface Kairos et tableaux Grafana ; alerte « VM non collectée depuis N jours » (seule la date est exposée).
- Rotation/révocation de jetons, gestion de clients par API, authentification des utilisateurs.
- Worker Procrastinate, purge ou historisation des anciens snapshots, comparaison entre snapshots.
- Configuration réelle d'AWX (projet, inventaire, planification) au-delà de la documentation du type d'identifiant.

## Estimation
1 session, risque moyen. Tient sans découpage si les deux ajustements ci‑dessous sont acceptés.
Contenu : table des jetons + migration, commande d'exploitation, `POST /api/v1/inventory`
(authentification, validation, écriture transactionnelle), envoi depuis le rôle Ansible, tests.

## Notes techniques
Point de découpage si trop gros : (a) envoi authentifié + écriture en base, (b) playbook AWX + lecture des hôtes.

**Ajustements du tech lead, validés par l'humain le 2026-11-10 :**
1. **Lecture des hôtes** : ne pas réutiliser le jeton de collecte pour lire. Ce jeton vit dans AWX ;
   s'il fuit, il ne doit permettre que d'envoyer, jamais de lire l'inventaire (donc les failles)
   d'un client. Proposition : lecture par la commande d'exploitation
   (`python -m kairos hosts client-a`) ; la lecture par API viendra avec l'authentification des utilisateurs.
2. **Critère AWX** : AWX n'est pas disponible dans l'environnement de développement. Proposition :
   test automatisé avec `ansible-playbook` sur une VM Ubuntu locale (connexion locale), puis recette
   manuelle par l'humain sur son AWX.

**Choix techniques :**
- Jeton : 32 octets aléatoires, stocké en SHA‑256 (suffisant pour un secret à forte entropie),
  table `collect_tokens` avec `client_id`.
- L'envoi part du nœud d'exécution AWX (`delegate_to: localhost`) : les VM n'ont pas besoin
  d'accéder au réseau de Kairos.
- `package_facts` peut renvoyer plusieurs versions d'un même paquet (architectures) : une
  installation par couple nom + version.
- Insertion groupée (environ 2 000 paquets par VM) dans une seule transaction.
