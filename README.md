# ISIMA Pixel War 2026 — DevOps

Ce dépôt présente une mise en production Cloud-Native d’un MVP Pixel War, avec automatisation IaC, déploiement Kubernetes, CI/CD et observabilité.

## 1) Architecture cible

```
Internet
   │
   ▼
[Ingress GKE (gce)]
   ├── /       → frontend (React + nginx)
   └── /api    → backend  (Flask + Gunicorn)
                     │
                     ▼
               [PostgreSQL StatefulSet + PVC]

[Namespace monitoring]
   ├── Prometheus
   └── Grafana
```

### Stack technique

| Couche | Choix |
|---|---|
| Frontend | React + Canvas API, servi par nginx |
| Backend | Python Flask + Gunicorn |
| Données | PostgreSQL 15 (StatefulSet + PVC) |
| IaC | Terraform (GCP/GKE/Artifact Registry/IAM) |
| Configuration | Ansible (`common`, `docker`) |
| Orchestration | Kubernetes (GKE) |
| CI/CD | GitHub Actions |
| Observabilité | Prometheus + Grafana |

## 2) Déploiement de zéro

### Prérequis

```bash
gcloud >= 450
terraform >= 1.6
kubectl >= 1.28
ansible >= 2.14
docker >= 24
```

### 2.1 Provisionnement infra (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Si l’exécution échoue avec des `403` (`compute.instanceGroupManagers.get`, `iam.serviceAccounts.get`), le compte/SA ne possède pas les permissions IAM nécessaires sur le projet.

### 2.2 Configuration hôtes (Ansible, optionnel sur GKE managé)

```bash
cd ansible
ansible-playbook -i inventory.ini site.yml
```

### 2.3 Déploiement Kubernetes

```bash
kubectl create namespace pixelwar || true

kubectl apply -f k8s/priority-classes.yaml
kubectl apply -f k8s/secret.yaml           -n pixelwar
kubectl apply -f k8s/db.yaml               -n pixelwar
kubectl apply -f k8s/backend.yaml          -n pixelwar
kubectl apply -f k8s/frontend.yaml         -n pixelwar
kubectl apply -f k8s/network-policies.yaml -n pixelwar
kubectl apply -f k8s/ingress/              -n pixelwar

kubectl apply -f k8s/monitoring/namespace.yaml
kubectl apply -f k8s/monitoring/ -n monitoring
```

## 3) Pipeline CI/CD

Secret requis côté GitHub :

| Secret | Description |
|---|---|
| `GCP_SA_KEY` | Clé JSON du service account utilisé par GitHub Actions |

Le workflow fait :
1. tests/lint backend,
2. build + push images backend/frontend,
3. apply manifests Kubernetes,
4. rollout status,
5. récupération adresse ingress,
6. smoke test HTTP public,
7. debug automatique (pods/endpoints/ingress/logs) en sortie.

## 4) Utilisation de l’application

```bash
kubectl get ingress -n pixelwar
```

Puis ouvrir `http://<INGRESS_IP>/`.

API (exemples) :

```bash
# créer/rejoindre une partie
curl -X POST http://<INGRESS_IP>/api/games \
  -H 'Content-Type: application/json' \
  -d '{"game_id":"main","title":"ISIMA 2026","width":50,"height":50}'

# lire la grille
curl http://<INGRESS_IP>/api/games/main/grid
```

Le frontend supporte plusieurs parties via `game_id` (champ UI + URL `?game=<id>`).

## 5) Sécurité

- Secrets applicatifs centralisés dans `Secret` Kubernetes.
- Conteneurs non-root + capabilities minimales (`drop: [ALL]`).
- `readOnlyRootFilesystem` sur backend.
- NetworkPolicies : deny-all + flux explicitement autorisés.
- Node hardening (Ansible) pour scénarios VM/bare-metal.

## 6) Résilience et performance

- Backend avec HPA (`1 → 6` réplicas sur CPU).
- PostgreSQL en StatefulSet + PVC persistante.
- PriorityClass dédiée DB (`pixelwar-db-critical`) pour limiter le risque de starvation.
- Optimisation backend de pose de pixel via `jsonb_set(...)` (mise à jour d’une cellule, pas de réécriture complète de la grille).
- Polling frontend rendu plus réactif, avec garde anti-requêtes concurrentes.

## 7) Justification des choix

- **PostgreSQL** : persistance forte + JSONB adapté à l’état global de la grille.
- **StatefulSet pour DB** : identité stable + stockage persistant.
- **Gunicorn** : exécution production Flask.
- **Docker multi-stage** : images plus légères et reproductibles.
- **GKE Ingress (gce)** : exposition HTTP managée, intégrée à GCP.

## 8) Correspondance avec les critères du sujet

- **Automatisation** : Terraform + Ansible + CI/CD, faible intervention manuelle.
- **Sécurité** : secrets, non-root, NetworkPolicies, réduction des privilèges.
- **Qualité infra/code** : manifests séparés, Dockerfiles multi-stage, pipeline lisible.
- **Résilience** : HPA, stockage persistant, mécanismes de scheduling prioritaire.
- **Observabilité** : Prometheus + Grafana opérationnels.

## 9) Domaine personnalisé (optionnel)

Pour remplacer l’IP publique par un nom de domaine :

1. disposer d’un domaine (payant ou existant),
2. créer un enregistrement DNS `A` vers l’IP ingress,
3. ajouter une règle `host` dans l’ingress (quand l’admission webhook cluster est sain).
