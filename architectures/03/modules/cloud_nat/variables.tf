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

variable "bgp_asn" {
  description = "BGP ASN for Cloud Router"
  type        = number

  validation {
    condition     = var.bgp_asn >= 64512 && var.bgp_asn <= 65534
    error_message = "BGP ASN must be a valid number between 64512 and 65534."
  }
}

variable "vpc_network_id" {
  description = "VPC network ID for the Cloud NAT service"
  type        = string

  validation {
    condition     = var.vpc_network_id != ""
    error_message = "VPC network ID must be provided."
  }
}

variable "subnet_id" {
  description = "Subnet ID for the Cloud NAT"
  type        = string

  validation {
    condition     = var.subnet_id != ""
    error_message = "Subnet ID must be provided."
  }
}

variable "min_ports_per_vm" {
  description = "Minimum number of ports allocated to a VM from this NAT"
  type        = number
  default     = 64

  validation {
    condition     = var.min_ports_per_vm >= 64 && var.min_ports_per_vm <= 65536
    error_message = "min_ports_per_vm must be between 64 and 65536."
  }
}

variable "max_ports_per_vm" {
  description = "Maximum number of ports allocated to a VM from this NAT"
  type        = number
  default     = 4096

  validation {
    condition     = var.max_ports_per_vm >= 64 && var.max_ports_per_vm <= 65536
    error_message = "max_ports_per_vm must be between 64 and 65536."
  }
}

variable "tcp_established_idle_timeout_sec" {
  description = "Timeout (in seconds) for TCP established connections"
  type        = number
  default     = 300

  validation {
    condition     = var.tcp_established_idle_timeout_sec >= 30 && var.tcp_established_idle_timeout_sec <= 86400
    error_message = "tcp_established_idle_timeout_sec must be between 30 and 86400 seconds."
  }
}

variable "tcp_transitory_idle_timeout_sec" {
  description = "Timeout (in seconds) for TCP transitory connections"
  type        = number
  default     = 30

  validation {
    condition     = var.tcp_transitory_idle_timeout_sec >= 30 && var.tcp_transitory_idle_timeout_sec <= 86400
    error_message = "tcp_transitory_idle_timeout_sec must be between 30 and 86400 seconds."
  }
}
