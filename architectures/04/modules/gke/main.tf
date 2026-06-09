resource "google_container_cluster" "default" {
  name = "${var.prefix}-autopilot-cluster"

  location         = var.location
  enable_autopilot = true

  network    = var.vpc_network_id
  subnetwork = var.subnet_id

  ip_allocation_policy {
    stack_type                    = "IPV4"
    services_secondary_range_name = var.subnet_service_ip_range_name
    cluster_secondary_range_name  = var.subnet_pod_ip_range_name
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # kubectlからアクセスするためfalse
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  deletion_protection = false
}
