locals {
  possible_database_versions = ["POSTGRES_9_6", "POSTGRES_10", "POSTGRES_11", "POSTGRES_12", "POSTGRES_13", "POSTGRES_14", "POSTGRES_15", "POSTGRES_16", "POSTGRES_17"]
}

variable "prefix" {
  description = "Prefix for naming resources"
  type        = string

  default = "test"
}


variable "region" {
  description = "Region for resources"
  type        = string

  default = "asia-northeast1"
}

variable "database_version" {
  description = "Database version"
  type        = string

  default = "POSTGRES_15"

  validation {
    condition     = contains(local.possible_database_versions, var.database_version)
    error_message = "The database version must be one of the following: ${join(", ", local.possible_database_versions)}"
  }
}

variable "vpc_network_self_link" {
  description = "VPC network self link"
  type        = string
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number

  default = 10
}

variable "disk_autoresize_limit" {
  description = "Disk autoresize limit in GB"
  type        = number

  default = 1000
}

variable "db_user_name" {
  description = "Database user name"
  type        = string

  default = "app_user"
}

variable "db_password" {
  description = "Database user password (received from secret_manager module)"
  type        = string
  sensitive   = true
}

variable "db_password_version" {
  description = "Increment this value to rotate the DB password"
  type        = number

  default = 1
}
