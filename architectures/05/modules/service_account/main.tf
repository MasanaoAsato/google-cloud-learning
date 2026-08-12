# ── Service Accounts ─────────────────────────────────────────────

resource "google_service_account" "gcf_processor" {
  account_id   = "${var.prefix}-gcf-processor-sa"
  display_name = "Cloud Functions processor runtime SA"
}

resource "google_service_account" "gcf_subscriber" {
  account_id   = "${var.prefix}-gcf-subscriber-sa"
  display_name = "Cloud Functions subscriber runtime SA"
}

resource "google_service_account" "eventarc_invoker" {
  account_id   = "${var.prefix}-eventarc-invoker-sa"
  display_name = "Eventarc trigger SA for invoking Cloud Functions"
}

