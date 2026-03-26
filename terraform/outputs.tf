output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.pixel_war.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.pixel_war.endpoint
  sensitive   = true
}

output "artifact_registry_url" {
  description = "Docker image base URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.pixel_war.repository_id}"
}

output "cicd_service_account" {
  description = "Service account to use in GitHub Actions secret GCP_SA_KEY"
  value       = google_service_account.cicd_sa.email
}

output "get_credentials_cmd" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.pixel_war.name} --zone ${var.zone} --project ${var.project_id}"
}
