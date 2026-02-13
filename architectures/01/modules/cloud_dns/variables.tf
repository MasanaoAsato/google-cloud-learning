variable "dns_managed_zone_name" {
  description = "The name of the Cloud DNS managed zone."
  type        = string
}

variable "domain_name" {
  description = "The domain name for the A record."
  type        = string
}

variable "lb_ip_address" {
  description = "The IP address for the A record."
  type        = string
}

variable "dns_auth_record_name" {
  description = "The name of the DNS record for key authorization."
  type        = string
}

variable "dns_auth_record_type" {
  description = "The type of the DNS record for key authorization."
  type        = string
}

variable "dns_auth_record_data" {
  description = "The data of the DNS record for key authorization."
  type        = string
}
