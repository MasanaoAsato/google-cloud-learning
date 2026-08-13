# ── processor function ソースコード ──────────────────────────────

data "archive_file" "processor" {
  type        = "zip"
  output_path = "/tmp/${var.prefix}-processor.zip"
  source_dir  = "${path.module}/source/processor"
}

resource "google_storage_bucket_object" "processor_source" {
  name   = "processor-${data.archive_file.processor.output_md5}.zip"
  bucket = var.functions_source_bucket_name
  source = data.archive_file.processor.output_path
}

# ── subscriber function ソースコード ─────────────────────────────

data "archive_file" "subscriber" {
  type        = "zip"
  output_path = "/tmp/${var.prefix}-subscriber.zip"
  source_dir  = "${path.module}/source/subscriber"
}

resource "google_storage_bucket_object" "subscriber_source" {
  name   = "subscriber-${data.archive_file.subscriber.output_md5}.zip"
  bucket = var.functions_source_bucket_name
  source = data.archive_file.subscriber.output_path
}

# ── processor: Cloud Storage イベントを受信し Pub/Sub へ publish ──

resource "google_cloudfunctions2_function" "processor" {
  name        = "${var.prefix}-processor"
  location    = var.region
  description = "Receives GCS upload events via Eventarc and publishes to Pub/Sub"

  build_config {
    runtime     = "nodejs22"
    entry_point = "processor"
    source {
      storage_source {
        bucket = var.functions_source_bucket_name
        object = google_storage_bucket_object.processor_source.name
      }
    }
  }

  service_config {
    max_instance_count             = var.processor_max_instance_count
    min_instance_count             = var.processor_min_instance_count
    available_memory               = var.processor_available_memory
    timeout_seconds                = var.processor_timeout_seconds
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
    service_account_email          = var.gcf_processor_sa_email

    environment_variables = {
      PUBSUB_TOPIC = var.processor_output_topic_id
    }
  }
}

# ── subscriber: Pub/Sub メッセージを受信し output bucket へ書き込み ──

resource "google_cloudfunctions2_function" "subscriber" {
  name        = "${var.prefix}-subscriber"
  location    = var.region
  description = "Receives Pub/Sub messages via Eventarc and writes results to GCS"

  build_config {
    runtime     = "nodejs22"
    entry_point = "subscriber"
    source {
      storage_source {
        bucket = var.functions_source_bucket_name
        object = google_storage_bucket_object.subscriber_source.name
      }
    }
  }

  service_config {
    max_instance_count             = var.subscriber_max_instance_count
    min_instance_count             = var.subscriber_min_instance_count
    available_memory               = var.subscriber_available_memory
    timeout_seconds                = var.subscriber_timeout_seconds
    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
    service_account_email          = var.gcf_subscriber_sa_email

    environment_variables = {
      OUTPUT_BUCKET = var.output_bucket_name
    }
  }
}
