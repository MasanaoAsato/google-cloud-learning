resource "google_compute_router" "nat_router" {
  name    = "crouter-${var.prefix}"
  region  = var.region
  network = var.vpc_network_id

  bgp {
    asn = var.bgp_asn
  }
}

resource "google_compute_address" "nat_address" {
  name         = "nat-manual-ip-${var.prefix}"
  region       = var.region
  address_type = "EXTERNAL"
  network_tier = "PREMIUM"

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_router_nat" "nat" {
  name                               = "cnat-${var.prefix}"
  router                             = google_compute_router.nat_router.name
  region                             = var.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.nat_address.self_link]
  auto_network_tier                  = "PREMIUM"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  min_ports_per_vm               = var.min_ports_per_vm
  max_ports_per_vm               = var.max_ports_per_vm
  enable_dynamic_port_allocation = true

  tcp_established_idle_timeout_sec = var.tcp_established_idle_timeout_sec
  tcp_transitory_idle_timeout_sec  = var.tcp_transitory_idle_timeout_sec

  subnetwork {
    name                    = var.subnet_id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
