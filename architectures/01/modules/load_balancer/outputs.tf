output "lb_ip_address" {
  description = "The global IP address of the load balancer"
  value       = google_compute_global_address.lb_ip.address
}

output "dns_auth_record_data" {
  description = "The data of the DNS record for certificate authorization"
  value       = google_certificate_manager_dns_authorization.lb.dns_resource_record[0].data
}

output "dns_auth_record_name" {
  description = "The name of the DNS record for certificate authorization"
  value       = google_certificate_manager_dns_authorization.lb.dns_resource_record[0].name
}

output "dns_auth_record_type" {
  description = "The type of the DNS record for certificate authorization"
  value       = google_certificate_manager_dns_authorization.lb.dns_resource_record[0].type
}
