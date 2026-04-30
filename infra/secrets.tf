# Reference existing secrets — they were created manually
# Terraform manages access, not the secret values themselves

data "google_secret_manager_secret" "github_webhook_secret" {
  secret_id = "GITHUB_WEBHOOK_SECRET"
  project   = var.project_id
}

data "google_secret_manager_secret" "github_pat" {
  secret_id = "GITHUB_PAT"
  project   = var.project_id
}

data "google_secret_manager_secret" "gitlab_webhook_token" {
  secret_id = "GITLAB_WEBHOOK_TOKEN"
  project   = var.project_id
}

data "google_secret_manager_secret" "gitlab_pat" {
  secret_id = "GITLAB_PAT"
  project   = var.project_id
}

data "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "ANTHROPIC_API_KEY"
  project   = var.project_id
}
