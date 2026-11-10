# Collecte Kairos (projet AWX)

Le playbook `collect.yml` lit l'OS et les paquets apt de chaque VM, **sans rien modifier**,
puis envoie l'inventaire à l'API Kairos depuis le nœud d'exécution AWX.

## 1. Créer le client et son jeton dans Kairos

```bash
docker compose run --rm api python -m kairos create-client client-a "Client A"
```

Le jeton n'est affiché qu'une fois : le copier directement dans AWX (étape 3).

## 2. Type d'identifiant personnalisé AWX

*Administration → Types d'identifiants → Ajouter*, nom : **Kairos**.

Configuration d'entrée :

```yaml
fields:
  - id: url
    type: string
    label: URL de l'API Kairos
  - id: token
    type: string
    label: Jeton de collecte
    secret: true
required: [url, token]
```

Configuration de l'injecteur :

```yaml
env:
  KAIROS_URL: "{{ url }}"
  KAIROS_TOKEN: "{{ token }}"
```

## 3. Identifiant et modèle de job

- Créer un identifiant de type **Kairos** par client (URL + jeton du client).
- Modèle de job : projet = ce dépôt, playbook = `ansible/collect.yml`, inventaire du client,
  identifiants = SSH du client **et** Kairos du client.

## Test sans AWX

```bash
KAIROS_URL=http://127.0.0.1:8000 KAIROS_TOKEN=<jeton> \
  ansible-playbook -i vm-01, -c local ansible/collect.yml
```
