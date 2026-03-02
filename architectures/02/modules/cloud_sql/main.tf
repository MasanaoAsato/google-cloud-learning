resource "google_sql_database_instance" "main" {
  name             = "${var.prefix}-main-instance"
  database_version = var.database_version
  region           = var.region

  settings {
    # gcloud sql tiers list で確認可能
    tier              = "db-f1-micro"
    edition           = "ENTERPRISE"
    availability_type = "REGIONAL"

    disk_autoresize       = true
    disk_size             = var.disk_size
    disk_type             = "PD_SSD"
    disk_autoresize_limit = var.disk_autoresize_limit

    ip_configuration {
      ipv4_enabled    = true
      private_network = var.vpc_network_self_link
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    password_validation_policy {
      min_length                  = 12
      disallow_username_substring = true
      enable_password_policy      = true
    }

    database_flags {
      name  = "timezone"
      value = "Asia/Tokyo"
    }

    backup_configuration {
      enabled = true
      # UTC time zone(JST 01:00) database_flags設定範囲外
      start_time                     = "16:00"
      location                       = var.region
      point_in_time_recovery_enabled = true

      backup_retention_settings {
        retention_unit   = "COUNT"
        retained_backups = 7
      }
    }
  }
  deletion_protection = false
}

resource "google_sql_database" "default" {
  name     = "${var.prefix}-database"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = var.db_user_name
  instance = google_sql_database_instance.main.name

  password_wo         = var.db_password
  password_wo_version = var.db_password_version
}
