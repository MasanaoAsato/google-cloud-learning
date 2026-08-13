data "google_project" "project" {}

data "google_storage_project_service_account" "gcs_sa" {}

locals {
  pubsub_sa_email         = "service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  cloudfunctions_sa_email = "service-${data.google_project.project.number}@gcf-admin-robot.iam.gserviceaccount.com"
}

# ── プロジェクトレベル IAM ────────────────────────────────────────

resource "google_project_iam_member" "gcf_processor_artifactregistry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${var.gcf_processor_sa_email}"
}

resource "google_project_iam_member" "eventarc_invoker_eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${var.eventarc_invoker_sa_email}"
}

resource "google_project_iam_member" "gcf_subscriber_artifactregistry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${var.gcf_subscriber_sa_email}"
}

# Cloud Functions サービスエージェントに Artifact Registry 読み取り権限を付与
# Gen2 Functions のビルド・デプロイ時にコンテナイメージの読み書きで必要
resource "google_project_iam_member" "cloudfunctions_sa_artifactregistry" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${local.cloudfunctions_sa_email}"
}

# GCS サービスエージェントに Pub/Sub Publisher を付与
# Eventarc が GCS イベントを受信するために必要
resource "google_project_iam_member" "gcs_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_sa.email_address}"
}

# ── Cloud Storage バケットレベル IAM ─────────────────────────────

resource "google_storage_bucket_iam_member" "gcf_processor_input_viewer" {
  bucket = var.input_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.gcf_processor_sa_email}"
}

resource "google_storage_bucket_iam_member" "gcf_subscriber_output_creator" {
  bucket = var.output_bucket_name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${var.gcf_subscriber_sa_email}"
}

# ── Pub/Sub トピックレベル IAM ───────────────────────────────────

# Pub/Sub サービスエージェントに DLQ topic への Publisher 権限を付与
# subscriber の Eventarc トリガーが作るサブスクリプションで DLQ を使う場合に必要
resource "google_pubsub_topic_iam_member" "pubsub_sa_dlq_publisher" {
  topic  = var.dlq_topic_name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.pubsub_sa_email}"
}

resource "google_pubsub_topic_iam_member" "gcf_processor_publisher" {
  topic  = var.processor_output_topic_name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${var.gcf_processor_sa_email}"
}

# ── Cloud Run サービスレベル IAM ─────────────────────────────────

resource "google_cloud_run_v2_service_iam_member" "eventarc_invoker_processor" {
  project  = var.project_id
  location = var.region
  name     = var.processor_function_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.eventarc_invoker_sa_email}"
}

resource "google_cloud_run_v2_service_iam_member" "eventarc_invoker_subscriber" {
  project  = var.project_id
  location = var.region
  name     = var.subscriber_function_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.eventarc_invoker_sa_email}"
}

# Pub/Sub SA が eventarc_invoker_sa になりすましてOIDCトークンを発行するために必要
# Push サブスクリプションが subscriber function を呼び出す際に使用
resource "google_service_account_iam_member" "pubsub_sa_token_creator" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.eventarc_invoker_sa_email}"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${local.pubsub_sa_email}"
}
