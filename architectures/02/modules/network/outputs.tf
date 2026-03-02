output "vpc_network_id" {
  value       = google_compute_network.vpc_network.id
  description = "The ID of the VPC network"
}

output "vpc_network_self_link" {
  value       = google_compute_network.vpc_network.self_link
  description = "The self link of the VPC network"
}

output "subnet_id" {
  value       = google_compute_subnetwork.subnet_direct_vpc_egress.id
  description = "The ID of the subnetwork"
}
