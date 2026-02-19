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
