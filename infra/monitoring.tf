resource "google_monitoring_notification_channel" "email" {
  display_name = "Code Review Agent Email Alerts"
  project      = var.project_id
  type         = "email"

  labels = {
    email_address = "pavansai2809@yahoo.com"
  }
}

resource "google_monitoring_alert_policy" "cloud_run_errors" {
  display_name = "Code Review Agent — 5xx Errors"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run 5xx error rate"

    condition_threshold {
      filter = <<-EOT
        resource.type = "cloud_run_revision"
        AND resource.labels.service_name = "code-review-agent"
        AND metric.type = "run.googleapis.com/request_count"
        AND metric.labels.response_code_class = "5xx"
      EOT

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }

      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "60s"
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }
}
