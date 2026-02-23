locals {
  possible_cpu_values = ["1", "2", "4", "6", "8"]
}

variable "prefix" {
  description = "Prefix for naming resources"
  type        = string

  default = "test"
}

variable "location" {
  description = "Location for resources"
  type        = string

  default = "asia-northeast1"
}

variable "crun_cpu" {
  description = "CPU value for Cloud Run service"
  type        = string

  default = "2"

  validation {
    condition     = contains(local.possible_cpu_values, var.crun_cpu)
    error_message = "The CPU value must be one of the following: ${join(", ", local.possible_cpu_values)}"
  }
}

variable "crun_memory" {
  description = "Memory value for Cloud Run service"
  type        = string

  default = "256Mi"
}

variable "crun_min_instance_count" {
  description = "Minimum instance count for Cloud Run service"
  type        = number

  default = 0
}

variable "crun_max_instance_count" {
  description = "Maximum instance count for Cloud Run service"
  type        = number

  default = 3
}

variable "crun_timeout_seconds" {
  description = "Timeout in seconds for Cloud Run service"
  type        = string

  default = "30s"
}


variable "vpc_network_id" {
  description = "The ID of the VPC network"
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnetwork"
  type        = string
}

# Cloud SQL Auth Proxy (Unixドメインソケット)で接続する場合は必要
# variable "cloud_sql_connection_name" {
#   description = "Cloud SQL connection name"
#   type        = string
# }

variable "service_account_email" {
  description = "The email of the service account"
  type        = string
}

variable "secret_name" {
  description = "The name of the secret in Secret Manager"
  type        = string
}

variable "db_user_name" {
  description = "Database user name"
  type        = string
}

variable "db_private_ip" {
  description = "Database private IP address"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}
