output "vpc_network_id" {
  value       = google_compute_network.vpc_network.id
  description = "The ID of the VPC network"
}

output "subnet_id" {
  value       = google_compute_subnetwork.nat.id
  description = "The ID of the subnetwork"
}
