# 0002 — Observation seule, collecte via AWX, analyse côté serveur

Date : 2026-11-10 · Statut : acceptée (analyse CVE à valider par prototype)

## Décision
1. **Kairos n'agit jamais sur les VM.** Le playbook de collecte est en lecture seule,
   contrôlé automatiquement par `scripts/check_ansible_readonly.py`.
2. **AWX détient les identifiants SSH** et planifie le job de collecte. Kairos n'a aucune clé.
3. **Mode push** : le playbook envoie l'inventaire à l'API Kairos avec un jeton par client,
   injecté par un type d'identifiant personnalisé AWX.
4. **Rien n'est installé sur les VM.** L'analyse CVE se fait sur le serveur Kairos :
   liste des paquets → SBOM CycloneDX → Trivy (qui gère les rétroportages des distributions)
   → enrichissement EPSS / CISA KEV.

## Conséquences
- Une compromission de Kairos n'ouvre pas l'accès aux VM.
- Point à valider : Trivy doit exploiter correctement un SBOM construit à partir de
  `package_facts` (prototype dédié avant de construire l'analyse).
