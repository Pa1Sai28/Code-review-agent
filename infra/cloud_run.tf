resource "google_cloud_run_v2_service" "code_review_agent" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/code-review-agent/${var.image_name}:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name = "GITHUB_WEBHOOK_SECRET"
        value_source {
          secret_key_ref {
            secret  = "GITHUB_WEBHOOK_SECRET"
            version = "latest"
          }
        }
      }

      env {
        name = "GITHUB_PAT"
        value_source {
          secret_key_ref {
            secret  = "GITHUB_PAT"
            version = "latest"
          }
        }
      }

      env {
        name = "GITLAB_WEBHOOK_TOKEN"
        value_source {
          secret_key_ref {
            secret  = "GITLAB_WEBHOOK_TOKEN"
            version = "latest"
          }
        }
      }

      env {
        name = "GITLAB_PAT"
        value_source {
          secret_key_ref {
            secret  = "GITLAB_PAT"
            version = "latest"
          }
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "ANTHROPIC_API_KEY"
            version = "latest"
          }
        }
      }

      ports {
        container_port = 5000
      }
    }

    service_account = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

data "google_project" "project" {
  project_id = var.project_id
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.code_review_agent.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "cloud_run_url" {
  value       = google_cloud_run_v2_service.code_review_agent.uri
  description = "The public URL of the Cloud Run service"
}
