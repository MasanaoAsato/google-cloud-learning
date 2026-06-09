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

variable "vpc_network_id" {
  description = "The ID of the VPC network"
  type        = string
}

variable "subnet_id" {
  description = "The ID of the subnetwork"
  type        = string
}

variable "subnet_pod_ip_range_name" {
  description = "The IP range for pods in the subnetwork"
  type        = string
}

variable "subnet_service_ip_range_name" {
  description = "The IP range for services in the subnetwork"
  type        = string
}
