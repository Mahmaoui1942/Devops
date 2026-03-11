provider "google" {
  project = "pixel-war-489910"
  region  = "europe-west1"
  zone    = "europe-west1-b"
}

resource "google_container_cluster" "pixel_war" {
  name     = "pixel-war-cluster"
  location = "europe-west1-b"

  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = false
}

resource "google_container_node_pool" "pixel_war_nodes" {
  name       = "pixel-war-node-pool"
  location   = "europe-west1-b"
  cluster    = google_container_cluster.pixel_war.name
  node_count = 2

  node_config {
    machine_type = "e2-medium"
    disk_size_gb = 20

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
