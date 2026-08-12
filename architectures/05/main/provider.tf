terraform {
  required_version = ">= 1.14.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.40.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0.0"
    }
  }
}

provider "google" {
  project = "your-project-id"
  region  = "asia-northeast1"
}
  