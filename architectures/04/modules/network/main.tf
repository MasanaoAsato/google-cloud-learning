resource "google_compute_network" "vpc_network" {
  name                    = "${var.prefix}-vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet_gke" {
  name          = "${var.prefix}-gke-subnetwork"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id

  secondary_ip_range {
    range_name    = "${var.prefix}-pod-range"
    ip_cidr_range = "10.1.0.0/16"
  }
  secondary_ip_range {
    range_name    = "${var.prefix}-service-range"
    ip_cidr_range = "10.2.0.0/20"
  }
}
