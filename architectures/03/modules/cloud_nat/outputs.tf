output "nat_router_name" {
  description = "Cloud NAT Router name for monitoring"
  value       = google_compute_router.nat_router.name
}

output "nat_gateway_name" {
  description = "Cloud NAT Gateway name for monitoring"
  value       = google_compute_router_nat.nat.name
}
