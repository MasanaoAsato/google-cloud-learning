data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"

    members = [
      "allUsers",
    ]
  }
}


resource "google_cloud_run_v2_service" "default" {
  name                = "${var.prefix}-cloud-run-service"
  location            = var.location
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = false
  template {
    service_account = var.service_account_email

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          memory = var.crun_memory
          cpu    = var.crun_cpu
        }
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.secret_name
            version = "latest"
          }
        }
      }
      env {
        name  = "DB_USER"
        value = var.db_user_name
      }
      env {
        name  = "DB_PRIVATE_IP"
        value = var.db_private_ip
      }
      env {
        name  = "DB_NAME"
        value = var.db_name
      }

      # Cloud SQL Auth Proxy (Unixドメインソケット)で接続する場合は必要
      #   volume_mounts {
      #     name       = "cloudsql"
      #     mount_path = "/cloudsql"
      #   }
      # }

      # volumes {
      #   name = "cloudsql"
      #   cloud_sql_instance {
      #     instances = [var.cloud_sql_connection_name]
      #   }
    }


    vpc_access {
      egress = "ALL_TRAFFIC"
      network_interfaces {
        network    = var.vpc_network_id
        subnetwork = var.subnet_id
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
