output "service_name" {
  value       = google_cloud_run_v2_service.code_review_agent.name
  description = "Cloud Run service name"
}

output "service_url" {
  value       = google_cloud_run_v2_service.code_review_agent.uri
  description = "Cloud Run service URL — use this for webhook registration"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/code-review-agent"
  description = "Artifact Registry URL for pushing Docker images"
}
