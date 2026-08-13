# ── GCS → processor function トリガー ────────────────────────────

resource "google_eventarc_trigger" "gcs_to_processor" {
  name     = "${var.prefix}-gcs-to-processor"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = var.input_bucket_name
  }

  destination {
    cloud_run_service {
      service = var.processor_function_name
      region  = var.region
    }
  }

  retry_policy {
    max_attempts = var.eventarc_max_attempts
  }

  service_account = var.eventarc_invoker_sa_email
}

# ── Pub/Sub → subscriber function Push サブスクリプション（DLQ付き）────

resource "google_pubsub_subscription" "subscriber" {
  name  = "${var.prefix}-subscriber"
  topic = var.processor_output_topic_name

  ack_deadline_seconds       = 60
  message_retention_duration = var.message_retention_duration

  push_config {
    push_endpoint = var.subscriber_function_uri
    oidc_token {
      service_account_email = var.eventarc_invoker_sa_email
    }
  }

  dead_letter_policy {
    dead_letter_topic     = var.dlq_topic_id
    max_delivery_attempts = var.max_delivery_attempts
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
