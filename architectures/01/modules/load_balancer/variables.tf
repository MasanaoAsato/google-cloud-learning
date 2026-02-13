variable "prefix" {
  description = "Prefix for naming resources"
  type        = string

  default = "test"
}

variable "dns_authorization_domain" {
  description = "Domain for DNS authorization"
  type        = string
}

variable "certification_domains" {
  description = "List of domains for certificate management"
  type        = list(string)
}

variable "certification_map_entry_hostname" {
  description = "Hostname for certificate map entry"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string

  default = "asia-northeast1"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name to be used in the Load Balancer"
  type        = string
}

variable "enable_cdn" {
  description = "Whether to enable CDN for the Load Balancer"
  type        = bool
  default     = false
}

variable "security_policy_self_link" {
  description = "Security policy for the Load Balancer"
  type        = string
}
