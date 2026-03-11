output "cluster_name" {
  value = google_container_cluster.pixel_war.name
}

output "cluster_endpoint" {
  value = google_container_cluster.pixel_war.endpoint
}