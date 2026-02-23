resource "google_service_account" "cloud_run" {
  account_id   = "${var.prefix}-cr-sa"
  display_name = "Cloud Run Service Account for ${var.prefix}"
}

# Cloud SQL Client　Cloud SQL Auth Proxy (Unixドメインソケット)で接続する場合は必要
# resource "google_project_iam_member" "cloudsql_client" {
#   project = var.project_id
#   role    = "roles/cloudsql.client"
#   member  = "serviceAccount:${google_service_account.cloud_run.email}"
# }

# Secret Manager Accessor
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run Invoker
resource "google_project_iam_member" "cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}
