# ISIMA Pixel War 2026 — DevOps

Plateforme Cloud-Native complète pour une Pixel War collaborative en temps réel.

## Architecture

```
Internet
   │
   ▼
[Ingress nginx]
   ├── /       → frontend (React, nginx) ×2
   └── /api    → backend  (Flask)        ×2
                     │
                     ▼
               [PostgreSQL] (StatefulSet, PVC 5Gi)

[Namespace: monitoring]
   ├── Prometheus (scrape backend + nodes)
   └── Grafana    (dashboards PixelWar)
```

**Stack :**
| Couche | Technologie |
|---|---|
| Frontend | React + Canvas API, servi par nginx |
| Backend | Python / Flask + Gunicorn |
| Base de données | PostgreSQL 15 (StatefulSet) |
| IaC | Terraform (GKE, Artifact Registry, IAM) |
| Configuration | Ansible (common hardening, Docker) |
| Conteneurs | Docker multi-stage (images minimales) |
| Orchestration | Kubernetes / GKE |
| CI/CD | GitHub Actions |
| Observabilité | Prometheus + Grafana |

---

## Déploiement de zéro

### Prérequis

```bash
# Outils requis
gcloud  >= 450
terraform >= 1.6
kubectl >= 1.28
ansible >= 2.14
docker  >= 24
```

### 1. Terraform — Provisionner l'infrastructure GCP

```bash
cd terraform

# Authentification GCP
gcloud auth application-default login

# Initialiser et déployer
terraform init
terraform plan
terraform apply

# Récupérer les credentials kubectl
$(terraform output -raw get_credentials_cmd)
```

Terraform crée :
- Cluster GKE (2 nœuds `e2-medium`, Network Policy Calico activé, Workload Identity)
- Artifact Registry Docker (`europe-west1-docker.pkg.dev/…/pixel-war`)
- Service Account CI/CD avec rôles minimaux (`artifactregistry.writer`, `container.developer`)

### 2. Ansible — Configurer les nœuds (optionnel sur GKE managé)

Pour des VMs custom ou un cluster bare-metal :

```bash
cd ansible

# Éditer l'inventaire avec vos IPs
nano inventory.ini

# Lancer le playbook complet
ansible-playbook -i inventory.ini site.yml
```

Le playbook `site.yml` applique :
- **Role `common`** : packages, timezone, swap désactivé, sysctl k8s, hardening SSH
- **Role `docker`** : installation Docker CE, daemon configuré (log rotation, `no-new-privileges`)

### 3. Build & Push des images Docker (manuel, ou via CI/CD)

```bash
# Backend
docker build -t europe-west1-docker.pkg.dev/pixel-war-489910/pixel-war/backend:latest ./Backend
docker push europe-west1-docker.pkg.dev/pixel-war-489910/pixel-war/backend:latest

# Frontend
docker build -t europe-west1-docker.pkg.dev/pixel-war-489910/pixel-war/frontend:latest ./pixel-war
docker push europe-west1-docker.pkg.dev/pixel-war-489910/pixel-war/frontend:latest
```

### 4. Kubernetes — Déployer l'application

```bash
# Créer le namespace
kubectl create namespace pixelwar

# Appliquer les manifests (ordre important)
kubectl apply -f k8s/secret.yaml           -n pixelwar
kubectl apply -f k8s/db.yaml               -n pixelwar
kubectl apply -f k8s/backend.yaml          -n pixelwar
kubectl apply -f k8s/frontend.yaml         -n pixelwar
kubectl apply -f k8s/network-policies.yaml -n pixelwar
kubectl apply -f k8s/ingress/              -n pixelwar

# Stack de monitoring
kubectl apply -f k8s/monitoring/namespace.yaml
kubectl apply -f k8s/monitoring/          -n monitoring

# Vérifier
kubectl get pods -n pixelwar
kubectl get pods -n monitoring
```

### 5. CI/CD — GitHub Actions

Ajouter ces secrets dans `Settings > Secrets > Actions` du dépôt GitHub :

| Secret | Valeur |
|---|---|
| `GCP_SA_KEY` | JSON de la clé du SA (cf. `terraform output cicd_service_account`) |

Le pipeline se déclenche automatiquement sur chaque push `main` :
1. **Test** — lint flake8 du backend
2. **Build & Push** — images taguées `sha` + `latest` vers Artifact Registry
3. **Deploy** — `kubectl set image` + attente du rollout

### 6. Accéder à l'application

```bash
# Frontend
kubectl get svc frontend -n pixelwar
# → External IP du LoadBalancer

# Grafana
kubectl get svc grafana -n monitoring
# → External IP:3000  (admin / pixelwar2026!)

# Créer une partie pour commencer
curl -X POST http://<BACKEND_IP>:5000/games \
  -H 'Content-Type: application/json' \
  -d '{"game_id":"main","title":"ISIMA 2026","width":50,"height":50}'
```

---

## Sécurité

| Mesure | Détail |
|---|---|
| Secrets K8s | Variables sensibles dans `Secret` (jamais en clair dans les Deployments) |
| Conteneurs non-root | `runAsNonRoot: true`, `runAsUser` défini sur tous les pods |
| Read-only filesystem | `readOnlyRootFilesystem: true` sur le backend |
| Drop capabilities | `capabilities.drop: [ALL]` sur tous les conteneurs |
| NetworkPolicies | Deny-all par défaut, flux autorisés explicitement (frontend→backend→db) |
| SSH hardening | Root login et authentification par mot de passe désactivés via Ansible |
| GKE Shielded Nodes | Secure Boot + Integrity Monitoring activés |
| Service Account CI/CD | Privilèges minimaux (pas de `roles/owner` ou `roles/editor`) |

## Résilience

- **Backend** : 2 replicas + HPA (scale jusqu'à 6 sur CPU > 70%)
- **Frontend** : 2 replicas
- **Base de données** : StatefulSet avec PVC (survit aux redémarrages de pod et de nœud)
- **Auto-repair / auto-upgrade** : activé sur le node pool GKE

## Choix techniques justifiés

**PostgreSQL vs Redis** : La grille est un état persistant structuré (tableau 2D). PostgreSQL avec JSONB permet des mises à jour atomiques par pixel (`UPDATE … SET grid = …`) et survit naturellement aux pannes contrairement à un cache mémoire.

**StatefulSet vs Deployment pour la DB** : Un StatefulSet garantit une identité réseau stable (`db-0`) et une association persistante PVC/pod, ce qui est requis pour une base de données.

**Gunicorn** : Serveur WSGI multi-processus pour Flask en production (remplace le serveur de développement intégré).

**Multi-stage Dockerfile** : L'image frontend compile React dans un stage Node puis copie le build statique dans nginx:alpine — image finale < 30 MB sans outils de build.

## Développement local

```bash
# Tout en un avec Docker Compose
docker compose up --build

# Frontend : http://localhost:3000
# Backend  : http://localhost:5000
# Créer une partie :
curl -X POST http://localhost:5000/games \
  -H 'Content-Type: application/json' \
  -d '{"game_id":"test","title":"Local","width":30,"height":30}'
```
