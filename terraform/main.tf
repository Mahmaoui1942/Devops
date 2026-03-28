terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  # Uncomment to store state in GCS (recommended for prod)
  # backend "gcs" {
  #   bucket = "pixel-war-tfstate"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ── Variables ──────────────────────────────────────────────────────────────
variable "project_id" {
  default = "pixel-war-489910"
}
variable "region" {
  default = "europe-west1"
}
variable "zone" {
  default = "europe-west1-b"
}
variable "node_count" {
  default = 2
}
variable "max_node_count" {
  default = 6
}
variable "machine_type" {
  default = "e2-medium"
}

# ── Artifact Registry ──────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "pixel_war" {
  location      = var.region
  repository_id = "pixel-war"
  format        = "DOCKER"
  description   = "Docker images for Pixel War"
}

# ── GKE Cluster ────────────────────────────────────────────────────────────
resource "google_container_cluster" "pixel_war" {
  name     = "pixel-war-cluster"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy support (required for NetworkPolicies)
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  addons_config {
    network_policy_config {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
  }
}

resource "google_container_node_pool" "pixel_war_nodes" {
  name       = "pixel-war-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.pixel_war.name
  initial_node_count = var.node_count

  autoscaling {
    min_node_count = var.node_count
    max_node_count = var.max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 20
    image_type   = "COS_CONTAINERD"

    # Least privilege OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# ── Service Account for CI/CD ──────────────────────────────────────────────
resource "google_service_account" "cicd_sa" {
  account_id   = "pixel-war-cicd"
  display_name = "Pixel War CI/CD Service Account"
}

resource "google_project_iam_member" "cicd_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}
