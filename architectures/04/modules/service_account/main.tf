resource "google_service_account" "gke" {
  account_id = "${var.prefix}-gke-sa"
}

resource "google_service_account_iam_member" "gke_wid" {
  service_account_id = google_service_account.gke.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[default/app-ksa]"
}
