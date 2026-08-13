data "google_project" "project" {}

resource "google_storage_bucket" "input" {
  name                        = "${var.prefix}-input-${data.google_project.project.number}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket" "output" {
  name                        = "${var.prefix}-output-${data.google_project.project.number}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket" "functions_source" {
  name                        = "${var.prefix}-functions-source-${data.google_project.project.number}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

