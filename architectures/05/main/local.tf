locals {
  # General
  prefix     = "test"
  region     = "asia-northeast1"
  project_id = "your-project-id"

  # APIs
  required_apis = [
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "eventarc.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
  ]

  # Pub/Sub
  message_retention_duration     = "86600s"  # 1日
  dlq_message_retention_duration = "604800s" # 7日
  max_delivery_attempts          = 5

  # Eventarc
  eventarc_max_attempts = 1

  # processor function スケーリング
  processor_max_instance_count = 3
  processor_min_instance_count = 0
  processor_available_memory   = "256M"
  processor_timeout_seconds    = 60

  # subscriber function スケーリング
  subscriber_max_instance_count = 3
  subscriber_min_instance_count = 0
  subscriber_available_memory   = "256M"
  subscriber_timeout_seconds    = 60
}
