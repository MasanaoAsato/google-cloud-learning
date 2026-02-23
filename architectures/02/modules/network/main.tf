resource "google_compute_network" "vpc_network" {
  name                    = "${var.prefix}-vpc-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet_direct_vpc_egress" {
  name          = "${var.prefix}-test-subnetwork"
  ip_cidr_range = "10.0.0.1/16"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_global_address" "default" {
  #provider     = google-beta

  name         = "private-vpc-peering-ip"
  address_type = "INTERNAL"
  purpose      = "VPC_PEERING"
  network      = google_compute_network.vpc_network.id
  address      = "10.10.0.0/16"
}

resource "google_service_networking_connection" "default" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.default.name]
}
