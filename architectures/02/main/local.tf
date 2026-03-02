locals {
  # general
  prefix     = "test"
  region     = "asia-northeast1"
  project_id = "my-gcp-project"

  # secret manager
  secret_manager_secret_id = "db-password"

  # cloud sql
  disk_size             = 10
  disk_autoresize_limit = 1000
  db_user_name          = "app_user"
  db_password_version   = 1

  # cloud run
  crun_cpu                = "2"
  crun_memory             = "512Mi"
  crun_min_instance_count = 0
  crun_max_instance_count = 3
  crun_timeout_seconds    = "30s"
}
