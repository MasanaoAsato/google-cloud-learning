locals {
  # General values
  prefix   = "test"
  location = "asia-northeast1"
  region   = "asia-northeast1"
  # Cloud DNS values
  dns_managed_zone_name     = "example-zone"
  dns_managed_zone_dns_name = "mystudy.com."

  # Cloud Run values
  crun_cpu                = "1"
  crun_memory             = "512Mi"
  crun_min_instance_count = 0
  crun_max_instance_count = 3
  crun_timeout_seconds    = "30s"

  # load balancer values
  dns_authorization_domain         = "mystudy.com"
  certification_domains            = ["mystudy.com", "*.mystudy.com"]
  certification_map_entry_hostname = "dev.mystudy.com"
  enable_cdn                       = false

  # cloud nat values
  bgp_asn                          = 64515
  min_ports_per_vm                 = 2048
  max_ports_per_vm                 = 8192
  tcp_established_idle_timeout_sec = 300
  tcp_transitory_idle_timeout_sec  = 30

}
