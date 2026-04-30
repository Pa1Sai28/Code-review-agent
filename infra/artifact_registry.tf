resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "code-review-agent"
  description   = "Docker repository for Code Review Agent"
  format        = "DOCKER"
  project       = var.project_id
}

output "docker_repo_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/code-review-agent"
  description = "Artifact Registry Docker repository URL"
}
