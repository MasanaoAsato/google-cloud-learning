output "vpc_network_id" {
  value       = google_compute_network.vpc_network.id
  description = "The ID of the VPC network"
}

output "subnet_id" {
  value       = google_compute_subnetwork.subnet_gke.id
  description = "The ID of the subnetwork"
}

output "subnet_pod_ip_range_name" {
  value       = google_compute_subnetwork.subnet_gke.secondary_ip_range[0].range_name
  description = "The IP range for pods in the subnetwork"
}

output "subnet_service_ip_range_name" {
  value       = google_compute_subnetwork.subnet_gke.secondary_ip_range[1].range_name
  description = "The IP range for services in the subnetwork"

}
