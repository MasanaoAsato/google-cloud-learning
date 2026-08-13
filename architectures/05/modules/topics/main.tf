resource "google_pubsub_topic" "processor_output" {
  name                       = "${var.prefix}-processor-output"
  message_retention_duration = var.message_retention_duration
}

resource "google_pubsub_topic" "dlq" {
  name                       = "${var.prefix}-dlq"
  message_retention_duration = var.dlq_message_retention_duration
}

# DLQ 監視用 Pull サブスクリプション（障害解析・デバッグ用）
resource "google_pubsub_subscription" "dlq_monitor" {
  name  = "${var.prefix}-dlq-monitor"
  topic = google_pubsub_topic.dlq.name

  ack_deadline_seconds       = 60
  message_retention_duration = var.dlq_message_retention_duration
  retain_acked_messages      = true

  expiration_policy {
    ttl = "" # 無期限
  }
}
