data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"

    members = [
      "allUsers",
    ]
  }
}


resource "google_cloud_run_v2_service" "default" {
  name     = "${var.prefix}-cloud-run-service"
  location = var.location
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          memory = var.crun_memory
          cpu    = var.crun_cpu
        }
      }
    }

    scaling {
      min_instance_count = var.crun_min_instance_count
      max_instance_count = var.crun_max_instance_count
    }

    timeout = var.crun_timeout_seconds
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

}

resource "google_cloud_run_v2_service_iam_policy" "noauth" {
  location    = google_cloud_run_v2_service.default.location
  name        = google_cloud_run_v2_service.default.name
  policy_data = data.google_iam_policy.noauth.policy_data
}
