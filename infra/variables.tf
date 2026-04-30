variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "pa1-cloud-project"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "code-review-agent"
}

variable "image_name" {
  description = "Docker image name in Artifact Registry"
  type        = string
  default     = "code-review-agent"
}
